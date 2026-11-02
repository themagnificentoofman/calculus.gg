// One-time, idempotent rollout step. Credentials are read from stdin, never logged.
import { readFile } from 'node:fs/promises';
import { firestoreStore, serviceAccountToken } from '../lib/server/firestore-admin.ts';
import { publicProfile, identifier } from '../lib/server/game-engine.ts';
const config = JSON.parse(await readFile(new URL('../firebase-applet-config.json', import.meta.url), 'utf8'));
let source = ''; for await (const chunk of process.stdin) source += chunk;
const token = () => serviceAccountToken(source.trim(), config.projectId);
const store = firestoreStore(config.projectId, config.firestoreDatabaseId, token);
const apply = process.argv.includes('--apply');
let next = '', count = 0;
do {
  const url = new URL(`https://firestore.googleapis.com/v1/projects/${config.projectId}/databases/${config.firestoreDatabaseId}/documents/users`);
  url.searchParams.set('pageSize', '100'); if (next) url.searchParams.set('pageToken', next);
  const response = await fetch(url, { headers: { Authorization: `Bearer ${await token()}` }, signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error(`Profile listing failed (${response.status}).`);
  const page = await response.json();
  for (const document of page.documents || []) {
    const uid = identifier(document.name.split('/').at(-1));
    if (apply) await store.transaction(async tx => {
      const profile = await tx.get(`users/${uid}`);
      if (profile) tx.set(`users_public/${uid}`, publicProfile({ ...profile, uid }));
    });
    count++;
  }
  next = page.nextPageToken || '';
} while (next);
console.log(`${apply ? 'Updated' : 'Dry run: would update'} ${count} public profiles. Private records were unchanged.`);
