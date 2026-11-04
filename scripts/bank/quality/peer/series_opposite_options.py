"""Independent literal option checks, preserving already reviewed series tasks."""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
from series_literal_choices import parse
from series_intervals import enclose
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def main(folder,out):
 folder=Path(folder);patches=json.loads((folder/'option-patches.json').read_text());sources={r['problemId']:r for r in map(json.loads,(folder/'source-records.jsonl').read_text().splitlines())};results=[]
 for p in patches:
  old=sources[p['problemId']];assert digest(old)==p['sourceRawHash'] and old['contentHash']==p['sourceContentHash'] and old['semanticHash']==p['sourceSemanticHash']
  oldanswer=parse(next(c['math'] for c in old['choices'] if c['choiceId']==old['answerChoiceId']));values=[parse(c['math']) for c in p['choices']];index=next(i for i,c in enumerate(p['choices']) if c['choiceId']==p['answerChoiceId'])
  assert s.simplify(s.expand_log(values[index]-oldanswer,force=True))==0
  bounds=[enclose(v) for v in values]
  assert all(a[1]<b[0] or b[1]<a[0] for a,b in itertools.combinations(bounds,2)),p['problemId']
  assert all(a[0]>0 for a in bounds) or all(a[1]<0 for a in bounds)
  results.append({'problemId':p['problemId'],'familyId':p['familyId'],'sourceRawHash':p['sourceRawHash'],'sourceContentHash':p['sourceContentHash'],'patchSha256':digest(p),'unchangedReviewedCorrectValue':True,'sixLiteralPairInequalities':True,'sameStrictSignForAllChoices':True,'independentRationalEnclosures':[{ 'choiceId':p['choices'][i]['choiceId'],'lower':str(a),'upper':str(b)} for i,(a,b) in enumerate(bounds)],'passed':True})
 report={'status':'independent-option-change-review-passed','author':'source_research','reviewer':'root','records':results,'instances':len(results),'exactPairInequalities':6*len(results),'inputs':{n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ['source-records.jsonl','option-patches.json']},'reviewCode':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['series_opposite_options.py','series_literal_choices.py','series_intervals.py','rational_intervals.py']},'scope':'The mathematical tasks and already independently reviewed correct values are unchanged. This separate implementation parses the literal new choices, proves identity with the prior correct value symbolically, and separates all six pairs using explicit outward rational intervals. It imports no author recipe or author interval code. Final combined stable-ID screen and guarded source/presentation/lineage reconstruction remain separate gates.','intervalTheoremReference':{'url':'https://dlmf.nist.gov/5.11.ii','checked':'2026-11-04','claim':'For positive real log-Gamma, the signed remainder after truncation is bounded by the first neglected term. Recurrence shifts all arguments above32 before using this bound.'},'humanReviewed':False,'formalProofAssistantChecked':False}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'instances':len(results),'exactLiteralPairInequalities':6*len(results),'passed':True}))
if __name__=='__main__':main(*sys.argv[1:])
