// Pure format helpers shared by the private operator and Worker. No Node dependencies.
export const canonical = value => value && typeof value === 'object'
  ? Array.isArray(value) ? `[${value.map(canonical).join(',')}]`
    : `{${Object.keys(value).sort().map(k => JSON.stringify(k)+':'+canonical(value[k])).join(',')}}`
  : JSON.stringify(value);
export const hex = value => Array.from(new Uint8Array(value), v => v.toString(16).padStart(2,'0')).join('');
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
export function mergeMetadata(shared, residual) {
  const result = {...shared};
  for (const [key,value] of Object.entries(residual)) {
    if (['__proto__','constructor','prototype'].includes(key)) throw Error('Invalid metadata key');
    if (Object.hasOwn(result,key)) {
      if (!object(result[key]) || !object(value)) throw Error('Overlapping immutable metadata');
      result[key] = mergeMetadata(result[key],value);
    } else result[key] = value;
  }
  return result;
}
export function reconstruct(row, residual) {
  const p = mergeMetadata(JSON.parse(row.metadata_json),residual);
  if (['problemId','problemRevision','contentHash','semanticHash'].some(k => Object.hasOwn(p,k))) throw Error('Overlapping immutable identity');
  return {...p,problemId:row.problem_id,problemRevision:row.revision,contentHash:hex(row.content_hash),semanticHash:hex(row.semantic_hash)};
}
export async function decodeCompact(row) {
  const compressed = new Uint8Array(row.payload_gzip);
  if (compressed.length > 65536 || row.metadata_json.length > 65536) throw Error('Oversized bank payload');
  const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'));
  const reader = stream.getReader(), parts = []; let size = 0;
  try {
    while (true) {
      const {done,value} = await reader.read(); if (done) break;
      size += value.length;
      if (size > 65536) { await reader.cancel(); throw Error('Oversized decompressed bank payload'); }
      parts.push(value);
    }
  } finally { reader.releaseLock(); }
  const buffer = new Uint8Array(size); let offset = 0;
  for (const part of parts) { buffer.set(part,offset); offset += part.length; }
  const p = reconstruct(row,JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(buffer)));
  const {contentHash,...body} = p;
  const serialized = canonical(body);
  if (new TextEncoder().encode(serialized).length > 65536) throw Error('Oversized canonical bank payload');
  const digest = await crypto.subtle.digest('SHA-256',new TextEncoder().encode(serialized));
  if (hex(digest) !== contentHash) throw Error('Immutable bank hash mismatch');
  return p;
}
