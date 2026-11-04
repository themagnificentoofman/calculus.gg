// Immutable review-derived vocabulary; history is normalized only in memory.
import registry from './selection-vocabulary.json' with {type:'json'};
const key=p=>p.problem_id+'@'+p.revision;
export function selectionFeatures(row,policy=registry){
 const reviewed=policy.items[key(row)];
 if(!reviewed)return row;
 if(reviewed.sourceFamily!==row.source_family)throw Error('Selection vocabulary source family mismatch');
 const combination=row.combination?.endsWith(':'+row.technique)?row.combination.slice(0,-row.technique.length)+reviewed.technique:row.combination;
 return {...row,family_id:reviewed.family,idea:reviewed.idea,structure:reviewed.structure,technique:reviewed.technique,combination};
}
export function assertSelectionVocabularySource(problem,policy=registry){
 const entry=policy.items[problem.problemId+'@'+problem.problemRevision];
 if(entry&&(entry.sourceContentHash!==problem.contentHash||entry.sourceFamily!==problem.familyId))throw Error('Selection vocabulary source revision mismatch');
}
export function historicalSelectionFeatures(exposure,policy=registry){
 const entry=policy.history[exposure.problemId];
 const signature=JSON.stringify([exposure.familyId,exposure.idea,exposure.structure,exposure.technique]);
 const reviewed=entry?.[signature];
 if(!reviewed)return exposure;
 const combination=exposure.combination?.endsWith(':'+exposure.technique)?exposure.combination.slice(0,-exposure.technique.length)+reviewed.technique:exposure.combination;
 return {...exposure,familyId:reviewed.family,idea:reviewed.idea,structure:reviewed.structure,technique:reviewed.technique,combination};
}
