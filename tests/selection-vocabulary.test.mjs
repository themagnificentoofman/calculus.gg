import test from 'node:test';
import assert from 'node:assert/strict';
import {selectionFeatures,historicalSelectionFeatures,assertSelectionVocabularySource} from '../lib/server/selection-vocabulary.mjs';

test('reviewed vocabulary joins selector and attempted history without rewriting saved evidence',()=>{
 const row={problem_id:'cn_fixture',revision:2,source_family:'new-label',family_id:'new-label',idea:'alias',structure:'fallback',technique:'generic',combination:'synthesis:generic',weight:.8};
 const selected={sourceFamily:'new-label',sourceContentHash:'exact-source',family:'real-construction',idea:'shared-idea',structure:'reviewed-form',technique:'actual-route'};
 const saved={problemId:'cn_fixture',familyId:'old-label',idea:'alias',structure:'fallback',technique:'generic',combination:'synthesis:generic',lineageId:'historical-id',stage:'attempted',at:12345,roundId:'old-round'};
 const signature=JSON.stringify([saved.familyId,saved.idea,saved.structure,saved.technique]);
 const policy={items:{'cn_fixture@2':selected},history:{cn_fixture:{[signature]:selected}}};
 const frozen=structuredClone(saved),resolved=historicalSelectionFeatures(saved,policy),candidate=selectionFeatures(row,policy);
 assert.equal(candidate.family_id,resolved.familyId);assert.equal(candidate.idea,resolved.idea);assert.equal(candidate.structure,resolved.structure);assert.equal(candidate.technique,resolved.technique);assert.equal(candidate.combination,resolved.combination);
 assert.deepEqual(saved,frozen);for(const field of ['at','roundId','stage','lineageId'])assert.equal(resolved[field],saved[field]);
 assert.equal(historicalSelectionFeatures({...saved,technique:'different-actual-route'},policy).technique,'different-actual-route');
 assert.equal(selectionFeatures({...row,revision:1},policy).technique,'generic');
 assert.throws(()=>selectionFeatures({...row,source_family:'unreviewed-origin'},policy),/source family/);
 assertSelectionVocabularySource({problemId:'cn_fixture',problemRevision:2,familyId:'new-label',contentHash:'exact-source'},policy);
 assert.throws(()=>assertSelectionVocabularySource({problemId:'cn_fixture',problemRevision:2,familyId:'new-label',contentHash:'different-source'},policy),/source revision/);
});
