import { env } from 'cloudflare:workers';
export const dynamic = 'force-dynamic';
export function GET() {
  return Response.json({ status: 'ok', aiConfigured: Boolean(env.GEMINI_API_KEY && env.DB) }, {
    headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' },
  });
}
