import {withCurrentReviews} from '../lib/solution-review-view.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {solutionQualityIssues,assertSolutionQuality} from '../lib/bank/solution-quality.mjs';
import {presentBankProblem,reviewSavedQuestion,isReviewedLegacyHash} from '../lib/server/solution-presentation.mjs';
import {validateRecord,hash} from '../scripts/bank/admin.mjs';
import {playerView} from '../lib/server/game-engine.ts';
const sample=JSON.parse(readFileSync(new URL('./fixtures/bank/review-samples.json',import.meta.url)))[0];
const reviewed=()=>presentBankProblem(structuredClone(sample));
test('review is source-bound, preserves immutable identities/choice order/answers, and never mutates its input',()=>{
 const original=structuredClone(sample),p=presentBankProblem(original);
 assert.deepEqual(original,sample);assert.equal(p.contentHash,sample.contentHash);assert.equal(p.answerChoiceId,sample.answerChoiceId);
 assert.deepEqual(p.choices.map(c=>c.choiceId),sample.choices.map(c=>c.choiceId));assertSolutionQuality(p);
 assert.equal(isReviewedLegacyHash(sample.contentHash),true);assert.equal(isReviewedLegacyHash('0'.repeat(64)),false);
 for(const changed of [{contentHash:'0'.repeat(64)},{problemRevision:2},{familyId:'not-reviewed'},{templateVersion:'future-unreviewed'}])assert.throws(()=>assertSolutionQuality(presentBankProblem({...sample,...changed})),/source-bound/);
 const fake={...sample,statement:'0',solutionQuality:p.solutionQuality};delete fake.contentHash;fake.contentHash=hash(fake);
 assert.throws(()=>validateRecord(fake),/source-bound/,'self-declared approval cannot register new content');
});
test('admission rejects ambiguous symbols, noncanonical notation, broken formulas, prose wrapping and unsupported conclusions',()=>{
 const p=reviewed(),last=p.solutionSteps.at(-1),cases=[
  [String.raw`\textnormal{Here }m=6.`,last],
  [String.raw`F(b)-F(a)=1`,last],
  [String.raw`\log x`,last],
  [String.raw`\begin{gathered}\textnormal{Do this}\\\textnormal{then that}\end{gathered}`,last],
  [String.raw`\textnormal{Use x^2 for the function.}`,last],
  [String.raw`x=1,quad y=2`,last],
  [String.raw`x=1,qquad y=2`,last],
  [String.raw`a_12=3`,last],
  [String.raw`x^12=3`,last],
  [String.raw`\frac{1}{`,last],
  [...p.solutionSteps,'not the verified answer']
 ];
 for(const solutionSteps of cases)assert.ok(solutionQualityIssues({...p,solutionSteps}).length,solutionSteps.join(' / '));
});
test('reviewed private solutions stay behind the accepted-answer gate and preserve grading',()=>{
 const p=reviewed(),question={problemId:p.problemId,problemRevision:p.problemRevision,contentHash:p.contentHash,bankRelease:'cn-2026-11-03-ideas-v3',familyId:p.familyId,context:{parameters:p.parameters},latexProblem:p.statement,options:p.choices.map(c=>c.math),correctIndex:p.choices.findIndex(c=>c.choiceId===p.answerChoiceId),explanation:sample.solutionSteps,topic:p.topic,difficulty:p.difficulty};
 const game={mode:'test',status:'active',players:['alice'],scores:{alice:0},questions:[question],answers:{alice:{}}},before=structuredClone(game);
 const view=playerView(game,'alice');assert.deepEqual(view.progress.reviews,{});assert.ok(!JSON.stringify(view.game).includes('explanation'));assert.ok(!JSON.stringify(view.game).includes('solutionQuality'));
 game.answers.alice[0]={selectedOption:0,correct:true,xp:10,timeMs:1000};const answer=structuredClone(game.answers.alice[0]);
 const after=playerView(game,'alice');assert.deepEqual(after.progress.answers[0],answer);assert.equal(after.progress.reviews[0].correctIndex,question.correctIndex);assert.equal(after.progress.reviews[0].explanationClarified,true);
 assert.deepEqual(game.questions,before.questions);assert.deepEqual(after.progress.reviews[0].explanation,p.solutionSteps);
 assert.equal(reviewSavedQuestion({...question,contentHash:'0'.repeat(64)}),null);
 assert.equal(reviewSavedQuestion({...question,context:undefined}),null,'missing historical source context is not guessed');
});

test('delayed review snapshots cannot undo a clarification or expose an unanswered solution',()=>{
 const accepted={selectedOption:2,correct:false,xp:0},old={answers:{0:accepted},reviews:{0:{correctIndex:1,explanation:['old']}}};
 const current={0:{correctIndex:1,explanation:['clarified'],solutionReviewVersion:'worked-solutions-v1'},1:{correctIndex:3,explanation:['private'],solutionReviewVersion:'worked-solutions-v1'}};
 const p=withCurrentReviews(old,current);assert.deepEqual(p.answers,old.answers);assert.equal(p.reviews[0].explanation[0],'clarified');assert.equal(p.reviews[1],undefined);assert.equal(old.reviews[0].explanation[0],'old');
});
test('the reported symmetry example and uncommon-notation examples are exact-source reviewed',()=>{
 const records=JSON.parse(readFileSync(new URL('./fixtures/bank/solution-review-examples.json',import.meta.url)));
 for(const original of records){const p=presentBankProblem(original);assertSolutionQuality(p);assert.equal(p.contentHash,original.contentHash);assert.equal(p.answerChoiceId,original.answerChoiceId);assert.deepEqual(p.choices.map(c=>c.choiceId),original.choices.map(c=>c.choiceId));
  assert.throws(()=>assertSolutionQuality(presentBankProblem({...original,contentHash:'f'.repeat(64)})),/source-bound/);
 }
 const p=presentBankProblem(records[0]);assert.equal(p.problemId,'cn_c05d5e5ff7186cb58716');assert.ok(!p.solutionSteps.some(s=>/\bm=/.test(s)));assert.match(p.solutionSteps.join(' '),/odd/);assert.equal(p.solutionSteps.at(-1),'1');
});

test('all 24 harmonic statements use the same defined harmonic notation as their solutions',()=>{
 const records=JSON.parse(readFileSync(new URL('./fixtures/bank/harmonic-source-examples.json',import.meta.url)));
 assert.equal(records.length,24);assert.equal(new Set(records.map(p=>p.familyId)).size,3);
 for(const original of records){
  assert.match(original.statement,/operatorname\{harmonic\}/);
  const p=presentBankProblem(original);assertSolutionQuality(p);
  assert.doesNotMatch([p.statement,...p.solutionSteps,...p.choices.map(c=>c.math)].join(' '),/operatorname\{harmonic\}/);
  assert.match(p.statement,/H_k/);assert.match(p.statement,/H_n=/);
  assert.equal(p.contentHash,original.contentHash);assert.equal(p.answerChoiceId,original.answerChoiceId);
  assert.equal(p.problemRevision,original.problemRevision);
  assert.ok(solutionQualityIssues({...p,statement:original.statement}).some(s=>s.includes('computer function')));
 }
});

test('statement clarifications keep equations out of prose and bind to unchanged source identities',()=>{
 const records=JSON.parse(readFileSync(new URL('./fixtures/bank/statement-source-examples.json',import.meta.url)));
 assert.equal(records.length,138);assert.equal(new Set(records.map(p=>p.familyId)).size,18);
 for(const original of records){
  const p=presentBankProblem(original);assertSolutionQuality(p);
  assert.notEqual(p.statement,original.statement);assert.equal(p.contentHash,original.contentHash);
  assert.equal(p.answerChoiceId,original.answerChoiceId);assert.equal(p.problemRevision,original.problemRevision);
  assert.deepEqual(p.choices.map(c=>c.choiceId),original.choices.map(c=>c.choiceId));
  assert.throws(()=>assertSolutionQuality(presentBankProblem({...original,contentHash:'f'.repeat(64)})),/source-bound/);
 }
 const p=reviewed();
 assert.ok(solutionQualityIssues({...p,statement:String.raw`\textnormal{Find x/y.}`}).some(s=>s.includes('plain prose')));
 assert.ok(!solutionQualityIssues({...p,statement:String.raw`\textnormal{A flow of 2 L/min and concentration 3 g/L.}`}).some(s=>s.includes('plain prose')));
});

test('dyadic tangent explanations use explicit numeric multiplication without rewriting saved questions',()=>{
 const records=JSON.parse(readFileSync(new URL('./fixtures/bank/binary-tangent-source-examples.json',import.meta.url)));
 assert.equal(records.length,8);
 for(const original of records){
  const before=structuredClone(original),p=presentBankProblem(original),m=original.provenance.authoring.builderParameters.m;
  assertSolutionQuality(p);assert.deepEqual(original,before);
  assert.equal(p.contentHash,original.contentHash);assert.equal(p.semanticHash,original.semanticHash);
  assert.equal(p.answerChoiceId,original.answerChoiceId);
  const snapshot={...original,solutionReviewVersion:'worked-solutions-v1',explanation:original.solutionSteps};
  const saved=structuredClone(snapshot);
  assert.equal(reviewSavedQuestion(snapshot).clarified,true,'a later correction under the same format contract remains visible as a clarification');
  assert.deepEqual(snapshot,saved,'the recorded explanation is immutable');
  assert.equal(reviewSavedQuestion({...snapshot,explanation:p.solutionSteps}).clarified,false);
  const text=p.solutionSteps.join('\n');
  for(const exponent of ['k','N']){
   assert.ok(text.includes(String.raw`\frac1{${m}\cdot2^${exponent}}`));
   assert.ok(!text.includes(String.raw`\frac1{${m}2^${exponent}}`));
  }
 }
});
