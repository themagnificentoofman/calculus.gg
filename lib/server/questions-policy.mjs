// Prevent JSON escape sequences from silently turning TeX into control characters.
export const latexJsonPattern = '^[^\\u0000-\\u001f\\u007f]+$';
const latexString = new RegExp(latexJsonPattern);

export const topics = ['integration', 'differentiation', 'limits', 'series', 'differential equations', 'multivariable'];
export const difficulties = ['easy', 'medium', 'hard', 'olympiad'];

// Shuffle once on the server; the saved question set is shared by every player.
export function shuffleQuestionOptions(question, random = Math.random) {
  const order = question.options.map((_, index) => index);
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  return { ...question, options: order.map(index => question.options[index]), correctIndex: order.indexOf(question.correctIndex) };
}

export function questionOptionsAreDistinct(question) {
  const canonical = option => option.replace(/\\(?:dfrac|tfrac)\b/g, '\\frac')
    .replace(/\\(?:left|right)\b/g, '').replace(/\\(?:quad|qquad|[,;! ])/g, '').replace(/\s+/g, '');
  return new Set(question.options.map(canonical)).size === question.options.length;
}

export function validateQuestionRequest(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const { category, difficulty, count } = value;
  if (!(category === 'all' || topics.includes(category)) || !difficulties.includes(difficulty)) return null;
  if (!Number.isInteger(count) || count < 1 || count > 20) return null;
  return { category, difficulty, count };
}

export function validQuestionResponse(value, request) {
  const bounded = (text, max) => typeof text === 'string' && text.trim().length > 0 && text.length <= max && latexString.test(text);
  return Array.isArray(value) && value.length === request.count && value.every(q =>
    q && bounded(q.latexProblem, 8000) && Array.isArray(q.options) && q.options.length === 4 &&
    q.options.every(option => bounded(option, 4000)) && Number.isInteger(q.correctIndex) &&
    q.correctIndex >= 0 && q.correctIndex < 4 && Array.isArray(q.explanation) &&
    q.explanation.length > 0 && q.explanation.length <= 40 && q.explanation.every(step => bounded(step, 8000)) &&
    topics.includes(q.topic) && (request.category === 'all' || q.topic === request.category) && q.difficulty === request.difficulty
  );
}

export async function readBoundedJson(request, maxBytes = 4096) {
  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
    throw new Error('content-type');
  }
  if (Number(request.headers.get('content-length') || 0) > maxBytes) throw new Error('too-large');
  const reader = request.body?.getReader();
  if (!reader) throw new Error('invalid-json');
  let size = 0;
  const chunks = [];
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > maxBytes) { await reader.cancel(); throw new Error('too-large'); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  try { return JSON.parse(new TextDecoder().decode(bytes)); }
  catch { throw new Error('invalid-json'); }
}
