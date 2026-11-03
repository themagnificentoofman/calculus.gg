import { env } from 'cloudflare:workers';
import { bankPreflight } from '@/lib/server/bank-preflight';
export const POST = (request: Request) => bankPreflight(request, env.DB, env.BANK_OPS_PUBLIC_KEY, env.BANK_OPS_EXPIRES_AT);
