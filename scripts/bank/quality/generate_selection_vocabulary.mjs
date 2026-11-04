// Generate compact server-only features from the shared exact-source review map.
import {readFileSync,writeFileSync,copyFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
const read=p=>JSON.parse(readFileSync(p,'utf8')),sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const stage='.bank-data/quality/final-candidates-v1',source=stage+'/group-definitions.json',destination='docs/bank/problem-quality/final-admission-v1/selection-groups.json';
if(existsSync(destination))throw Error('Preserve previous final vocabulary');
const groups=read(source);if(groups.status!=='independently-reviewed')throw Error('Unreviewed vocabulary');
const paths=[stage+'/canonical-candidates.jsonl',stage+'/retained-originals.jsonl','../milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl'];
const records=paths.flatMap(p=>readFileSync(p,'utf8').trim().split('\n').map(JSON.parse)),items={},history={},ambiguous=new Set();
for(const p of records){
 const key=p.problemId+'@'+p.problemRevision,d=groups.itemDefinitions[key];
 if(!d||d.sourceContentHash!==p.contentHash||d.sourceFamily!==p.familyId)throw Error('Source-bound descriptor missing: '+key);
 const value={sourceFamily:p.familyId,sourceContentHash:p.contentHash,family:d.constructionFamilyId,idea:d.relatedIdeaGroupId,structure:d.structuralSignature,technique:d.primaryTechnique};
 if(items[key]&&JSON.stringify(items[key])!==JSON.stringify(value))throw Error('Descriptor conflict');items[key]=value;
 const meta=p.pedagogy;
 for(const family of new Set([p.familyId,meta.constructionId,value.family])){
  const signature=JSON.stringify([family,meta.relatedIdeaGroupId,meta.structuralSignature,meta.primaryTechnique]);
  const h=history[p.problemId]??={};
  const normalized={family:value.family,idea:value.idea,structure:value.structure,technique:value.technique};
  const historicalKey=JSON.stringify([p.problemId,signature]);
  // Old exposures do not record a revision. If identical old metadata could
  // denote two genuinely different reviewed routes, retain its saved fields.
  // Current questions already save their resolved route; never guess backward.
  if(ambiguous.has(historicalKey))continue;
  if(h[signature]&&JSON.stringify(h[signature])!==JSON.stringify(normalized)){delete h[signature];ambiguous.add(historicalKey);continue;}
  h[signature]=normalized;
 }
}
copyFileSync(source,destination);
const registry={version:1,status:'source-bound-reviewed',sourceDefinitions:{path:destination,sha256:sha(destination)},items,history};
writeFileSync('lib/server/selection-vocabulary.json',JSON.stringify(registry)+'\n');
writeFileSync(stage+'/selection-vocabulary-binding.json',JSON.stringify({sourceDefinitions:registry.sourceDefinitions,registrySha256:sha('lib/server/selection-vocabulary.json'),records:Object.keys(items).length,historyProblemIds:Object.keys(history).length,generatorSha256:sha('scripts/bank/quality/generate_selection_vocabulary.mjs'),ambiguousOldSignaturesRetainedUnchanged:[...ambiguous].map(JSON.parse),ambiguityPolicy:'Older exposures omit revision. Keep original metadata where a later option/classification revision changes the demonstrated route; exact identity/lineage repeat exclusions still apply. New questions record resolved features.',canonicalRecordsChanged:0,historicalSnapshotsChanged:0},null,2)+'\n');
console.log({records:Object.keys(items).length,historyProblemIds:Object.keys(history).length});
