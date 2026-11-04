import test from 'node:test';
import assert from 'node:assert/strict';
import {auditGroup,features} from '../scripts/bank/quality/option-audit.mjs';
test('held-out family screen reproduces the radial-log divisibility clue using training alone',()=>{
 const records=Array.from({length:30},(_,i)=>({problemId:'radial-test-'+i,familyId:'radial-log',choices:[0,5,9,11].map((d,j)=>({choiceId:String(j),math:String(14400*(i+41)+d)})),answerChoiceId:'0'}));
 const result=auditGroup(records),divisible=result.results.find(r=>r.rule==='integer-divisible-14400');
 assert.equal(divisible.heldout.expectedTieBrokenAccuracy,1);assert.equal(divisible.heldout.uniqueCorrect,15);assert(result.reviewRequired);
 assert.equal(new Set([...result.trainingIds,...result.heldoutIds]).size,30);
});
test('numeric and symbolic-form coverage is explicit, and tiny families cannot self-clear',()=>{
 assert.equal(features('\\frac{3}{7}').numeric,3/7);assert.equal(features('\\pi^2').numeric,null);assert.equal(features('120000').trailingZeros,4);
 const p={problemId:'single',familyId:'one',choices:['\\pi','\\sqrt{2}','e','\\ln 2'].map((math,i)=>({choiceId:String(i),math})),answerChoiceId:'0'};
 const result=auditGroup([p]);assert.equal(result.reviewRequired,true);assert.equal(result.selectedUsingTrainingOnly.heldout.items,0);
});
test('a repair cannot hide a singleton rational-power clue behind matched fraction formatting',()=>{
 const make=competitor=>Array.from({length:10},(_,i)=>({problemId:'cube-repair-'+i,familyId:'negative-binomial',choices:['\\frac{27}{8}',competitor,'\\frac{9}{5}','\\frac{17}{10}'].map((math,j)=>({choiceId:String(j),math})),answerChoiceId:'0'}));
 const failed=auditGroup(make('\\frac{11}{7}')).results.find(r=>r.rule==='rationalCube-max');
 assert.equal(failed.training.expectedTieBrokenAccuracy,1);assert.equal(failed.heldout.expectedTieBrokenAccuracy,1);
 const repaired=auditGroup(make('\\frac{125}{64}')).results.find(r=>r.rule==='rationalCube-max');
 assert.equal(repaired.heldout.expectedTieBrokenAccuracy,.5);assert.equal(repaired.heldout.uniquePredictions,0);
 assert.equal(features('\\frac{64}{216}').rationalCube,1);assert.equal(features('-\\frac{8}{27}').rationalCube,1);
 assert.equal(features('-\\frac{8}{27}').rationalSquare,0);assert.equal(features('\\frac{16}{81}').rationalSquare,1);
 assert.equal(features('\\sqrt{2}').rationalCube,null);
});
test('a lone sign-error pair leaks the magnitude even when ordinary numeric ranks vary',()=>{
 const make=competingPair=>Array.from({length:12},(_,i)=>{
  const a='\\frac{2}{'+(i+5)**3+'}',b='\\frac{1}{'+(i+4)**2+'}';
  return {problemId:'sign-pair-'+i,familyId:'log-moment',choices:[a,'- '+a,b,competingPair?'- '+b:'\\frac{1}{'+(i+7)**3+'}'].map((math,j)=>({choiceId:String(j),math})),answerChoiceId:'0'};
 });
 const leaked=auditGroup(make(false)).results.find(r=>r.rule==='opposite-pair-positive');
 assert.equal(leaked.training.expectedTieBrokenAccuracy,1);assert.equal(leaked.heldout.expectedTieBrokenAccuracy,1);
 const competing=auditGroup(make(true)).results.find(r=>r.rule==='opposite-pair-positive');
 assert.equal(competing.heldout.expectedTieBrokenAccuracy,.5);assert.equal(competing.heldout.uniquePredictions,0);
});
