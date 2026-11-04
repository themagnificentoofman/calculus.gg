import test from 'node:test';
import assert from 'node:assert/strict';
import {adaptCandidate,digest} from '../scripts/bank/quality/adapt.mjs';
import {contentAttribution} from '../lib/bank/content-attribution.mjs';
import {presentBankProblem} from '../lib/server/solution-presentation.mjs';
import {assertSolutionQuality} from '../lib/bank/solution-quality.mjs';
import {publicGame,playerView} from '../lib/server/game-engine.ts';
import {createHash} from 'node:crypto';
const raw={familyId:'test-quality-adapter',topic:'limits',difficulty:'easy',statement:'2+2=?',choices:[1,2,3,4].map(n=>({choiceId:String(n),math:String(n),misconception:n===4?'correct':'Test-only alternative'})),answerChoiceId:'4',solutionSteps:['2+2=4','4'],pedagogy:{constructionId:'test-quality-adapter',relatedIdeaGroupId:'test',structuralSignature:'test',primaryTechnique:'test-addition',alternativeTechniques:[],prerequisites:[],reasoningDemand:['execution'],answerForm:'integer',difficultyRationale:'Test fixture',sourceRecordIds:[]}};
function approval(value=raw){return {familyId:raw.familyId,module:'test-only-not-registered',index:0,reviewId:'test-only',rawSha256:digest(value),verifier:'test-only',finiteDomain:{indices:[0]},review:{status:'independently-reviewed',author:'fixture-author',reviewer:'fixture-reviewer',report:'test-only',reportSha256:'a'.repeat(64),centralDecision:'Addition',nearestNeighbor:'A test fixture, no playable content',easiestOptionsVisibleRoute:'Direct addition',difficultyRationale:'Test fixture, no calibration claim',difficulty:'easy',optionAuditReport:'test-only',optionAuditSha256:'b'.repeat(64)}};}
test('adapter requires exact finite source and independent options-visible review, and does not confer registry admission',()=>{
 const entry=approval(),p=adaptCandidate(raw,entry);assert.equal(p.validation.humanReviewed,false);
 assert.throws(()=>assertSolutionQuality(presentBankProblem(p)),/source-bound/);
 assert.throws(()=>adaptCandidate({...raw,answerChoiceId:'3'},entry),/Unknown or changed/);
 assert.throws(()=>adaptCandidate(raw,{...entry,review:{...entry.review,reviewer:entry.review.author}}),/independent/i);
 assert.throws(()=>adaptCandidate(raw,{...entry,review:{...entry.review,difficulty:'olympiad',qualifiedOlympiad:false}}),/Unqualified/);
 assert.throws(()=>adaptCandidate(raw,{...entry,contentHash:'0'.repeat(64)}),/destination hash/);
});
test('cross-language source binding keeps decimal literals and exact large integer evidence',()=>{
 const serialized=JSON.stringify({...raw,verificationEvidence:[{decimal:4,exact:0}]}).replace('"decimal":4','"decimal":4.0').replace('"exact":0','"exact":9007199254740993');
 const entry={...approval(),rawSha256:createHash('sha256').update(serialized).digest('hex')};
 const p=adaptCandidate(serialized,entry);
 assert.equal(p.validation.evidence.executedChecks[0].decimal,4);
 assert.equal(p.validation.evidence.executedChecks[0].exact,'9007199254740993');
 assert.throws(()=>adaptCandidate(serialized.replace('4.0','4'),entry),/changed finite source/);
});
test('editorial supplements bind missing choice routes and original lineage without changing frozen math or hiding adaptation',()=>{
 const source={...raw,choices:raw.choices.map(({misconception,...c})=>c),provenance:{kind:'original-constructor-extension'}};
 const supplement={rawSha256:digest(source),report:'test-only-source-bound-metadata',reportSha256:'c'.repeat(64),originalProvenanceKind:source.provenance.kind,choiceMisconceptions:Object.fromEntries(raw.choices.map(c=>[c.choiceId,c.misconception]))};
 const entry={...approval(source),editorialSupplement:supplement};
 const p=adaptCandidate(source,entry);assert.equal(p.provenance.kind,'original');assert.equal(p.provenance.authoring.rawSha256,digest(source));assert.deepEqual(p.choices,raw.choices);
 assert.throws(()=>adaptCandidate(source,{...entry,editorialSupplement:{...supplement,rawSha256:'0'.repeat(64)}}),/Unbound/);
 assert.throws(()=>adaptCandidate(source,{...entry,editorialSupplement:{...supplement,choiceMisconceptions:{...supplement.choiceMisconceptions,extra:'unused'}}}),/exact choices/);
 const existing={...source,choices:[{...source.choices[0],misconception:'existing reviewed route'},...source.choices.slice(1)]};
 assert.throws(()=>adaptCandidate(existing,{...approval(existing),editorialSupplement:{...supplement,rawSha256:digest(existing)}}),/without replacing/);
 const adapted={...source,provenance:{...source.provenance,independentOriginal:false}};
 assert.throws(()=>adaptCandidate(adapted,{...approval(adapted),editorialSupplement:{...supplement,rawSha256:digest(adapted)}}),/cannot use original/);
 assert.throws(()=>adaptCandidate(source,{...entry,editorialSupplement:{...supplement,statement:'rewrite'}}),/unsupported/);
});
function adaptation(){return {...raw,provenance:{kind:'adapted',sourceRecordId:'source-native-activity',sourceUrl:'https://example.org/activity',sourceItemLocator:'Activity 1',upstreamCreators:['Fixture author'],upstreamCopyright:'Fixture copyright',modificationNotice:'Test-only transformation',sourceInspectionEvidenceId:'fixture-inspection',permissionEvidenceId:'fixture-permission',licenseScope:'This test fixture only',licenseUrl:'https://creativecommons.org/licenses/by-sa/4.0/',independentOriginal:false,sourceLicense:'CC-BY-SA-4.0',adapterLicense:'CC-BY-SA-4.0',license:'CC-BY-SA-4.0',attribution:'Fixture credit'}};}
test('adaptations require exact source permission, content license and credit; cannot be relabeled original',()=>{
 const value=adaptation(),entry={...approval(value),adaptation:{sourceRegister:'test-only-register',sourceRegisterSha256:'c'.repeat(64),sourceRecordId:'source-native-activity'}};
 const p=adaptCandidate(value,entry);assert.equal(p.provenance.kind,'adapted');assert.equal(p.provenance.authoring.independentOriginal,false);assert.equal(contentAttribution(p).sourceItem,'Activity 1');
 for(const key of ['sourceRecordId','permissionEvidenceId','modificationNotice','upstreamCreators']){const changed=structuredClone(value);delete changed.provenance[key];assert.throws(()=>adaptCandidate(changed,{...entry,rawSha256:digest(changed)}),/Adapted content/);}
 const disguised={...value,provenance:{...value.provenance,kind:'original'}};assert.throws(()=>adaptCandidate(disguised,{...entry,rawSha256:digest(disguised)}),/cannot use original/);
 assert.throws(()=>contentAttribution({...p,provenance:{...p.provenance,sourceUrl:'javascript:bad'}}),/Incomplete/);
});
test('item credits are retained privately and exposed with the answered review, without leaking answer metadata before answering',()=>{
 const p=adaptation(),credit=contentAttribution(p),question={latexProblem:raw.statement,options:raw.choices.map(c=>c.math),correctIndex:3,explanation:raw.solutionSteps,topic:'limits',difficulty:'easy',contentAttribution:credit};
 const game={status:'active',mode:'test',players:['player'],scores:{player:0},questions:[question],answers:{player:{}}};
 assert.equal(publicGame(game).questions[0].contentAttribution,undefined);assert.deepEqual(playerView(game,'player').progress.reviews,{});
 const notice=publicGame(game).questions[0].contentNotice;assert.equal(notice.license,credit.license);assert.equal(notice.sourceUrl,credit.sourceUrl);assert.equal(notice.modifications,undefined);
 game.answers.player[0]={selectedOption:3,correct:true,xp:1,timeMs:1};
 assert.deepEqual(playerView(game,'player').progress.reviews[0].contentAttribution,credit);assert.equal(game.questions[0].contentAttribution,credit);
});
