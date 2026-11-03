#!/usr/bin/env node
import { generateKeyPairSync, sign } from 'node:crypto';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
const dir = '.bank-data/authorization';
mkdirSync(dir, { recursive: true, mode: 0o700 });
if (process.argv[2] === 'prepare') {
  if (existsSync(dir + '/private.pem')) throw Error('Preserve the existing authorization; do not rotate implicitly');
  const { privateKey, publicKey } = generateKeyPairSync('ed25519');
  writeFileSync(dir + '/private.pem', privateKey.export({ type: 'pkcs8', format: 'pem' }), { mode: 0o600 });
  const authorization = { publicKey: publicKey.export({ type: 'spki', format: 'der' }).toString('base64'), expiresAt: Date.now() + 60 * 60_000 };
  writeFileSync(dir + '/public.json', JSON.stringify(authorization), { mode: 0o600 });
  console.log(JSON.stringify(authorization));
} else {
  const timestamp = String(Date.now());
  const signature = sign(null, Buffer.from(`calculus-ninja-d1-preflight-v1\nPOST\n/api/bank-preflight\n${timestamp}`), readFileSync(dir + '/private.pem')).toString('base64');
  const response = await fetch('https://calculus.ninja/api/bank-preflight', { method: 'POST', headers: { 'x-bank-time': timestamp, 'x-bank-signature': signature }, redirect: 'error', signal: AbortSignal.timeout(30_000) });
  const body = await response.text();
  if (!response.ok) throw Error(`Preflight HTTP ${response.status}: ${body.slice(0,200)}`);
  const result = JSON.parse(body);writeFileSync(dir + '/result.json', JSON.stringify(result, null, 2) + '\n');console.log(JSON.stringify(result, null, 2));
}
