"""Finite classification-only amendment; frozen literal choices and served presentation."""
from pathlib import Path
import copy,json,hashlib,re
import sympy as s
from differentiation_literal_choices import parse
P=Path(__file__).resolve().parent
FAMILY='m3-multivariable-medium-density-centroid'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def lines(p):return [json.loads(x)for x in p.read_text().splitlines()]
SOURCES=lines(P/'source-records.jsonl');SERVED=lines(P/'served-sources.jsonl');MAPS=json.load(open(P/'source-map.json'))
def build(family,index):
 if family!=FAMILY or type(index)is not int or not 0<=index<10:raise ValueError('Outside frozen finite domain')
 old=SOURCES[index];visible=SERVED[index];m=MAPS[index];assert old['problemId']==visible['problemId']==m['problemId']
 raw={k:copy.deepcopy(visible[k])for k in ['familyId','topic','statement','assumptions','pedagogy','choices','answerChoiceId','solutionSteps']}
 raw.update({'constructorVersion':'density-centroid-easy-ceiling-v1','instanceIndex':index,'finiteInstanceIndices':list(range(10)),
  'parameters':{'instance':index,'sourceInstance':old['parameters']['instance'],'sourceProblemId':old['problemId']},'difficulty':'easy',
  'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':digest(old),'servedRawHash':digest(visible)},
  'provenance':{'kind':'original','theoremReferenceURLs':old.get('provenance',{}).get('authoring',{}).get('theoremReferenceURLs',[])},
  'review':{'meaningChanged':False,'newIndependentIdeas':0,'qualifiedOlympiad':False,'recommendedDifficulty':'easy','easiestOptionsVisibleRoute':'The positive density x^n increases on the unit interval, so its x-centroid lies strictly between1/2 and1. Exactly one displayed choice lies in this interval.',
   'difficultyRationale':'A qualitative increasing-density check uniquely selects the answer; no ratio of integrals or multiple-stage computation is needed with these options. Classify the current menus Easy without inventing new distractors.',
   'relatedIdeaGroupId':m['relatedIdeaGroupId'],'normalizedLineageKey':m['normalizedTaskKey'],'preserveNormalizedLineage':True,'status':'pending-independent-peer-and-final-catalog-rebind'},
  'presentationRule':'Preserve the exact active served statement, literal choices, answer choice ID, and solution steps; change difficulty only.'})
 if m.get('finalReviewId'):raw['replacesPrivateProblemId']=old['problemId']
 else:raw['revisesProblemId']=old['problemId'];raw['sourceContentHash']=old['contentHash']
 raw['contentHash']=digest(raw);return raw

def verify(raw):
 index=raw['instanceIndex'];assert canonical(raw)==canonical(build(FAMILY,index));old=SOURCES[index];visible=SERVED[index]
 for k in['statement','choices','answerChoiceId','solutionSteps']:assert raw[k]==visible[k]
 n=int(re.search(r'rho\(x,y\)=x\^\{(\d+)\}',raw['statement']).group(1));assert n>0
 values=[parse(c['math'])for c in raw['choices']];assert len(set(values))==4 and all(v.is_Rational for v in values)
 candidates=[c['choiceId']for c,v in zip(raw['choices'],values)if s.Rational(1,2)<v<1]
 assert candidates==[raw['answerChoiceId']]
 correct=values[next(i for i,c in enumerate(raw['choices'])if c['choiceId']==raw['answerChoiceId'])];assert correct==s.Rational(n+1,n+2)
 pairs=[{'choiceIds':[raw['choices'][i]['choiceId'],raw['choices'][j]['choiceId']],'exactDifference':str(values[i]-values[j])}for i in range(4)for j in range(i+1,4)]
 return {'rawSha256':digest(raw),'sourceProblemId':old['problemId'],'sourceCanonicalRawHash':digest(old),'sourceContentHash':old['contentHash'],'sourceRevision':old['problemRevision'],'exponent':n,'uniqueIntervalChoiceId':candidates[0],'literalValues':[str(v)for v in values],'exactAnswer':str(correct),'literalPairCertificates':pairs,'recommendedDifficulty':'easy','qualifiedOlympiad':False,'passed':True}
if __name__=='__main__':
 rows=[build(FAMILY,i)for i in range(10)];reviews=[verify(r)for r in rows]
 (P/'candidates.jsonl').write_text(''.join(canonical(r)+'\n'for r in rows));(P/'finite-review.json').write_text(json.dumps({'proof':'For positive increasing w(x)=x^n, pair x and1−x in the first centered moment: integral_(1/2)^1 (x−1/2)[w(x)−w(1−x)]dx>0. Hence mean>1/2; positive density inside(0,1) gives mean<1. Direct integration independently gives(n+1)/(n+2).','records':reviews,'counts':{'records':10,'retainedPublicRevisions':8,'privateReplacements':2,'uniqueQualitativeSelections':10,'pairDistinctions':60},'scope':'Classification-only author finite review; independent confirmation remains required.'},indent=2)+'\n');print(json.dumps({'records':10,'exponents':[r['exponent']for r in reviews]}))
