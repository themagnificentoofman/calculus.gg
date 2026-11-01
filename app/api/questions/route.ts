import { env } from 'cloudflare:workers';
import firebaseConfig from '@/firebase-applet-config.json';
import { verifyFirebaseToken } from '@/lib/server/firebase-token.mjs';
import { readBoundedJson, validateQuestionRequest, validQuestionResponse } from '@/lib/server/questions-policy.mjs';
import { generateQuestionsOnServer } from '@/lib/server/generate-questions';
import { consumeQuota } from '@/lib/server/quota';

export const dynamic = 'force-dynamic';

const json = (data: unknown, status = 200, extra: Record<string, string> = {}) => Response.json(data, {
  status,
  headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', ...extra },
});

export async function POST(request: Request) {
  const origin = request.headers.get('origin');
  if (origin && origin !== new URL(request.url).origin) return json({ error: 'Request origin is not allowed.' }, 403);
  if (request.headers.get('sec-fetch-site') === 'cross-site') return json({ error: 'Request origin is not allowed.' }, 403);
  const match = /^Bearer ([^\s]+)$/.exec(request.headers.get('authorization') || '');
  if (!match || match[1].length > 8192) return json({ error: 'Please sign in before generating questions.' }, 401);
  let input;
  try { input = validateQuestionRequest(await readBoundedJson(request)); }
  catch (error) {
    const message = error instanceof Error ? error.message : '';
    return json({ error: 'Send a valid question request as JSON (maximum 4 KB).' }, message === 'too-large' ? 413 : 400);
  }
  if (!input) return json({ error: 'Choose a supported category, difficulty, and 1–20 questions.' }, 400);
  if (!env.GEMINI_API_KEY || !env.DB) return json({ error: 'Question generation has not been configured yet. Please contact the site owner.' }, 503);
  let uid: string;
  try { uid = await verifyFirebaseToken(match[1], firebaseConfig.projectId); }
  catch { return json({ error: 'Your sign-in has expired. Please sign in again.' }, 401); }
  try {
    if (!await consumeQuota(env.DB, uid)) return json({ error: 'Question generation limit reached. Please try again later.' }, 429, { 'Retry-After': '60' });
    const questions = await generateQuestionsOnServer(input.category, input.difficulty, input.count, env.GEMINI_API_KEY, env.GEMINI_MODEL || 'gemini-3.1-pro-preview');
    if (!validQuestionResponse(questions, input)) return json({ error: 'The AI returned an incomplete question set. Please try again.' }, 502);
    return json({ questions });
  } catch {
    // Do not return upstream error bodies, request text, or API key details.
    return json({ error: 'Question generation is temporarily unavailable. Please try again.' }, 502);
  }
}
