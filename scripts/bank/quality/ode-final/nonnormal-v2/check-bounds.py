from pathlib import Path
import json
import repairs as r
import sympy as s
rows=[]
for i in range(10):
 raw=r.build(r.FAMILY,i);K,*_=r.data(r.sources()[i]);L=s.sqrt(1+K*K)/s.E;U=K*s.exp(-1+1/K)
 cs=[]
 for c in raw['choices']:
  v=s.sympify(c['expression']);low=r.sign_certificate(v-L);high=r.sign_certificate(U-v)
  cs.append({'choiceId':c['choiceId'],'namedRoute':c['namedRoute'],'lowerDifference':low,'upperDifference':high,'survivesBounds':low['sign']==1 and high['sign']==1})
 survivors=[c['choiceId']for c in cs if c['survivesBounds']];assert raw['answerChoiceId']in survivors
 if i not in[2,5,8]:assert len(survivors)>=2 and any(c['namedRoute']=='decay-time-one' and c['survivesBounds']for c in cs)
 rows.append({'index':i,'rawSha256':r.digest(raw),'sourceProblemId':raw['sourcePreview']['problemId'],'lowerBound':str(L),'upperBound':str(U),'choices':cs,'survivingChoices':survivors,'boundAloneDecides':len(survivors)==1})
Path(__file__).with_name('visible-bound-review.json').write_text(json.dumps({'scope':'Outward rational sign certificates for literal values versus the root-discovered t=1 column lower bound and triangle-norm upper bound. This does not prove absence of other shortcuts.','records':rows},indent=2)+'\n')
print(json.dumps({'survivors':[len(x['survivingChoices'])for x in rows]}))
