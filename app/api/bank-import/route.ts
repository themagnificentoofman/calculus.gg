import { env } from 'cloudflare:workers';
import { bankOperator } from '../../../lib/server/bank-operator.mjs';
import { operatorQa } from '../../../lib/server/operator-qa';
import { firestoreStore, serviceAccountToken } from '../../../lib/server/firestore-admin';
import config from '../../../firebase-applet-config.json';
export const dynamic = 'force-dynamic';
export function POST(request: Request) {
  return bankOperator(request, env.DB, env.BANK_OPERATOR_PUBLIC_KEY, env.BANK_OPERATOR_EXPIRES_AT, (input: any, db: D1Database) => {
    if (!env.FIREBASE_SERVICE_ACCOUNT_JSON) throw Error('Missing server identity');
    const store = firestoreStore(config.projectId, config.firestoreDatabaseId, () => serviceAccountToken(env.FIREBASE_SERVICE_ACCOUNT_JSON!, config.projectId));
    return operatorQa(input, db, store);
  });
}
