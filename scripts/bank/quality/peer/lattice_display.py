"""Independent syntactic whole-term equality, exact prior presentation binding."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def signed_terms(tex):
 text=''.join(tex.split());depth=0;start=0;sign=1;terms=[]
 if text[0]=='-':sign=-1;start=1
 for i,c in enumerate(text):
  if c=='{':depth+=1
  if c=='}':depth-=1;assert depth>=0
  if c in '+-'and depth==0 and i>start:
   term=text[start:i];assert term.startswith('\\frac{');terms.append((sign,term));start=i+1;sign=1 if c=='+'else-1
 assert depth==0 and text[start:].startswith('\\frac{');terms.append((sign,text[start:]));return Counter(terms)
def main(source,originals,served,output):
 source,originals,served,output=map(Path,[source,originals,served,output]);assert not output.exists()
 old={r['problemId']:r for r in map(json.loads,originals.read_text().splitlines())};visible={r['problemId']:r for r in map(json.loads,served.read_text().splitlines())};records=[]
 for r in map(json.loads,source.read_text().splitlines()):
  prior=old[r['sourcePreview']['problemId']];current=visible[prior['problemId']];assert digest(prior)==r['sourcePreview']['canonicalRawHash']
  assert r['statement']==current['statement']and r['answerChoiceId']==current['answerChoiceId']and r['difficulty']==current['difficulty']
  assert r['solutionSteps'][:-1]==current['solutionSteps'][:-1]
  before={c['choiceId']:c for c in current['choices']};assert set(before)=={c['choiceId']for c in r['choices']}
  checked=[]
  for c in r['choices']:
   assert c['misconception']==before[c['choiceId']]['misconception']
   assert signed_terms(c['math'])==signed_terms(before[c['choiceId']]['math'])
   checked.append({'choiceId':c['choiceId'],'before':before[c['choiceId']]['math'],'after':c['math'],'signedCompleteTermsIdentical':True})
  assert signed_terms(r['solutionSteps'][-1])==signed_terms(current['solutionSteps'][-1])
  assert r['solutionSteps'][-1]==next(c['math']for c in r['choices']if c['choiceId']==r['answerChoiceId'])
  records.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':digest(r),'sourcePreview':r['sourcePreview'],'literalChoiceEqualities':checked,
   'equivalentConclusion':True,'allEarlierStepsIdentical':True,'passed':True})
 assert len(records)==8
 output.write_text(json.dumps({'inputSha256':sha(source),'originalsSha256':sha(originals),'servedSha256':sha(served),'reviewerCodeSha256':sha(Path(__file__)),
  'author':'series_final_review','reviewer':'root','records':records,'instances':8,'literalEqualities':32,
  'scope':'Owner check uses signed complete-term multisets, independently of the author symbolic parser. Commutativity of addition proves exact equality with no assumptions about special functions. The earlier complete task proofs remain separately bound; this review does not claim a new derivation or idea.'},indent=2)+'\n');print(json.dumps({'passed':8,'reportSha256':sha(output)}))
if __name__=='__main__':main(*sys.argv[1:])
