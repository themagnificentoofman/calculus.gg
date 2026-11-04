import {readFileSync,realpathSync} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {createLegacyPolicy} from '../../../lib/server/legacy-selection.mjs';
import {canonical} from '../../../lib/bank/compact-codec.mjs';
import {presentBankProblem} from '../../../lib/server/solution-presentation.mjs';
import {assertSolutionQuality} from '../../../lib/bank/solution-quality.mjs';
const ROOT=fileURLToPath(new URL('../../../',import.meta.url));
const sha=value=>createHash('sha256').update(value).digest('hex');

/** Mandatory build and delta gate. Evidence is outside the canonical record,
 * avoiding a circular hash while binding each exact approved revision. */
export function verifyLegacyEligibility(root=ROOT,registry=JSON.parse(readFileSync(resolve(root,'lib/server/legacy-eligibility.json'),'utf8'))) {
 if(registry.schemaVersion!==1)throw Error('Unknown legacy eligibility schema');
 createLegacyPolicy(registry.records);
 const reports=new Map(),resolvedRoot=realpathSync(root);
 for(const approval of registry.records){
  const path=realpathSync(resolve(resolvedRoot,approval.review.path)),rel=relative(resolvedRoot,path);
  if(rel.startsWith('..')||isAbsolute(rel))throw Error('Legacy evidence must be inside the reviewed source tree');
  let report=reports.get(path);
  if(!report){const bytes=readFileSync(path);if(bytes.length>16000000)throw Error('Legacy review exceeds bound');report={hash:sha(bytes),body:JSON.parse(bytes)};reports.set(path,report);}
  if(report.hash!==approval.review.sha256)throw Error('Legacy review hash mismatch');
  const body=report.body;
  if(body.status!=='independently-reviewed'||!body.author||!body.reviewer||body.author===body.reviewer||!Array.isArray(body.records)||body.records.length>20000)throw Error('Independent legacy review required');
  const matches=body.records.filter(r=>r.problem?.problemId===approval.problemId&&r.problem?.problemRevision===approval.revision);
  if(matches.length!==1)throw Error('Legacy approval has no unique exact reviewed revision');
  const item=matches[0],p=item.problem,{contentHash,...contents}=p;
  if(sha(canonical(contents))!==contentHash||contentHash!==approval.contentHash||p.familyId!==approval.familyId
    ||item.constructionId!==approval.constructionId||item.usefulness!==approval.usefulness||item.passed!==true
    ||item.literalOptionsVerified!==true||item.currentPresentationVerified!==true||item.difficulty!==p.difficulty
    ||typeof item.easiestOptionsVisibleRoute!=='string'||!item.easiestOptionsVisibleRoute.trim()
    ||typeof item.optionAuditDisposition!=='string'||!item.optionAuditDisposition.trim())throw Error('Incomplete exact legacy quality/usefulness evidence');
  // The ordinary source-bound mathematical/presentation gate remains required.
  assertSolutionQuality(presentBankProblem(p));
 }
 return {verified:registry.records.length,reports:reports.size};
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(JSON.stringify(verifyLegacyEligibility()));
