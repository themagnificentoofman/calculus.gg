import { env } from 'cloudflare:workers';
import config from '../../firebase-applet-config.json';
import { verifyFirebaseIdentity } from './firebase-token.mjs';
import { firestoreStore, serviceAccountToken } from './firestore-admin';
import { createGameApi } from './game-api';
import { selectBankQuestions, assertBankSetPlayable } from './bank-selection';
import { consumeBankReadQuota, consumeMutationQuota } from './quota';
export function gameApi(resource: 'games' | 'profile' | 'questions' | 'social', request: Request) {
  if (!env.FIREBASE_SERVICE_ACCOUNT_JSON || !env.DB) return Response.json({ error: 'Secure gameplay has not been configured. Please contact the site owner.' }, { status: 503, headers: { 'Cache-Control': 'no-store' } });
  const store = firestoreStore(config.projectId, config.firestoreDatabaseId, () => serviceAccountToken(env.FIREBASE_SERVICE_ACCOUNT_JSON!, config.projectId));
  return createGameApi({ store, verify: token => verifyFirebaseIdentity(token, config.projectId),
    select: (input, recent) => selectBankQuestions(env.DB!, input, recent),
    checkPlayable: questions => assertBankSetPlayable(env.DB!, questions),
    mutationQuota: uid => consumeMutationQuota(env.DB!, uid),
    quota: uid => consumeBankReadQuota(env.DB!, uid) })(resource, request);
}
