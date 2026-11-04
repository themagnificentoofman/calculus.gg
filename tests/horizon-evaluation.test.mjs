import test from 'node:test';
import assert from 'node:assert/strict';
import {roundMeasures,acceptanceFailures,compareIntegration} from '../scripts/bank/quality/evaluate-horizons.mjs';

const contract={count:20,rounds:{olympiad:10}};
const good=()=>Array.from({length:10},()=>({count:20,relaxation:'none',exactEquivalentRepeats:0,withinRoundDuplicates:0,sameFamilyAdjacency:0,maxFamily:2}));
test('every required per-round horizon condition is an executable failing gate',()=>{
 assert.deepEqual(acceptanceFailures(good(),{difficulty:'olympiad'},contract),[]);
 for(const [key,value,gate] of [['exactEquivalentRepeats',1,'exactEquivalentRepeats'],['withinRoundDuplicates',1,'withinRoundDuplicates'],['sameFamilyAdjacency',1,'sameFamilyAdjacency'],['maxFamily',3,'family-cap'],['relaxation','recent-problems','relaxation'],['count',19,'question-count'],['error','No content','request-failure']]){
  const rounds=good();rounds[6][key]=value;assert(acceptanceFailures(rounds,{difficulty:'olympiad'},contract).some(f=>f.round===7&&f.gate===gate));
 }
 assert(acceptanceFailures(good().slice(1),{difficulty:'olympiad'},contract).some(f=>f.gate==='incomplete-horizon'));
});
test('equivalent revisions, aliases, primary decisions, and independent idea groups are distinct measures',()=>{
 const groups={items:{new:'old'},families:{a:{constructionFamilyId:'same',relatedIdeaGroupId:'idea',structuralSignature:'s',primaryTechnique:'p',qualifiedOlympiad:true},b:{constructionFamilyId:'same',relatedIdeaGroupId:'idea',structuralSignature:'s',primaryTechnique:'p',qualifiedOlympiad:true}}};
 const result=roundMeasures([{problemId:'old',familyId:'a'},{problemId:'new',familyId:'b'}],groups,new Set(['old']));
 assert.equal(result.exactEquivalentRepeats,2);assert.equal(result.withinRoundDuplicates,1);assert.equal(result.sameFamilyAdjacency,1);assert.equal(result.qualifiedIdeas,1);
 assert.throws(()=>roundMeasures([{problemId:'unknown',familyId:'unknown'}],groups),/Missing independently reviewed/);
});
function report(role,phase,means){return {role,phase,groupDefinitionsSha256:'groups',contractSha256:'contract',cells:[{input:{category:'integration',difficulty:'olympiad'},tolerance:{ideaMeanLoss:.25,methodMeanLoss:.5,nearCloneMeanIncrease:.2},runs:[{seed:1,means}]}]};}
test('an exact options-visible case disposition overrides family qualification without erasing its exposure',()=>{
 const family={constructionFamilyId:'control',relatedIdeaGroupId:'control-energy',structuralSignature:'endpoint-moments',primaryTechnique:'gram-inverse',qualifiedOlympiad:true};
 const groups={families:{control:family},items:{old:'same-task',revised:'same-task'},itemDefinitions:{'old@1':{qualifiedOlympiad:false,primaryTechnique:'elementary-bounds'},'revised@2':{qualifiedOlympiad:false,primaryTechnique:'elementary-bounds'}}};
 for(const q of [{problemId:'old',problemRevision:1,familyId:'control'},{problemId:'revised',problemRevision:2,familyId:'control'}]){
  const result=roundMeasures([q],groups,new Set(['same-task']));
  assert.equal(result.qualifiedIdeas,0);assert.equal(result.exactEquivalentRepeats,1);assert.equal(result.distinctIdeas,1);
 }
 assert.equal(roundMeasures([{problemId:'independent-sibling',problemRevision:1,familyId:'control'}],groups).qualifiedIdeas,1);
});
test('matched integration regression gate uses baseline variability, immutable groups, and exact seeds',()=>{
 const values={distinctIdeas:18,distinctPrimaryMethods:12,closeVariantWindows3:1};
 const base=report('baseline','heldout',values),development=report('baseline','development',values),candidate=report('candidate','heldout',{...values,distinctIdeas:17.7});
 assert.equal(compareIntegration(candidate,base,development).failures[0].metric,'ideaMeanLoss');
 candidate.cells[0].runs[0].means.distinctIdeas=17.8;assert.deepEqual(compareIntegration(candidate,base,development).failures,[]);
 candidate.groupDefinitionsSha256='renamed groups';assert.throws(()=>compareIntegration(candidate,base,development),/identical reviewed groups/);
 candidate.groupDefinitionsSha256='groups';candidate.cells[0].runs[0].seed=2;assert.throws(()=>compareIntegration(candidate,base,development),/matched baseline seed/);
});

test('same exact task does not inherit repaired family-context qualification in baseline metrics',()=>{
 const groups={families:{theta:{constructionFamilyId:'theta',relatedIdeaGroupId:'theta-duality',structuralSignature:'Gaussian-lattice',primaryTechnique:'Poisson-duality',qualifiedOlympiad:true}},itemDefinitions:{'same@1':{qualifiedOlympiad:true,qualificationByRole:{baseline:{qualifiedOlympiad:false,scope:'Original family has a proved middle-two menu clue'},candidate:{qualifiedOlympiad:true,scope:'Repaired family menu context independently reviewed'}}}}};
 const questions=[{problemId:'same',problemRevision:1,familyId:'theta'}];
 assert.equal(roundMeasures(questions,groups,new Set(),'baseline').qualifiedIdeas,0);
 assert.equal(roundMeasures(questions,groups,new Set(),'candidate').qualifiedIdeas,1);
 assert.equal(roundMeasures(questions,groups,new Set(),'baseline').distinctIdeas,roundMeasures(questions,groups,new Set(),'candidate').distinctIdeas);
});
