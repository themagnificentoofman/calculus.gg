import{readFileSync,realpathSync}from'node:fs';
import{resolve,relative,isAbsolute}from'node:path';
import{fileURLToPath}from'node:url';
import{createHash}from'node:crypto';
const ROOT=fileURLToPath(new URL('../../../',import.meta.url));
export function verifySelectionVocabulary(root=ROOT){
 const registry=JSON.parse(readFileSync(resolve(root,'lib/server/selection-vocabulary.json'),'utf8'));
 if(registry.version!==1||registry.status!=='source-bound-reviewed'||!registry.sourceDefinitions)throw Error('Selection vocabulary has not passed exact-source review');
 const path=realpathSync(resolve(root,registry.sourceDefinitions.path)),rel=relative(realpathSync(root),path);
 if(rel.startsWith('..')||isAbsolute(rel))throw Error('Selection review must be inside the source tree');
 const bytes=readFileSync(path);if(createHash('sha256').update(bytes).digest('hex')!==registry.sourceDefinitions.sha256)throw Error('Selection vocabulary review changed');
 const groups=JSON.parse(bytes);if(groups.status!=='independently-reviewed'||Object.keys(registry.items).length>20000||Object.keys(registry.history).length>20000)throw Error('Unreviewed or unbounded selection vocabulary');
 for(const[key,item]of Object.entries(registry.items)){
  const d=groups.itemDefinitions[key];
  if(!d||d.sourceContentHash!==item.sourceContentHash||d.sourceFamily!==item.sourceFamily||d.constructionFamilyId!==item.family||d.relatedIdeaGroupId!==item.idea||d.structuralSignature!==item.structure||d.primaryTechnique!==item.technique)throw Error('Selection feature disagrees with exact review: '+key);
 }
 for(const[id,signatures]of Object.entries(registry.history)){
  const allowed=Object.entries(registry.items).filter(([key])=>key.startsWith(id+'@')).map(([,v])=>v);
  for(const[signature,item]of Object.entries(signatures)){
   const fields=JSON.parse(signature);if(fields.length!==4||!fields.every(x=>typeof x==='string')||!allowed.some(d=>d.family===item.family&&d.idea===item.idea&&d.structure===item.structure&&d.technique===item.technique))throw Error('Unbound historical vocabulary');
  }
 }
 return {records:Object.keys(registry.items).length,historyProblemIds:Object.keys(registry.history).length};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(verifySelectionVocabulary());
