import { env } from 'cloudflare:workers';
import config from '../../firebase-applet-config.json';
import { verifyFirebaseIdentity } from './firebase-token.mjs';
import { firestoreStore, serviceAccountToken } from './firestore-admin';
import { createGameApi } from './game-api';
import { generateQuestionsOnServer, DEFAULT_OPENAI_MODEL } from './generate-questions';
import { consumeQuota } from './quota';
export function gameApi(resource: 'games' | 'profile' | 'questions' | 'social', request: Request) {
  if (!env.FIREBASE_SERVICE_ACCOUNT_JSON || !env.OPENAI_API_KEY || !env.DB) return Response.json({ error: 'Secure gameplay has not been configured. Please contact the site owner.' }, { status: 503, headers: { 'Cache-Control': 'no-store' } });
  const store = firestoreStore(config.projectId, config.firestoreDatabaseId, () => serviceAccountToken(env.FIREBASE_SERVICE_ACCOUNT_JSON!, config.projectId));
  return createGameApi({ store, verify: token => verifyFirebaseIdentity(token, config.projectId),
    generate: (category, difficulty, count) => generateQuestionsOnServer(category, difficulty, count, env.OPENAI_API_KEY!, env.OPENAI_MODEL || DEFAULT_OPENAI_MODEL),
    quota: uid => consumeQuota(env.DB!, uid) })(resource, request);
}
