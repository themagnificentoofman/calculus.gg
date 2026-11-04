"""Three finite literal ground-state distractor repairs, with exact source joins."""
from pathlib import Path
import copy,json,hashlib,re,itertools
import sympy as s
from differentiation_literal_choices import parse
P=Path(__file__).resolve().parent
FAMILY='m3-differential-equations-olympiad-ground-state-variance'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def lines(p):return [json.loads(x)for x in p.read_text().splitlines()]
SOURCES={r['parameters']['instance']:r for r in lines(P/'source-records.jsonl')};SERVED={r['parameters']['instance']:r for r in lines(P/'served-sources.jsonl')};MAPS={r['sourceIndex']:r for r in json.load(open(P/'source-map.json'))};PROPOSALS={r['sourceIndex']:r for r in json.load(open(P/'repair-proposals.json'))}
def build(family,index):
 if family!=FAMILY or type(index)is not int or index not in[1,3,5]:raise ValueError('Outside frozen finite domain')
 old=SOURCES[index];visible=SERVED[index];m=MAPS[index];p=PROPOSALS[index];assert old['problemId']==visible['problemId']==m['problemId']==p['sourceProblemId']
 raw={k:copy.deepcopy(visible[k])for k in['familyId','topic','statement','assumptions','pedagogy','choices','answerChoiceId','solutionSteps']}
 c=next(c for c in raw['choices']if c['choiceId']==p['replaceChoiceId']);assert c['math']==p['oldMath']
 c['math']=p['proposedMath'];c['choiceId']='ch_'+digest([FAMILY,index,'wrong-frequency',c['math']])[:16];c['misconception']=p['misconception'];c['namedRoute']='potential-coefficient-as-variance'
 for choice in raw['choices']:
  if choice.get('misconception')=='confuse the second moment with its doubled value':
   choice['misconception']='Double the amplitude-Gaussian variance1/a instead of taking the squared-amplitude variance1/(2a); the resulting2/a is four times the correct moment.'
 raw.update({'constructorVersion':'ground-state-coefficient-variance-options-v3','instanceIndex':index,'finiteInstanceIndices':[1,3,5],
  'parameters':copy.deepcopy(old['parameters']),'difficulty':old['difficulty'],'revisesProblemId':old['problemId'],'sourceContentHash':old['contentHash'],
  'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':digest(old),'servedRawHash':digest(visible)},
  'provenance':{'kind':'original','theoremReferenceURLs':old.get('provenance',{}).get('authoring',{}).get('theoremReferenceURLs',[])},
  'review':{'meaningChanged':False,'newIndependentIdeas':0,'qualifiedOlympiad':True,'recommendedDifficulty':'olympiad','easiestOptionsVisibleRoute':'Multiply the eigen-equation by y and integrate, then complete the nonnegative square integral(y′+a t y)². Schwartz decay removes the boundary terms. Equality identifies the minimizing Gaussian, and an integration-by-parts identity gives its normalized second moment1/(2a).',
   'difficultyRationale':'The task asks for the smallest admissible eigenvalue, not merely any Gaussian-shaped eigenfunction. A direct ansatz suggests the answer but does not justify minimality. The completion-square lower bound with its equality case is a nonroutine strategic step, followed by normalization of a moment. The new all-positive wrong-frequency value survives mere sign selection. Prior independent Olympiad classification is retained provisionally for peer review, not restored by repair or by conservative labeling.',
   'optionsVisibleElimination':'Positivity excludes no displayed value. Reciprocal-frequency scaling can reject a growing-frequency error and the new coefficient-as-variance error, but leaves the correct1/(2a) and2/a. Determining the factor requires identifying the minimizing eigenfunction and the squared amplitude moment.',
   'relatedIdeaGroupId':m['relatedIdeaGroupId'],'normalizedLineageKey':m['normalizedTaskKey'],'preserveNormalizedLineage':True,'status':'pending-independent-peer-and-final-catalog-rebind'},
  'presentationRule':'Preserve exact active statement, answer, and all worked steps. Replace one wrong scalar choice by the actual variance from the wrong-frequency misconception.'})
 raw['contentHash']=digest(raw);return raw

def verify(raw):
 i=raw['instanceIndex'];assert canonical(raw)==canonical(build(FAMILY,i));old=SOURCES[i];visible=SERVED[i];a=s.Integer(i+4);t=s.symbols('t',real=True)
 for k in['statement','answerChoiceId','solutionSteps']:assert raw[k]==visible[k]
 assert raw['statement'].find(str(a*a)+'t^2')>=0
 y=s.exp(-a*t*t/2);assert s.simplify(-s.diff(y,t,2)+a*a*t*t*y-a*y)==0
 Y=s.Function('y')(t);identity=s.diff(Y,t)**2+a*a*t*t*Y**2-(s.diff(Y,t)+a*t*Y)**2+a*s.diff(t*Y**2,t)-a*Y**2;assert s.simplify(identity)==0
 assert s.simplify(s.diff(t*s.exp(-a*t*t),t)-(1-2*a*t*t)*s.exp(-a*t*t))==0
 values=[parse(c['math'])for c in raw['choices']];assert len(set(values))==4 and all(v.is_Rational and v>0 for v in values)
 answer=values[next(j for j,c in enumerate(raw['choices'])if c['choiceId']==raw['answerChoiceId'])];assert answer==s.Rational(1,2*a)
 new=next(c for c in raw['choices']if c.get('namedRoute')=='potential-coefficient-as-variance');assert parse(new['math'])==s.Rational(a*a,2)
 pairs=[{'choiceIds':[raw['choices'][j]['choiceId'],raw['choices'][k]['choiceId']],'exactDifference':str(values[j]-values[k]),'exactSum':str(values[j]+values[k])}for j,k in itertools.combinations(range(4),2)]
 lengths=[len(re.sub(r'\s','',c['math']))for c in raw['choices']];correctlength=lengths[next(j for j,c in enumerate(raw['choices'])if c['choiceId']==raw['answerChoiceId'])];assert not(correctlength==max(lengths)and lengths.count(correctlength)==1)
 return {'rawSha256':digest(raw),'sourceProblemId':old['problemId'],'sourceCanonicalRawHash':digest(old),'sourceContentHash':old['contentHash'],'sourceRevision':old['problemRevision'],'index':i,'frequency':str(a),'exactAnswer':str(answer),'wrongCoefficientVariance':new['math'],'literalPairCertificates':pairs,'answerNoLongerUniqueLongest':True,'recommendedDifficulty':'olympiad','qualifiedOlympiad':True,'analyticJustification':'All derivatives are Schwartz by the statement, so boundary terms and Gaussian moments converge. The exact completed-square identity proves lambda>=a for every admissible nonzero solution, and the displayed Gaussian attains equality. The derivative of t exp(-a t²) gives the moment ratio without a memorized normalization constant.','passed':True}
if __name__=='__main__':
 rows=[build(FAMILY,i)for i in[1,3,5]];reviews=[verify(r)for r in rows]
 (P/'candidates.jsonl').write_text(''.join(canonical(r)+'\n'for r in rows));(P/'finite-review.json').write_text(json.dumps({'records':reviews,'counts':{'records':3,'retainedPublicRevisions':3,'pairDistinctions':18,'oppositeSumChecks':18},'scope':'Author exact finite repair review with independent classification rationale; root independent peer remains required.'},indent=2)+'\n');print(json.dumps({'records':3,'indices':[1,3,5]}))
