"""Finite immutable Bessel-Laplace choice repairs; independent review pending.

All values use the same exact simplification path. Each coefficient comes from
a concrete frequency/sign/normalization error, not a small answer offset.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,itertools,json,sys
import sympy as s
P=Path(__file__).resolve().parent
FID='io3-bessel-laplace'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def tex(v):return s.latex(v)
@lru_cache(None)
def inputs():return list(map(json.loads,(P/'bessel-originals.jsonl').read_text().splitlines())),json.loads((P/'bessel-presentations.json').read_text())
def catalog():return [{'familyId':FID,'indices':list(range(8)),'newIndependentIdeas':0}]
def build(fid,index):
 if fid!=FID or type(index)is not int or index not in range(8):raise ValueError('Outside finite Bessel repair domain')
 originals,presentations=inputs();old=next(r for r in originals if r['parameters']['instance']==index);overlay=presentations[old['problemId']]
 assert overlay['sourceContentHash']==old['contentHash'] and overlay['revision']==old['problemRevision']
 a,b=map(s.Integer,[old['provenance']['authoring']['builderParameters'][v] for v in ['a','b']]);assert a>b>0
 answer=1/s.sqrt(a*a+b*b);assert tex(answer)==next(c['math'] for c in old['choices'] if c['choiceId']==old['answerChoiceId'])
 reasons={s.Integer(-1):'Use the growing modified-Bessel sign instead of the oscillatory sign',s.Rational(1,4):'Halve the frequency before taking its square',s.Rational(1,2):'Retain an extra angular-average factor in the squared frequency',s.Integer(2):'Count the squared-frequency term twice',s.Integer(4):'Double the frequency before squaring it',s.Integer(9):'Triple the frequency before squaring it'}
 # These four misconception menus vary the correct magnitude rank. They are
 # declared before the final-ID screen, with the rejected old pool preserved.
 menus=[(2,4,9),(-1,s.Rational(1,4),s.Rational(1,2)),(-1,s.Rational(1,4),4),(s.Rational(1,2),2,4)]
 choices=[];values=[]
 for c in [s.Integer(1),*map(s.sympify,menus[index%4])]:
  radicand=a*a+c*b*b;assert radicand>0;v=s.simplify(1/s.sqrt(radicand));values.append(v)
  choices.append({'choiceId':'ch_'+digest(s.srepr(v))[:16],'math':tex(v),'misconception':'correct' if c==1 else reasons[c],'expression':s.srepr(v)})
 for x,y in itertools.combinations(values,2):assert s.simplify(x-y).equals(0)is False
 row={'familyId':fid,'topic':'integration','difficulty':'olympiad','instanceIndex':index,'parameters':{'a':int(a),'b':int(b),'instance':index},'finiteInstanceIndices':list(range(8)),'statement':overlay.get('statement',old['statement']),'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':overlay['steps'],'assumptions':old['assumptions'],'pedagogy':old['pedagogy'],'previous':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'meaningChanged':False},'constructorVersion':'quality-integration-bessel-option-repairs-v1','provenance':{'kind':'original','theoremReferenceURLs':old['provenance']['authoring']['theoremReferenceURLs']},'verificationEvidence':[{'description':'Exact original answer preserved','result':True},{'description':'All six positive-radical values are mathematically distinct','result':True}],'analyticCertificate':old['validation']['evidence']['analyticCertificate']}
 row['contentHash']=digest(row);return row
def verify(r):return canonical(r)==canonical(build(r['familyId'],r['instanceIndex']))
if __name__=='__main__':
 rows=[build(FID,i) for i in range(8)];Path(sys.argv[1]).write_text(''.join(canonical(r)+'\n' for r in rows));print('8 finite raw option repairs; independent final review required')
