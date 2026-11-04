import { env } from 'cloudflare:workers';
import { contentRelease } from '@/lib/server/content-release.mjs';
import plan from '@/lib/server/content-release-plan.json';
export const dynamic = 'force-dynamic';
export const POST = (request: Request) => contentRelease(request, env.DB, plan, {
  publicKey: env.CONTENT_RELEASE_PUBLIC_KEY,
  expiresAt: env.CONTENT_RELEASE_EXPIRES_AT,
  allowance: env.CONTENT_RELEASE_ALLOWANCE,
});
