"""Every literal choice pair is checked; categorical cases are explicitly scoped."""
from pathlib import Path
import argparse,collections,hashlib,itertools,json
import sympy as s
from literal_math import parse
from enclosures import enclose,dump
BASE=Path(__file__).resolve().parent
CATEGORICAL={
 'm3-series-easy-p-series-pair':'Ordered convergence classifications, not additive mathematical quantities.',
 'm3-series-easy-alternating-absolute-conditional':'Ordered absolute/conditional classifications, not additive mathematical quantities.',
 'm3-series-easy-direct-comparison-information':'Four mutually exclusive logical conclusions, not additive mathematical quantities.',
 'quality-series-olympiad-uniform-log-sine-threshold':'Ordered uniform/not-uniform conclusions, not additive mathematical quantities.',
 'quality-series-olympiad-alternating-infinite-product':'Ordered zero/positive existence classes, not additive mathematical quantities.',
 'quality-series-olympiad-Dirichlet-moment-uniqueness':'Ordered exists/does-not-exist conclusions, not additive mathematical quantities.'}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def scalar_sum(a,b):
 z=a+b
 if z==0:return True,{'method':'exact symbolic cancellation','sum':'0'}
 if z in [s.oo,-s.oo]:return False,{'method':'extended-real sign; no opposing infinity','sum':str(z)}
 if z.is_Rational:return False,{'method':'nonzero exact rational sum','sum':str(z)}
 # Only rational/Gamma recurrence algebra is expanded; no numerical equals heuristic.
 z=s.factor_terms(s.expand_func(z))
 if z==0:return True,{'method':'exact Gamma recurrence/algebra cancellation','sum':'0'}
 iv=enclose(z)
 if iv[0]>0 or iv[1]<0:return False,{'method':'outward-rational enclosure excludes zero','expression':s.srepr(z),'enclosure':dump(iv)}
 q=s.simplify(z)
 if q==0:return True,{'method':'exact symbolic simplification','sum':'0'}
 raise ValueError('Unresolved pair sum '+str(z)+' '+str(iv))
def pair(a,b):
 if isinstance(a,s.Tuple)or isinstance(b,s.Tuple):
  assert isinstance(a,s.Tuple)and isinstance(b,s.Tuple)and len(a)==len(b)
  checks=[scalar_sum(x,y)for x,y in zip(a,b)]
  return all(p for p,_ in checks),{'method':'componentwise additive inverse of the complete ordered tuple','coordinates':[q for _,q in checks]}
 return scalar_sum(a,b)
def audit(r):
 f=r['familyId'];opts=r['choices'];base={'problemId':r['problemId'],'familyId':f,'optionInputSHA256':H(r),'answerChoiceId':r['answerChoiceId'],'literalChoices':[{'choiceId':c['choiceId'],'math':c['math']}for c in opts]}
 if f in CATEGORICAL:
  assert all(r'\textnormal' in c['math']for c in opts)and len({c['math']for c in opts})==4
  return base|{'status':'not-applicable-categorical','reason':CATEGORICAL[f],'oppositePairs':[],'mathematicalPairCount':None,'scope':'No arithmetic sign or magnitude prediction is defined for these literal labels; their ordinary formatting flags are reviewed separately.'}
 values=[parse(c['math'])for c in opts];certs=[];pairs=[]
 for i,j in itertools.combinations(range(4),2):
  opposite,certificate=pair(values[i],values[j]);certs.append({'indices':[i,j],'choiceIds':[opts[i]['choiceId'],opts[j]['choiceId']],'areOpposites':opposite,**certificate})
  if opposite:pairs.append([i,j])
 correct=next(i for i,c in enumerate(opts)if c['choiceId']==r['answerChoiceId'])
 return base|{'status':'complete-exact-mathematical-pair-review','decodedValues':[s.srepr(v)for v in values],'oppositePairs':pairs,'mathematicalPairCount':len(pairs),'pairedCorrect':any(correct in p for p in pairs),'pairCertificates':certs}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=BASE/'effective705-input.jsonl');ap.add_argument('--output',type=Path,default=BASE/'mathematical-pairs-before.json');args=ap.parse_args();rs=list(map(json.loads,args.input.read_text().splitlines()));out=[];errors=[]
 for r in rs:
  try:out.append(audit(r))
  except Exception as e:errors.append({'problemId':r['problemId'],'familyId':r['familyId'],'error':type(e).__name__+': '+str(e)})
 d={'inputSHA256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'records':len(rs),'statusCounts':dict(collections.Counter(r['status']for r in out)),'singlePairs':[r['problemId']for r in out if r['mathematicalPairCount']==1],'errors':errors,'recordsEvidence':out,'limits':'This is an exact additive-inverse diagnostic for complete numeric choices. Categorical options are individually listed as not applicable, not labeled numerically cleared. Analytic function enclosure hypotheses and explicit series remainders are in the bound review code. This diagnostic alone does not validate every task answer or clear unrelated option clues.'}
 args.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in d.items()if k!='recordsEvidence'}))
if __name__=='__main__':main()
