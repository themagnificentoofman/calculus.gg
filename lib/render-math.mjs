// Keep the direct ESM import: the old CommonJS wrapper corrupted KaTeX's
// lexer in production-minified bundles.
import katex from 'katex';
import { normalizeNotation } from './math-notation.mjs';

// Older generated JSON sometimes decoded TeX's backslashes as JSON controls:
// \frac -> form feed + rac, \text -> tab + ext, \bigl -> backspace + igl.
// Restore only recognized command words, never arbitrary whitespace or prose.
const escapedCommands = new Set(`frac fbox forall flat begin beta bar boxed big bigl bigr bigm biggl biggr biggm boldsymbol binom bf backslash brace brack bullet bmod text textnormal textbf textrm textit textsf texttt textcolor tan tanh theta times to top tfrac tilde tag ne neq not nabla nu newline neg notin notni ni nmid right rangle rightarrow rho rm rvert rVert`.split(' '));
const escapeLetters = { '\b': 'b', '\f': 'f', '\t': 't', '\n': 'n', '\r': 'r' };

/** @param {string} math */
export function normalizeMath(math) {
  const restored = (typeof math === 'string' ? math : '').replace(/[\b\f\t\n\r]([a-zA-Z]+)/g, (match, tail) => {
    const command = escapeLetters[match[0]] + tail;
    return escapedCommands.has(command) ? '\\' + command : match;
  });
  // Keep unknown controls intact so validation cannot erase a broken command.
  if (/[\u0000-\u001f\u007f]/.test(restored)) return restored;
  const source = restored.trim();
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
  const source = normalizeNotation(normalizeMath(math));
  if (/[\u0000-\u001f\u007f]/.test(source)) throw new Error('Unrecognized control character in formula');
  return katex.renderToString(source, {
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
    for (const source of [question.latexProblem, ...question.options, ...question.explanation]) {
      if (!normalizeMath(source)) return false;
      renderMath(source);
    }
    return true;
  } catch {
    return false;
  }
}
