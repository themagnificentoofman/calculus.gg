// Final source binding preserves the frozen topic reviews and public mathematics.
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {canonical,digest} from './adapt.mjs';
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const read=p=>JSON.parse(readFileSync(p,'utf8'));
const lines=p=>readFileSync(p,'utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
const base='docs/bank/problem-quality',out='.bank-data/quality/final-candidates-v1';
if(existsSync(out))throw Error('Preserve earlier finalization');
const topics=[
 ['integration','integration-previews-v5',`${base}/integration/final-group-map-v5.json`,`${base}/integration/final-option-review-v5.json`,`${base}/integration/served-option-review-v5.json`],
 ['diff-limits','diff-limits-previews-v4',`${base}/diff-limits/final-v4/normalized-record-map.jsonl`,`${base}/diff-limits/final-v4/final-option-dispositions.json`],
 ['series','series-previews-v7',`${base}/series/final-v7/item-group-map.json`,`${base}/series/final-v7/final-option-review.json`],
 ['ode-mv','ode-mv-previews-v7',`${base}/ode-mv/final-v7/group-map.json`,`${base}/ode-mv/final-v7/family-form-dispositions.json`]
];
const prior=read('scripts/bank/quality/reviewed.json'),entries={},records=[],retained=[],definitions=[],destinations=[],sourceArtifacts={};
const bind=p=>(sourceArtifacts[p]=sha(p),p);
const lateRoutes=new Set(['limits-recurrence-options','ode-nonnormal-options','mv-density-classification','ode-ground-options','series-lattice-display']);
for(const [topic,folder,mapPath,reportPath,servedPath]of topics){
 const stage='.bank-data/quality/'+folder;
 const maps=mapPath.endsWith('jsonl')?lines(bind(mapPath)):read(bind(mapPath)).records;
 const byId=new Map(maps.map(r=>[r.problemId,r]));
 const es=read(bind(stage+'/admission-previews.json'));
 const candidates=lines(bind(stage+'/canonical-previews.jsonl')),old=lines(bind(stage+'/retained-originals.jsonl'));
 const report=read(bind(reportPath));if(report.unresolved?.length||report.requiredActions?.length)throw Error('Unresolved final review: '+topic);
 if(servedPath)bind(servedPath);
 if(byId.size!==candidates.length+old.length)throw Error('Incomplete final map '+topic);
 for(const p of [...candidates,...old]){
  const m=byId.get(p.problemId);if(!m||m.contentHash!==p.contentHash||(m.revision??m.problemRevision)!==p.problemRevision||m.recommendedDifficulty!==p.difficulty)throw Error('Source-map mismatch '+p.problemId);
 }
 for(const p of candidates){
  const rid=p.provenance.authoring.reviewId,e=structuredClone(es[rid]);if(!e||entries[rid])throw Error('Review identity collision');
  const original=structuredClone(p),q=structuredClone(p),sameEarlier=prior.items[rid]?.contentHash===p.contentHash;
  e.supplementalReports||=[];
  const supplement=(path,purpose)=>{if(!e.supplementalReports.some(r=>r.path===path))e.supplementalReports.push({path,sha256:sha(path),purpose});};
  if(lateRoutes.has(e.module)){
   const peer=read(e.review.report);if(!peer.author||!peer.reviewer||peer.author===peer.reviewer)throw Error('Missing actual overlay identities '+rid);
   e.review.author=peer.author;e.review.reviewer=peer.reviewer;
  }
  if(!sameEarlier){
   e.review.optionAuditReport=reportPath;e.review.optionAuditSha256=sha(reportPath);
   q.validation.evidence.optionAuditReport=reportPath;q.validation.evidence.optionAuditSha256=sha(reportPath);
   const {contentHash,...body}=q;q.contentHash=digest(body);
  }
  supplement(reportPath,'Final actual-ID literal-choice and served family/form dispositions; supplements the preserved complete-task mathematical review.');
  if(servedPath)supplement(servedPath,'Exact served notation reconciliation with unchanged held-out split and flag sets.');
  if(e.editorialSupplement)supplement(`${base}/diff-limits-metadata-independent-peer.json`,'Independent exact-source check of complete editorial misconception/provenance supplement.');
  e.contentHash=q.contentHash;
  // Only final evidence references may change. Review names are external metadata.
  const projection=r=>{const v=structuredClone(r);delete v.contentHash;delete v.validation.evidence.optionAuditReport;delete v.validation.evidence.optionAuditSha256;return v;};
  if(canonical(projection(original))!==canonical(projection(q)))throw Error('Public/canonical mathematics changed during final binding');
  entries[rid]=e;records.push(q);definitions.push({...byId.get(q.problemId),contentHash:q.contentHash,reviewedPreviewContentHash:p.contentHash,topic:q.topic});
  destinations.push({reviewId:rid,problemId:q.problemId,revision:q.problemRevision,rawSha256:e.rawSha256,reviewedPreviewContentHash:p.contentHash,contentHash:q.contentHash,unchangedEarlierLocalAdmission:sameEarlier,publicAndMathematicalContentUnchanged:true,topicReview:reportPath});
 }
 // The two already-reviewed pilot adaptations are in the series effective
 // inventory but have never been published. They belong in the import delta.
 retained.push(...old.filter(p=>p.provenance?.authoring?.reviewId?.startsWith('quality-review:quality-series-medium-ac-')!==true));
 definitions.push(...old.map(p=>({...byId.get(p.problemId),topic:p.topic})));
}
for(const p of lines(bind('.bank-data/quality/adapted-pilot-admitted.jsonl'))){
 const e=prior.items[p.provenance.authoring.reviewId];if(e.contentHash!==p.contentHash)throw Error('Pilot binding');
 if(!definitions.some(r=>r.problemId===p.problemId&&r.contentHash===p.contentHash))throw Error('Pilot must already be in the exact effective series review');
 entries[e.reviewId]=e;records.push(p);
}
if(records.length!==3292||retained.length!==1115||new Set([...records,...retained].map(p=>p.problemId)).size!==4407)throw Error('Unexpected final inventory');
mkdirSync(out,{recursive:true});
writeFileSync(out+'/canonical-candidates.jsonl',records.map(canonical).join('\n')+'\n');
writeFileSync(out+'/retained-originals.jsonl',retained.map(canonical).join('\n')+'\n');
writeFileSync(out+'/admission-candidates.json',JSON.stringify(entries,null,2)+'\n');
writeFileSync(out+'/source-definitions.json',JSON.stringify(definitions,null,2)+'\n');
writeFileSync(out+'/destination-binding.json',JSON.stringify({status:'source-bound-finalization-pending-independent-reconstruction',sourceArtifacts,records:records.length,retained:retained.length,sourcePreservation:'Only option-audit evidence references and destination hashes change in previously unadmitted records; all public mathematics, choices, levels and lineage remain identical. Earlier locally registered unchanged records keep their exact hashes.',destinations,imported:0,active:0},null,2)+'\n');
console.log(JSON.stringify({candidates:records.length,retained:retained.length,effective:records.length+retained.length,unchangedEarlierLocalAdmission:destinations.filter(x=>x.unchangedEarlierLocalAdmission).length}));
