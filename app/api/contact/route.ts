import { env } from 'cloudflare:workers';
import config from '../../../firebase-applet-config.json';
import { verifyFirebaseIdentity } from '@/lib/server/firebase-token.mjs';
import { contactRetryAfter, createContactApi, reserveContactQuota, resendContactSender } from '@/lib/server/contact-api';

export const dynamic = 'force-dynamic';
function contact(request: Request) {
  if (!env.DB || !env.RESEND_API_KEY || !env.CONTACT_FROM_EMAIL) return Response.json({ error: 'The contact form is temporarily unavailable. Please try again later.' }, { status: 503, headers: { 'Cache-Control': 'no-store' } });
  return createContactApi({
    verify: token => verifyFirebaseIdentity(token, config.projectId),
    reserve: (uid, now) => reserveContactQuota(env.DB!, uid, now),
    status: (uid, now) => contactRetryAfter(env.DB!, uid, now),
    send: resendContactSender(env.RESEND_API_KEY, env.CONTACT_FROM_EMAIL),
  })(request);
}
export const GET = contact;
export const POST = contact;
