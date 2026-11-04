"""Exact155-record reuse plus independent eight-menu Gauss verification."""
from pathlib import Path
import argparse,copy,hashlib,itertools,json,math,collections
import sympy as s
import verify_limits as independent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return independent.digest(r)
def strip(r,gauss=False):
 r=copy.deepcopy(r);v=r['validation']['evidence'];v.pop('sourceHash',None);v.pop('pairwiseOptionChecks',None)
 if gauss:r.pop('choices');v.pop('checks',None)
 return r

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prior-stage',type=Path,required=True);ap.add_argument('--stage',type=Path,required=True);ap.add_argument('--prior-review-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 source=a.stage/'candidates.json';oldsrc={(r['familyId'],r['parameters']['instance']):r for r in json.loads((a.prior_stage/'candidates.json').read_text())};newsrc={(r['familyId'],r['parameters']['instance']):r for r in json.loads(source.read_text())};review=json.loads((a.prior_review_dir/'all-finite-review.json').read_text());joins=[];gauss=[]
 for record in review['records']:
  key=record['familyId'],record['instanceIndex'];old,new=oldsrc[key],newsrc[key];is_gauss=key[0].endswith('quadratic-gauss-magnitude');assert record['rawSHA256']==H(old);assert strip(old,is_gauss)==strip(new,is_gauss),key
  prior_hash=record['rawSHA256'];record['rawSHA256']=H(new);record['authorSourceHash']=new['validation']['evidence']['sourceHash'];record['evidenceReuseSourceRawSHA256']=prior_hash
  join={'familyId':key[0],'instanceIndex':key[1],'priorRawSHA256':prior_hash,'destinationRawSHA256':H(new),'statementsAnswersSolutionsParametersLevelsLineageEqual':True,'choicesEqual':old['choices']==new['choices'],'authorMetadataDifferencesOnly':not is_gauss}
  if is_gauss:
   answer,checks,norm,aliases,level,reason,notes=independent.expected_and_checks(new)
   # These literal menus are nonnegative integers; no author expression parser is required.
   values=[]
   for choice in new['choices']:
    assert choice['math'].isdigit();value=s.Integer(choice['math']);values.append(value)
    assert str(value)==choice['math'];checks.append(independent.yes('Literal nonnegative integer choice parsed independently',True))
   selected=next(v for c,v in zip(new['choices'],values)if c['choiceId']==new['answerChoiceId']);checks.append(independent.eq('New selected literal integer matches independent character calculation',selected,answer));assert s.srepr(answer)==record['independentAnswer'] and norm==record['normalizedTaskKey']
   pairs=[{'method':'exact nonzero integer difference','left':str(x),'right':str(y),'difference':str(x-y),'passed':True}for x,y in itertools.combinations(values,2)];assert all(x!=y for x,y in itertools.combinations(values,2));assert not any(x+y==0 for x,y in itertools.combinations(values,2))
   aa,bb=new['parameters']['case']['a'],new['parameters']['case']['b'];g=[math.gcd(aa,4*aa+r)for r in range(4)]
   def route(r,parity=False,unit=False,truncate=False):
    d=g[r]
    if bb%d and not truncate:return 0
    M=(4*aa+r)//d;A=aa//d;B=bb//d
    interference=1 if M%2 else(2 if parity else 1+(-1)**(A*(M//2)+B))
    return interference*(1 if unit else d)
   terms=[route(r)for r in range(4)];assert sum(terms)==answer
   models={'correct':answer,'Ignore the divisibility obstruction of the linear coefficient':sum(route(r,truncate=True)for r in range(4)),'Reinforce every surviving even-modulus character':sum(route(r,parity=True)for r in range(4)),'Forget the gcd multiplicity after reducing the period':sum(route(r,unit=True)for r in range(4)),'Omit the modulus divisible by the full fourfold leading coefficient':sum(terms[1:]),'Use the odd-modulus value in every class':sum(g),'Count both index differences twice':2*answer,'Halve the squared-modulus normalization':answer/2,'Square the period count without dividing by the original modulus':sum(x*x for x in g),'Square the total period count after summing congruence classes instead of summing their normalized squares':sum(g)**2,'Retain only the congruence class divisible by the full fourfold leading coefficient':terms[0],'Retain only the primitive odd congruence class':terms[1]}
   error_routes=[]
   for c,v in zip(new['choices'],values):
    assert models[c['misconception']]==v
    error_routes.append({'choiceId':c['choiceId'],'literalInteger':str(v),'authoredError':c['misconception'],'independentlyRecomputed':True,'qualification':'When divisibility is ignored, the erroneous model also truncates the reduced noninteger linear coefficient; the correct proof performs division only after checking divisibility.'if c['misconception'].startswith('Ignore the divisibility')else None})
   upper=sum(math.gcd(2*aa,4*aa+r)for r in range(4));survivors=[c['choiceId']for c,v in zip(new['choices'],values)if 0<=v<=upper];assert len(survivors)>=2
   square=lambda x:x>=0 and math.isqrt(int(x))**2==x
   squarechoices=[c['choiceId']for c,v in zip(new['choices'],values)if square(v)]
   if square(answer):assert len(squarechoices)>=2
   record['executedChecks']=checks;record['pairwiseChoiceCertificates']=pairs;record['selectedChoiceId']=new['answerChoiceId'];record['optionNumericDiagnostics']=list(map(int,values));record['optionBoundReview']={'method':'Character orthogonality leaves at most gcd(2a,m) unit phases per normalized squared magnitude; sum the four gcd bounds.','necessaryInterval':[0,upper],'survivingChoiceIds':survivors}
   record['stage14OptionReview']={'misconceptionRoutes':error_routes,'competingSquareChoiceIds':squarechoices,'mathematicalOppositePairs':[],'scope':'Only the literal options and author metadata changed. The reviewed all-n parity/gcd argument and public solution are identical.'}
   gauss.append({'familyId':key[0],'instanceIndex':key[1],'rawSHA256':H(new),'independentAnswer':str(answer),'normalizedTaskKey':norm,'correctChoiceId':new['answerChoiceId'],'pairwiseChoiceCertificates':pairs,'misconceptionRoutes':error_routes,'coarseBound':record['optionBoundReview'],'squareChoiceIds':squarechoices,'passed':True})
  joins.append(join)
 assert len(joins)==163 and len(gauss)==8
 review['candidateArtifact']=str(source.resolve());review['candidateArtifactSHA256']=sha(source);review['authorSourcesSHA256']={p.name:sha(p)for p in a.stage.glob('*.py')};review['reviewSourcesSHA256']={p.name:sha(p)for p in Path(__file__).parent.glob('*.py')};review['counts']['exactOrDomainChecks']=sum(len(r['executedChecks'])for r in review['records']);review['counts']['pairwiseChoiceCertificates']=sum(len(r['pairwiseChoiceCertificates'])for r in review['records']);review['evidenceReuse']={'priorReviewSHA256':sha(a.prior_review_dir/'all-finite-review.json'),'priorArtifactSHA256':sha(a.prior_stage/'candidates.json'),'bindingCodeSHA256':sha(Path(__file__)),'unchangedMathematicsAndChoicesReused':155,'GaussChoicesReverified':8,'scope':'155 records are exactly unchanged except two author evidence fields. Eight Gauss records preserve statements, solutions, exact answers, levels, finite parameters and lineage; new literal integer options and misconception formulas are independently rechecked, including48 nonzero pair differences and the nonunique elementary bound.','records':joins}
 (a.out/'all-finite-review.json').write_text(json.dumps(review,indent=2)+'\n');(a.out/'gauss-stage14-option-review.json').write_text(json.dumps({'sourceSHA256':sha(source),'records':gauss,'scope':'No author constructors or answer functions imported. Prior independent character-orthogonality checker executed again on all8, plus literal integer options and mistake routes. Analytic all-n hypotheses remain the unchanged prior review.'},indent=2)+'\n');(a.out/'source-rebinding.json').write_text(json.dumps(review['evidenceReuse'],indent=2)+'\n')
 print(json.dumps({'records':len(joins),'reusedUnchanged':155,'newGaussMenus':8,'newIntegerPairCertificates':48,'candidateSHA256':sha(source)}))
if __name__=='__main__':main()
