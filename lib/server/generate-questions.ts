import { questionMathIsRenderable } from '../render-math.mjs';
import { topics, validQuestionResponse } from './questions-policy.mjs';

export const DEFAULT_OPENAI_MODEL = 'gpt-5-mini';

// Keep provider errors free of request bodies, credentials, and upstream messages.
export class QuestionGenerationError extends Error {
  readonly kind: 'unavailable' | 'invalid-output' | 'timeout';
  constructor(kind: 'unavailable' | 'invalid-output' | 'timeout') {
    super(`Question generation: ${kind}`);
    this.kind = kind;
  }
}

export async function generateQuestionsOnServer(category: string, difficulty: string, count: number, apiKey: string, model = DEFAULT_OPENAI_MODEL) {
  const prompt = `Generate ${count} calculus questions for category "${category}" at difficulty level "${difficulty}".
  
  Difficulty levels:
  - easy: High school calculus (AP Calculus AB level). Basic derivatives and integrals.
  - medium: AP Calculus BC / College Calculus 1. Techniques of integration, series, etc.
  - hard: College Calculus 2/3. Multivariable, vector calculus, hard integrals.
  - olympiad: Extremely difficult, Putnam-style calculus problems.
  
  Categories: integration, differentiation, limits, series, differential equations, multivariable. If "all" is selected, mix problems from all categories.
  
  For each question, provide:
  1. The problem statement in LaTeX (do not include $ or $$ wrappers). Make it as concise as possible. Omit unnecessary plaintext instructions if the mathematical notation implies the task (e.g., just write "\\int x^2 dx" instead of "Evaluate the integral \\textnormal{...}"). Always state the requested operation explicitly (for derivatives, include the derivative operator, not just y=f(x)). Only use plaintext when necessary for context or word problems.
  2. 4 multiple choice options in LaTeX (do not include $ or $$ wrappers).
  3. The index of the correct option (0-3).
  4. A step-by-step explanation, where each step or sentence is a separate string in an array. Each complete string must be directly renderable by KaTeX with balanced groups and supported commands (do not include $ or $$ wrappers).
  5. The specific topic tag for this question (must be one of: integration, differentiation, limits, series, differential equations, multivariable).
  6. The difficulty tag for this question (must be one of: easy, medium, hard, olympiad).
  
  CRITICAL FORMATTING RULES FOR EXPLANATION AND PROBLEM STATEMENT:
  - You MUST use \\textnormal{...} for any plaintext words or sentences so they aren't italicized as math variables.
  - Do NOT use markdown formatting (like **bold**) inside the LaTeX strings.
  - Break down the explanation into logical steps, providing one step per array item. This ensures proper line breaks and readability.
  - Ensure proper spacing using \\quad or \\, where necessary.`;

  const schema = {
    type: 'object', additionalProperties: false, required: ['questions'],
    properties: {
      questions: {
        type: 'array', minItems: count, maxItems: count,
        items: {
          type: 'object', additionalProperties: false,
          required: ['latexProblem', 'options', 'correctIndex', 'explanation', 'topic', 'difficulty'],
          properties: {
            latexProblem: { type: 'string', minLength: 1, maxLength: 8000 },
            options: { type: 'array', minItems: 4, maxItems: 4, items: { type: 'string', minLength: 1, maxLength: 4000 } },
            correctIndex: { type: 'integer', minimum: 0, maximum: 3 },
            explanation: { type: 'array', minItems: 1, maxItems: 40, items: { type: 'string', minLength: 1, maxLength: 8000 } },
            topic: { type: 'string', enum: category === 'all' ? topics : [category] },
            difficulty: { type: 'string', enum: [difficulty] },
          },
        },
      },
    },
  };

  let response: Response;
  try {
    response = await fetch('https://api.openai.com/v1/responses', {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        store: false,
        instructions: 'You are a precise calculus problem author. Solve every problem before writing choices. Check domains and endpoint conditions. Use absolute values in logarithmic antiderivatives unless a positive domain is explicitly stated. All four options must be algebraically distinct. Exactly one option must be correct, and every explanation step must agree with it and correctIndex. Return only the requested JSON structure.',
        input: prompt,
        // Leave room for reasoning as well as the visible question JSON.
        max_output_tokens: Math.min(24000, 2400 + count * 1200),
        ...(model.startsWith('gpt-5') ? { reasoning: { effort: 'low' } } : {}),
        text: { format: { type: 'json_schema', name: 'calculus_questions', strict: true, schema } },
      }),
      signal: AbortSignal.timeout(70000),
    });
  } catch (error) {
    throw new QuestionGenerationError(error instanceof Error && ['TimeoutError', 'AbortError'].includes(error.name) ? 'timeout' : 'unavailable');
  }
  if (!response.ok) throw new QuestionGenerationError('unavailable');

  try {
    const result = await response.json() as {
      status?: string;
      output?: Array<{ type: string; content?: Array<{ type: string; text?: string }> }>;
    };
    if (result.status !== 'completed' || !Array.isArray(result.output)) throw new Error();
    const content = result.output.filter(item => item.type === 'message').flatMap(item => item.content || []);
    if (content.some(item => item.type === 'refusal')) throw new Error();
    const text = content.filter(item => item.type === 'output_text').map(item => item.text || '').join('');
    const questions: unknown = JSON.parse(text).questions;
    if (!validQuestionResponse(questions, { category, difficulty, count })) throw new Error();
    if (!(questions as Parameters<typeof questionMathIsRenderable>[0][]).every(questionMathIsRenderable)) throw new Error();
    return questions;
  } catch {
    throw new QuestionGenerationError('invalid-output');
  }
}
