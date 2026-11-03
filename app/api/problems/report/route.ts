import { env } from 'cloudflare:workers';
import config from '../../../../firebase-applet-config.json';
import { verifyFirebaseIdentity } from '@/lib/server/firebase-token.mjs';
import { consumeBankReadQuota } from '@/lib/server/quota';
import { createProblemReport } from '@/lib/server/problem-report';
export const dynamic = 'force-dynamic';
export function POST(request: Request) {
  if (!env.DB) return Response.json({ error: 'Problem reporting is temporarily unavailable.' }, { status: 503 });
  return createProblemReport({ db: env.DB, verify: token => verifyFirebaseIdentity(token, config.projectId), quota: uid => consumeBankReadQuota(env.DB!, `report:${uid}`) })(request);
}
