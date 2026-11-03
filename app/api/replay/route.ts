import {env} from 'cloudflare:workers';
import config from '../../../firebase-applet-config.json';
import {firestoreStore,serviceAccountToken} from '../../../lib/server/firestore-admin';
import {verifyFirebaseIdentity} from '../../../lib/server/firebase-token.mjs';
import {createReplayApi} from '../../../lib/server/replay-api';
export const dynamic='force-dynamic';
export function POST(request:Request){
 if(!env.FIREBASE_SERVICE_ACCOUNT_JSON)return Response.json({error:'Replay service unavailable.'},{status:503});
 const store=firestoreStore(config.projectId,config.firestoreDatabaseId,()=>serviceAccountToken(env.FIREBASE_SERVICE_ACCOUNT_JSON!,config.projectId));
 return createReplayApi({store,verify:token=>verifyFirebaseIdentity(token,config.projectId)})(request);
}
