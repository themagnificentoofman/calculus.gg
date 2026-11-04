"""Three additional exact-opposite repairs discovered by explicit sine parsing."""
from pathlib import Path
from functools import lru_cache
import json,hashlib,itertools,re
import sympy as s
from unsupported_scalar_parser import parse
P=Path(__file__).resolve().parent;FAMILY='m3-integration-easy-odd-even';VERSION='quality-integration-odd-even-sign-addendum-v1'
def H(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tex(v):return s.latex(v).replace(r'\log',r'\ln')
@lru_cache(None)
def inputs():
 rows=[json.loads(l) for l in(P/'addendum-inputs.jsonl').read_text().splitlines()]
 return {int(re.search(r'\\frac\{\\pi\}\{(\d+)\}',r['statement'])[1])-4:r for r in rows}
def catalog():return [{'familyId':FAMILY,'indices':sorted(inputs()),'newIndependentIdeas':0}]
def build(fid,index):
 if fid!=FAMILY or type(index)is not int or index not in inputs():raise ValueError('Outside finite3 source-bound addendum')
 old=inputs()[index];m=index+4;x=s.symbols('x',real=True);a=s.pi/m;A=2*s.sin(a);ordinal=sorted(inputs()).index(index);B=A*2 if ordinal%2==0 else A/2
 primitive=x**4/4+s.sin(x);evaluated=s.simplify(primitive.subs(x,a)-primitive.subs(x,-a));assert s.simplify(evaluated-A)==0
 original=parse(next(c['math']for c in old['choices']if c['choiceId']==old['answerChoiceId']));assert s.simplify(original-A)==0
 why='Apply the even-symmetry doubling factor twice' if ordinal%2==0 else 'Omit the even-symmetry doubling factor';values=[A,-A,B,-B];choices=[{'choiceId':'ch_'+H(s.srepr(v))[:16],'math':tex(v),'expression':s.srepr(v),'misconception':reason}for v,reason in zip(values,['correct','Reverse the symmetric cosine integral sign',why,why+' and reverse the final sign'])]
 parsed=[parse(c['math'])for c in choices];assert all(s.simplify(u-v).equals(0)is False for u,v in itertools.combinations(parsed,2));assert sum(s.simplify(u+v)==0 for u,v in itertools.combinations(parsed,2))==2
 display=json.loads((P/'addendum-presentations.json').read_text())[old['problemId']];assert display['sourceContentHash']==old['contentHash']and display['revision']==old['problemRevision']
 row={'familyId':FAMILY,'topic':'integration','difficulty':old['difficulty'],'instanceIndex':index,'parameters':{'denominator':m,'sourceInstance':old['parameters']['instance']},'finiteInstanceIndices':sorted(inputs()),'statement':display['statement'],'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':display['steps'],'assumptions':old['assumptions'],'pedagogy':old['pedagogy'],'constructorVersion':VERSION,'provenance':{'kind':'original','theoremReferenceURLs':old['provenance']['authoring'].get('theoremReferenceURLs',[])},'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':H(old),'rawConstructorHash':old['provenance']['authoring'].get('rawSha256')},'sourcePresentation':{'sha256':fh(P/'addendum-presentations.json'),'entryHash':H(display),'solutionQuality':display.get('solutionQuality')},'review':{'status':'candidate-awaiting-independent-peer-and-final-id-options','newIndependentIdeas':0,'meaningChanged':False,'preservePreviousLineage':True,'easiestOptionsVisibleRoute':'Cancel the odd cubic, then double the cosine integral over the positive half interval.','optionRepairReason':'An exact sine opposite pair was outside the initial parser. Two competing sine magnitudes remove the singleton pair.','analyticConditions':'For the displayed positive integer m,0<pi/m<pi, so sin(pi/m)>0. Continuous integrands permit the elementary primitive and symmetry identities.'},'verificationEvidence':[{'description':'Derivative of the displayed polynomial-trigonometric primitive','left':s.srepr(s.diff(primitive,x)),'right':s.srepr(x**3+s.cos(x)),'result':'exact equality'},{'description':'Two primitive endpoint values','left':s.srepr(evaluated),'right':s.srepr(A),'result':'exact equality'},{'description':'Original literal answer equality','left':s.srepr(original),'right':s.srepr(A),'result':'exact equality'}],'analyticCertificate':old['validation']['evidence'].get('analyticCertificate',[])}
 base={r['problemId']:r for r in map(json.loads,(P/'addendum-baseline-inputs.jsonl').read_text().splitlines())};b=base.get(old['problemId'])
 if b:row['previous']={'problemId':b['problemId'],'revision':b['problemRevision'],'sourceContentHash':b['contentHash'],'semanticHash':b['semanticHash'],'meaningChanged':False}
 else:row['replacesPrivateProblemId']=old['problemId']
 row['contentHash']=H(row);return row

def verify(row):
 try:return row==build(row['familyId'],row['instanceIndex'])
 except Exception:return False
if __name__=='__main__':
 rows=[build(FAMILY,i)for i in inputs()];(P/'addendum-candidates.jsonl').write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n'for r in rows));print({'records':len(rows),'exactChecks':9,'literalPairs':18})
