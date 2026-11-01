// Import KaTeX's ESM entry directly. The react-katex CommonJS path corrupts
// KaTeX's lexer when minified by the current production bundler.
import katex from 'katex';

export function renderMath(math: string, displayMode = false) {
  return katex.renderToString(math, {
    displayMode,
    throwOnError: true,
    trust: false,
  });
}
