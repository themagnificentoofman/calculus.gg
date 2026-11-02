import { normalizeMath, questionMathIsRenderable } from '../render-math.mjs';
import { latexJsonPattern, questionOptionsAreDistinct, shuffleQuestionOptions, topics, validQuestionResponse } from './questions-policy.mjs';

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
  - Escape every LaTeX backslash correctly in JSON (two backslash characters in the JSON source). Never encode a TeX command as a JSON tab, newline, backspace, carriage return, or form feed.
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
            latexProblem: { type: 'string', minLength: 1, maxLength: 8000, pattern: latexJsonPattern },
            options: { type: 'array', minItems: 4, maxItems: 4, items: { type: 'string', minLength: 1, maxLength: 4000, pattern: latexJsonPattern } },
            correctIndex: { type: 'integer', minimum: 0, maximum: 3 },
            explanation: { type: 'array', minItems: 1, maxItems: 40, items: { type: 'string', minLength: 1, maxLength: 8000, pattern: latexJsonPattern } },
            topic: { type: 'string', enum: category === 'all' ? topics : [category] },
            difficulty: { type: 'string', enum: [difficulty] },
          },
        },
      },
    },
  };

  type Question = Parameters<typeof questionMathIsRenderable>[0] & { correctIndex: number; topic: string; difficulty: string };
  // Initial generation and the optional notation repair share one total deadline.
  const requestSignal = AbortSignal.timeout(70000);
  async function requestQuestions(input: string, expectedCount: number, maxOutputTokens: number): Promise<Question[]> {
    let response: Response;
    try {
      response = await fetch('https://api.openai.com/v1/responses', {
        method: 'POST',
        headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          store: false,
          instructions: 'You are a precise calculus problem author. Solve every problem before writing choices. Check domains and endpoint conditions. Use absolute values in logarithmic antiderivatives unless a positive domain is explicitly stated. All four options must be algebraically distinct. Exactly one option must be correct, and every explanation step must agree with it and correctIndex. Explain using mathematical expressions, never option letters or indices, because options will be shuffled after generation. Return only the requested JSON structure.',
          input,
          // Leave room for reasoning as well as the visible question JSON.
          max_output_tokens: maxOutputTokens,
          ...(model.startsWith('gpt-5') ? { reasoning: { effort: 'low' } } : {}),
          text: { format: { type: 'json_schema', name: 'calculus_questions', strict: true, schema: { ...schema, properties: { questions: { ...schema.properties.questions, minItems: expectedCount, maxItems: expectedCount } } } } },
        }),
        signal: requestSignal,
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
      const raw: unknown = JSON.parse(text).questions;
      const normalize = (value: unknown) => typeof value === 'string' ? normalizeMath(value) : value;
      // Normalize recognized JSON escape corruption before checking the canonical
      // strings. Unrecognized controls remain invalid; no formula is silently lost.
      const questions = Array.isArray(raw) ? raw.map(q => q && typeof q === 'object' ? {
        ...q,
        latexProblem: normalize(q.latexProblem),
        options: Array.isArray(q.options) ? q.options.map(normalize) : q.options,
        explanation: Array.isArray(q.explanation) ? q.explanation.map(normalize) : q.explanation,
      } : q) : raw;
      if (!validQuestionResponse(questions, { category, difficulty, count: expectedCount })) throw new Error();
      return questions as Question[];
    } catch {
      throw new QuestionGenerationError('invalid-output');
    }
  }

  const questions = await requestQuestions(prompt, count, Math.min(24000, 2400 + count * 1200));
  const isReady = (q: Question) => questionMathIsRenderable(q) && questionOptionsAreDistinct(q);
  const invalid = questions.map((q, index) => isReady(q) ? -1 : index).filter(index => index >= 0);
  if (!invalid.length) return questions.map(q => shuffleQuestionOptions(q));
  // Repair only a small invalid subset once. Do not retry transport failures,
  // refusals, truncated output, or a second malformed result.
  if (invalid.length > 3) throw new QuestionGenerationError('invalid-output');
  const repaired = await requestQuestions(
    `Repair these ${invalid.length} calculus questions. Correct invalid or unsupported LaTeX and replace duplicate distractors. Each complete problem, option, and explanation must render directly in KaTeX. All four options must be mathematically distinct with exactly one correct answer at correctIndex. Preserve the problem, the correct answer's mathematical meaning, correctIndex, topic, difficulty, and question order. Keep prose inside textnormal commands, balance all groups, and escape each backslash correctly in JSON. Return the corrected questions in the required JSON structure.\n${JSON.stringify(invalid.map(index => questions[index]))}`,
    invalid.length,
    Math.min(6000, 2400 + invalid.length * 1200),
  );
  for (const [offset, index] of invalid.entries()) {
    const original = questions[index], corrected = repaired[offset];
    if (!isReady(corrected) || corrected.correctIndex !== original.correctIndex || corrected.topic !== original.topic || corrected.difficulty !== original.difficulty) {
      throw new QuestionGenerationError('invalid-output');
    }
    questions[index] = corrected;
  }
  return questions.map(q => shuffleQuestionOptions(q));
}
