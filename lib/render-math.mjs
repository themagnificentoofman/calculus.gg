// Keep the direct ESM import: the old CommonJS wrapper corrupted KaTeX's
// lexer in production-minified bundles.
import katex from 'katex';

/** @param {string} math */
export function normalizeMath(math) {
  const source = typeof math === 'string' ? math.trim() : '';
  // Legacy questions may include an outer math delimiter. Strip only a
  // matching outer pair; never rewrite commands or nested groups.
  for (const [open, close] of [['$$', '$$'], ['\\[', '\\]'], ['\\(', '\\)'], ['$', '$']]) {
    if (source.length >= open.length + close.length && source.startsWith(open) && source.endsWith(close)) {
      return source.slice(open.length, -close.length).trim();
    }
  }
  return source;
}

/** @param {string} math */
export function renderMath(math, displayMode = false) {
  return katex.renderToString(normalizeMath(math), {
    displayMode,
    throwOnError: true,
    trust: false,
    maxSize: 20,
    maxExpand: 1000,
  });
}

/** @param {{ latexProblem: string, options: string[], explanation: string[] }} question */
export function questionMathIsRenderable(question) {
  try {
    for (const source of [question.latexProblem, ...question.options, ...question.explanation]) renderMath(source);
    return true;
  } catch {
    return false;
  }
}
