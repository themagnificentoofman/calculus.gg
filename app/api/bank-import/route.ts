import { env } from 'cloudflare:workers';
import { bankPilot } from '../../../lib/server/bank-pilot.mjs';
export const dynamic = 'force-dynamic';
export function POST(request: Request) {
  return bankPilot(request, env.DB, env.BANK_PILOT_PUBLIC_KEY, env.BANK_PILOT_EXPIRES_AT);
}
