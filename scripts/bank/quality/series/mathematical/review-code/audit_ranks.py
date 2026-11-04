"""Supplemental mathematical ranks, using literal values and exact enclosures."""
from pathlib import Path
import json,collections,itertools,hashlib,argparse
import sympy as s
from literal_math import parse
from audit_pairs import scalar_sum,canonical
from atan_certificate import normalized_tangent
from enclosures import enclose
BASE=Path(__file__).resolve().parent
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=BASE/'effective705-proposed.jsonl');ap.add_argument('--output',type=Path,default=BASE/'mathematical-ranks-proposed.json');args=ap.parse_args();source=args.input;rs=list(map(json.loads,source.read_text().splitlines()));out=[];errors=[]
 for r in rs:
  try:
   if any('\\textnormal' in c['math']for c in r['choices']):continue
   vals=[parse(c['math'])for c in r['choices']]
   if any(isinstance(v,s.Tuple)for v in vals):continue
   ranks=[1]*4;checks=[]
   for i,j in itertools.combinations(range(4),2):
    if r['familyId'].endswith('telescoping-arctan'):
     u,uc=normalized_tangent(vals[i]);v,vc=normalized_tangent(vals[j]);assert u!=v,('equivalent choices',r['problemId'],i,j);greater=u>v;cert={'method':'principal arctangent injectivity and exact rational tangent ordering','left':uc,'right':vc}
    else:
     diff=s.expand(vals[i]-vals[j]);cs=list(diff.atoms(s.coth));ts=list(diff.atoms(s.tanh))
     if len(cs)==len(ts)==1 and cs[0].args==ts[0].args and cs[0].args[0]>0 and s.simplify(diff-diff.coeff(cs[0])*(cs[0]-ts[0]))==0:
      coeff=diff.coeff(cs[0]);iv=enclose(coeff);assert iv[0]>0 or iv[1]<0;greater=iv[0]>0;cert={'method':'exact hyperbolic difference identity','identity':'coth(u)−tanh(u)=1/(sinh(u)cosh(u))>0 for u>0','u':str(cs[0].args[0]),'coefficient':str(coeff),'coefficientEnclosure':[str(x)for x in iv]}
     else:
      eq,cert=scalar_sum(vals[i],-vals[j]);assert not eq,('equivalent choices',r['problemId'],i,j)
      if diff==s.oo:greater=True
      elif diff==-s.oo:greater=False
      elif diff.is_Rational:greater=diff>0
      else:greater=s.Rational(cert['enclosure'][0])>0
    if greater:ranks[i]+=1
    else:ranks[j]+=1
    checks.append({'indices':[i,j],**cert})
   correct=next(i for i,c in enumerate(r['choices'])if c['choiceId']==r['answerChoiceId'])
   out.append({'problemId':r['problemId'],'familyId':r['familyId'],'correctRank':ranks[correct],'choiceRanks':ranks,'pairwiseInequalityCertificates':checks})
  except Exception as e:errors.append({'problemId':r['problemId'],'familyId':r['familyId'],'error':type(e).__name__+': '+str(e)})
 families={}
 for f in sorted({r['familyId']for r in out}):
  sub=[r for r in out if r['familyId']==f];counts=collections.Counter(r['correctRank']for r in sub);families[f]={'records':len(sub),'correctRanks':dict(counts),'middleTwoExpectedTieBrokenAccuracy':sum(r['correctRank']in [2,3]for r in sub)/(2*len(sub)),'extremeTwoExpectedTieBrokenAccuracy':sum(r['correctRank']in [1,4]for r in sub)/(2*len(sub)),'alwaysMiddle':all(r['correctRank']in [2,3]for r in sub),'alwaysExtreme':all(r['correctRank']in [1,4]for r in sub),'missingRanks':[i for i in range(1,5)if i not in counts]}
 result={'inputSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'records':len(out),'errors':errors,'families':families,'recordsEvidence':out,'limits':'Only scalar numerical answers are ordered. Categorical and tuple answers are not assigned an arbitrary scalar rank. A missing rank or a small finite aggregate is a diagnostic, not on its own proof of a usable shortcut; perfect unions are escalated explicitly.'}
 args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'records':len(out),'errors':errors,'perfectMiddleFamilies':[(f,x)for f,x in families.items()if x['records']>=8 and x['alwaysMiddle']],'perfectExtremeFamilies':[(f,x)for f,x in families.items()if x['records']>=8 and x['alwaysExtreme']]}))
