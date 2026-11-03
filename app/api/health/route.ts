import { env } from 'cloudflare:workers';
export const dynamic = 'force-dynamic';
export function GET() {
  return Response.json({ status: 'ok', questionSource: 'bank', bankConfigured: Boolean(env.DB), secureGameplayConfigured: Boolean(env.FIREBASE_SERVICE_ACCOUNT_JSON && env.DB) }, {
    headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' },
  });
}
