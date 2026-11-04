"""Two additional concrete fluency cases per existing lower integration family.

This is an explicitly new finite verification domain, not a mutation or
re-attestation of the frozen M3 constructor. No new independent ideas claimed.
The separately written solution verifier rechecks intermediate identities.
"""
from . import support as c,solutions
import hashlib,json,re

VERSION='quality-integration-extensions-v1'

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def catalog():
 return [{k:v for k,v in f.items() if k!='build'}|{'indices':[0,1],'finiteParameters':[{'m':12},{'m':13}],
   'constructionFamilyId':fid,'newIndependentIdeas':0,'reviewStatus':'candidate-awaiting-independent-review'}
  for fid,f in sorted(c.FAMILIES.items()) if f['topic']=='integration' and f['difficulty']!='olympiad']

def build(family,index):
 if type(index)is not int or index not in [0,1]:raise ValueError('Outside independently checked extension domain')
 f=c.FAMILIES[family]
 if f['topic']!='integration' or f['difficulty']=='olympiad':raise ValueError('Unsupported extension')
 m=12+index;raw=c.source_payload(family,m);options,audit=c.frozen.select_options(raw['options'],m)
 choices=[{'choiceId':'ch_'+hashlib.sha256(canonical(c.s.srepr(value)).encode()).hexdigest()[:16],
   'math':c.frozen.latex(value),'misconception':why} for value,why in options]
 context={'familyId':family,'parameters':{'instance':m-4},'provenance':{'authoring':{'builderParameters':{'m':m}}},'choices':choices,'answerChoiceId':choices[0]['choiceId']}
 independent=solutions.solve(context)
 assert independent['checks'] and all(check['result']=='exact equality' for check in independent['checks'])
 # Source expressions and wrong answers are independently pairwise checked,
 # rather than trusting distinct strings or the constructor's answer index.
 for i,(left,_) in enumerate(options):
  for right,_ in options[i+1:]:assert not c.eq(left,right)
 statement=raw['statement']
 if re.search(r'(?<![A-Za-z\\])m(?![A-Za-z])',statement):statement=r'm='+str(m)+r',\quad '+statement
 return {'familyId':family,'topic':'integration','difficulty':f['difficulty'],'parameters':{'extension':index,'m':m},
  'parameterDomain':{'m':[12,13]},'statement':statement,'choices':choices,'answerChoiceId':choices[0]['choiceId'],
  'solutionSteps':independent['solutionSteps'],'assumptions':[re.sub(r'\bm\b',str(m),v) for v in raw.get('domain',[])],
  'pedagogy':{'constructionId':family,'relatedIdeaGroupId':f['relatedIdeaGroupId'],'structuralSignature':raw['structuralSignature'],
   'primaryTechnique':f['primaryTechnique'],'alternativeTechniques':f['alternativeTechniques'],'prerequisites':f['prerequisites'],
   'reasoningDemand':[f['reasoningDemand']],'answerForm':'exact-expression','difficultyRationale':f['difficultyRationale'],
   'sourceRecordIds':[],'responseFormat':'multiple-choice'},'verificationEvidence':independent['checks'],
  'optionAudit':audit,'verificationRoute':VERSION,'newIndependentIdeas':0,'constructorVersion':VERSION,
  'reviewStatus':'candidate-awaiting-independent-review','finiteParameters':[{'m':12},{'m':13}]}

def verify(record):
 expected=build(record['familyId'],record['parameters']['extension'])
 if canonical(record)!=canonical(expected):raise ValueError('Extension source reconstruction mismatch')
 return True

def all_candidates():
 for family in catalog():
  for index in family['indices']:yield build(family['familyId'],index)

if __name__=='__main__':
 import sys
 rows=list(all_candidates());assert len(rows)==68
 with open(sys.argv[1],'w') as out:
  for row in rows:out.write(canonical(row)+'\n')
 print(canonical({'items':len(rows),'newIndependentIdeas':0,'exactChecks':sum(len(r['verificationEvidence']) for r in rows)}))
