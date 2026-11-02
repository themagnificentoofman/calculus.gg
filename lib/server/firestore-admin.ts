import { importPKCS8, SignJWT } from 'jose';

export type Data = Record<string, any>;
export interface Transaction { get(path: string): Promise<Data | null>; set(path: string, data: Data): void; delete(path: string): void }
export interface Store { get(path: string): Promise<Data | null>; transaction<T>(fn: (tx: Transaction) => Promise<T>): Promise<T>; find(collection: string, filters: [string, string, unknown][], limit?: number): Promise<{ id: string; data: Data }[]> }
export class StoreError extends Error { status: number; constructor(status: number) { super('Database request failed.'); this.status = status; } }

let cached: { source: string; until: number; token: Promise<string> } | undefined;
export function serviceAccountToken(source: string, projectId: string) {
  if (cached?.source === source && cached.until > Date.now()) return cached.token;
  const token = (async () => {
    const account = JSON.parse(source);
    if (account.project_id !== projectId || typeof account.client_email !== 'string' || typeof account.private_key !== 'string') throw new Error('Invalid server identity.');
    const key = await importPKCS8(account.private_key, 'RS256');
    const assertion = await new SignJWT({ scope: 'https://www.googleapis.com/auth/datastore' }).setProtectedHeader({ alg: 'RS256' })
      .setIssuer(account.client_email).setAudience('https://oauth2.googleapis.com/token').setIssuedAt().setExpirationTime('1h').sign(key);
    const response = await fetch('https://oauth2.googleapis.com/token', { method: 'POST', body: new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion }), signal: AbortSignal.timeout(10000) });
    const result = await response.json() as Data;
    if (!response.ok || typeof result.access_token !== 'string') throw new Error('Server identity unavailable.');
    return result.access_token as string;
  })();
  cached = { source, until: Date.now() + 50 * 60_000, token };
  token.catch(() => { if (cached?.token === token) cached = undefined; });
  return token;
}
export function encode(value: any): any {
  if (value === null) return { nullValue: null };
  if (value instanceof Date) return { timestampValue: value.toISOString() };
  if (typeof value === 'string') return { stringValue: value };
  if (typeof value === 'boolean') return { booleanValue: value };
  if (typeof value === 'number' && Number.isFinite(value)) return Number.isSafeInteger(value) ? { integerValue: String(value) } : { doubleValue: value };
  if (Array.isArray(value)) return { arrayValue: { values: value.map(encode) } };
  if (value && typeof value === 'object') return { mapValue: { fields: Object.fromEntries(Object.entries(value).filter(([, v]) => v !== undefined).map(([k, v]) => [k, encode(v)])) } };
  throw new Error('Invalid database value.');
}
export function decode(value: any): any {
  if ('timestampValue' in value) return new Date(value.timestampValue);
  if ('integerValue' in value) return Number(value.integerValue);
  if ('doubleValue' in value) return value.doubleValue;
  if ('booleanValue' in value) return value.booleanValue;
  if ('stringValue' in value) return value.stringValue;
  if ('nullValue' in value) return null;
  if ('arrayValue' in value) return (value.arrayValue.values || []).map(decode);
  if ('mapValue' in value) return Object.fromEntries(Object.entries(value.mapValue.fields || {}).map(([k, v]) => [k, decode(v)]));
  throw new Error('Unsupported database value.');
}
// HTTP transactions work in Workers without raw TCP or a browser Firebase session.
// The emulator URL is injected by isolated tests only; production always uses Google.
export function firestoreStore(projectId: string, databaseId: string, token: () => Promise<string>, origin = 'https://firestore.googleapis.com'): Store {
  const root = `projects/${projectId}/databases/${databaseId}/documents`;
  const pathName = (path: string) => { if (!/^[a-zA-Z0-9_/-]+$/.test(path) || path.includes('//') || path.startsWith('/')) throw new Error('Invalid document path.'); return `${root}/${path}`; };
  async function request(suffix: string, body?: any, allowMissing = false) {
    const response = await fetch(`${origin}/v1/${root}${suffix}`, { method: body === undefined ? 'GET' : 'POST', headers: { Authorization: `Bearer ${await token()}`, 'Content-Type': 'application/json' }, ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: AbortSignal.timeout(15000) });
    if (allowMissing && response.status === 404) return null;
    if (!response.ok) throw new StoreError(response.status);
    return response.json() as Promise<Data>;
  }
  const get = async (path: string, transaction?: string) => {
    pathName(path);
    if (transaction) {
      const rows = await request(':batchGet', { documents: [pathName(path)], transaction }) as any;
      const found = rows.find((row: any) => row.found)?.found;
      return found ? decode({ mapValue: { fields: found.fields || {} } }) as Data : null;
    }
    const result = await request(`/${path}`, undefined, true);
    return result ? decode({ mapValue: { fields: result.fields || {} } }) as Data : null;
  };
  return {
    get,
    async transaction(fn) {
      for (let attempt = 0; attempt < 6; attempt++) {
        const { transaction } = (await request(':beginTransaction', { options: { readWrite: {} } }))!;
        const writes = new Map<string, any>();
        try {
          const result = await fn({ get: path => { if (writes.size) throw new Error('Read before writing.'); return get(path, transaction); },
            set: (path, data) => { writes.set(path, { update: { name: pathName(path), fields: encode(data).mapValue.fields } }); },
            delete: path => { writes.set(path, { delete: pathName(path) }); } });
          await request(':commit', { transaction, writes: [...writes.values()] });
          return result;
        } catch (error) {
          await request(':rollback', { transaction }).catch(() => {});
          if (!(error instanceof StoreError) || ![409, 503].includes(error.status) || attempt === 5) throw error;
          await new Promise(resolve => setTimeout(resolve, 40 * 2 ** attempt + Math.random() * 30));
        }
      }
      throw new Error('Transaction retry limit reached.');
    },
    async find(collection, filters, limit = 100) {
      if (!/^[a-zA-Z0-9_]+$/.test(collection)) throw new Error('Invalid collection.');
      const predicates = filters.map(([field, op, value]) => {
        if (!/^[a-zA-Z0-9_]+$/.test(field) || !['ARRAY_CONTAINS', 'EQUAL', 'LESS_THAN_OR_EQUAL'].includes(op)) throw new Error('Invalid query filter.');
        return { functionValue: { name: op === 'ARRAY_CONTAINS' ? 'array_contains' : op === 'LESS_THAN_OR_EQUAL' ? 'less_than_or_equal' : 'equal', args: [{ fieldReferenceValue: field }, encode(value)] } };
      });
      const stages = [{ name: 'collection', args: [{ referenceValue: `/${collection}` }] },
        ...(predicates.length ? [{ name: 'where', args: [{ functionValue: { name: 'and', args: predicates } }] }] : []),
        { name: 'limit', args: [encode(Math.max(1, Math.min(1000, limit)))] }];
      const rows = await request(':executePipeline', { structuredPipeline: { pipeline: { stages } } }) as any;
      return rows.flatMap((row: any) => row.results || []).map((document: any) => {
        const { __name__: name, __create_time__: _created, __update_time__: _updated, ...fields } = document.fields || {};
        return { id: (document.name || name?.referenceValue || '').split('/').at(-1), data: decode({ mapValue: { fields } }) };
      });
    },
  };
}
