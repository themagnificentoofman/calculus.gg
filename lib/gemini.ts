import { GoogleGenAI, Type } from '@google/genai';

export async function generateQuestions(category: string, difficulty: string, count: number) {
  const ai = new GoogleGenAI({ apiKey: process.env.NEXT_PUBLIC_GEMINI_API_KEY });

  const prompt = `Generate ${count} calculus questions for category "${category}" at difficulty level "${difficulty}".
  
  Difficulty levels:
  - easy: High school calculus (AP Calculus AB level). Basic derivatives and integrals.
  - medium: AP Calculus BC / College Calculus 1. Techniques of integration, series, etc.
  - hard: College Calculus 2/3. Multivariable, vector calculus, hard integrals.
  - olympiad: Extremely difficult, Putnam-style calculus problems.
  
  Categories: integration, differentiation, limits, series, differential equations, multivariable. If "all" is selected, mix problems from all categories.
  
  For each question, provide:
  1. The problem statement in LaTeX (do not include $ or $$ wrappers). Make it as concise as possible. Omit unnecessary plaintext instructions if the mathematical notation implies the task (e.g., just write "\\int x^2 dx" instead of "Evaluate the integral \\textnormal{...}"). Only use plaintext when absolutely necessary for context or word problems.
  2. 4 multiple choice options in LaTeX (do not include $ or $$ wrappers).
  3. The index of the correct option (0-3).
  4. A step-by-step explanation, where each step or sentence is a separate string in an array. Each string must be valid LaTeX (do not include $ or $$ wrappers).
  5. The specific topic tag for this question (must be one of: integration, differentiation, limits, series, differential equations, multivariable).
  6. The difficulty tag for this question (must be one of: easy, medium, hard, olympiad).
  
  CRITICAL FORMATTING RULES FOR EXPLANATION AND PROBLEM STATEMENT:
  - You MUST use \\textnormal{...} for any plaintext words or sentences so they aren't italicized as math variables.
  - Do NOT use markdown formatting (like **bold**) inside the LaTeX strings.
  - Break down the explanation into logical steps, providing one step per array item. This ensures proper line breaks and readability.
  - Ensure proper spacing using \\quad or \\, where necessary.`;

  const response = await ai.models.generateContent({
    model: 'gemini-3.1-pro-preview',
    contents: prompt,
    config: {
      responseMimeType: 'application/json',
      responseSchema: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            latexProblem: { type: Type.STRING, description: 'The problem statement in LaTeX' },
            options: {
              type: Type.ARRAY,
              items: { type: Type.STRING },
              description: '4 multiple choice options in LaTeX'
            },
            correctIndex: { type: Type.INTEGER, description: 'Index of the correct option (0-3)' },
            explanation: { 
              type: Type.ARRAY, 
              items: { type: Type.STRING },
              description: 'Step-by-step explanation, where each step is a separate LaTeX string' 
            },
            topic: { type: Type.STRING, description: 'The topic tag for this question' },
            difficulty: { type: Type.STRING, description: 'The difficulty tag for this question' },
          },
          required: ['latexProblem', 'options', 'correctIndex', 'explanation', 'topic', 'difficulty'],
        },
      },
    },
  });

  const text = response.text;
  if (!text) {
    throw new Error('No response from Gemini');
  }

  return JSON.parse(text);
}
