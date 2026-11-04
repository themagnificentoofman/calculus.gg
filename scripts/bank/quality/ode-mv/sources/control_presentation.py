"""Immutable exact-field display normalization of ten frozen control records."""
from pathlib import Path
import json,hashlib,copy,itertools
import sympy as s
from literal_numeric import parse
P=Path(__file__).resolve().parent;FID='q4-differential-equations-oscillator-minimum-control-energy'
VERSION='quality-ode-control-display-v1'
def raw(r):return hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
ORIGINAL={r['instanceIndex']:r for r in map(json.loads,(P/'control-display-originals.jsonl').read_text().splitlines())}
def supports(r):return r.get('familyId')==FID and r.get('instanceIndex') in ORIGINAL and raw(r)==raw(ORIGINAL[r['instanceIndex']])
def normalized(v):
 z=s.Symbol('P');old=v.subs(s.pi,z);new=s.cancel(old,z,extension=[s.sqrt(2),s.sqrt(3)])
 assert s.cancel(old-new,z,extension=[s.sqrt(2),s.sqrt(3)])==0
 return s.factor_terms(new).subs(z,s.pi)
def build_revision(original):
 assert supports(original);r=copy.deepcopy(original);checks=[];values=[]
 for c in r['choices']:
  before=parse(c['math']);after=normalized(before);display=s.latex(after)
  assert s.cancel(parse(display)-before,extension=[s.sqrt(2),s.sqrt(3)])==0
  checks.append({'choiceId':c['choiceId'],'before':s.srepr(before),'after':s.srepr(after),'exactField':'Q(sqrt(2),sqrt(3))(P), with P restored to pi','result':'exact equality'})
  values.append(after);c['math']=display
 for a,b in itertools.combinations(values,2):assert s.simplify(a-b).equals(0)is False
 r['statement']=r['statement'].replace(r'x\prime\prime+1x=',r'x\prime\prime+x=')
 r['solutionSteps'][-1]=next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId'])
 r['constructorVersion']=VERSION;r['review'].update(previousCandidate={'problemId':original['problemId'],'contentHash':original['contentHash'],'semanticHash':original['semanticHash'],'rawHash':raw(original),'constructorVersion':original['constructorVersion']},meaningChanged=False,presentationOnly=True,sourceDisplayNormalization='All four options receive the same exact field cancellation and factor_terms convention; correct-value equality and all six pair inequalities checked. Final root literal-option review remains separate.')
 r['presentationVerification']=checks;r['contentHash']=raw({k:v for k,v in r.items() if k!='contentHash'})
 return r
def verify_revision(r,original):
 try:return supports(original) and r==build_revision(original)
 except Exception:return False
def catalog():return [{'familyId':FID,'indices':sorted(ORIGINAL),'finiteParameters':[ORIGINAL[i]['parameters'] for i in sorted(ORIGINAL)],'newIndependentIdeas':0}]
def build(fid,index):
 if fid!=FID or type(index)is not int or index not in ORIGINAL:raise ValueError('Outside frozen ten-record display domain')
 return build_revision(ORIGINAL[index])
def all_candidates():
 for i in sorted(ORIGINAL):yield build(FID,i)
def verify(r):
 try:return r==build(r['familyId'],r['instanceIndex'])
 except Exception:return False
if __name__=='__main__':
 rows=list(all_candidates());assert len(rows)==10
 (P/'control-display-candidates.jsonl').write_text(''.join(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n' for r in rows))
 report={'records':[{'problemId':r['problemId'],'instanceIndex':r['instanceIndex'],'rawHash':raw(r),'contentHash':r['contentHash'],'semanticHash':r['semanticHash'],'previous':r['review']['previousCandidate'],'exactChoiceEqualities':4,'exactPairInequalities':6,'statementChange':'Remove the unit coefficient in the oscillator equation.','solutionChange':'Use the normalized exact correct choice in the concluding equation.'} for r in rows],'sourceSha256':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['control_presentation.py','control-display-originals.jsonl','literal_numeric.py','control-display-candidates.jsonl']},'scope':'Pure display overlay; frozen537 and987 manifest preserved. No new mathematical task, answer, parameter, idea, level, semanticHash or lineage. Independent root review pending.'}
 (P/'control-display-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('10 immutable display overlays;40 exact equalities;60 pair inequalities')
