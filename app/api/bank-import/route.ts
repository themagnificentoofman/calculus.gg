import { env } from 'cloudflare:workers';
import { bankOperator } from '../../../lib/server/bank-operator.mjs';
export const dynamic = 'force-dynamic';
export function POST(request: Request) {
  return bankOperator(request, env.DB, env.BANK_OPERATOR_PUBLIC_KEY, env.BANK_OPERATOR_EXPIRES_AT);
}
