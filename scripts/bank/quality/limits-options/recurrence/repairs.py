"""Finite, source-bound recurrence-menu repair; frozen sources are read only."""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,itertools,json,math,re
P=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
@lru_cache(None)
def sources():
 manifest=json.loads((P/'source-manifest.json').read_text())
 assert hashlib.sha256((P/'source-records.jsonl').read_bytes()).hexdigest()==manifest['sourceRecordsSha256']
 assert hashlib.sha256((P/'reviewed-presentations.json').read_bytes()).hexdigest()==manifest['reviewedPresentationsSha256']
 records=list(map(json.loads,(P/'source-records.jsonl').read_text().splitlines()))
 assert len(records)==10
 for j,r in zip(manifest['records'],records):assert digest(r)==j['canonicalRawSha256'] and r['problemId']==j['problemId']
 return records,manifest,json.loads((P/'reviewed-presentations.json').read_text())
def catalog():
 rows,_,_=sources()
 return [{'familyId':f,'indices':[i for i,r in enumerate(rows)if r['familyId']==f]}for f in sorted({r['familyId']for r in rows})]
def choice(value,label):
 text=str(value)
 return {'choiceId':'ch_'+hashlib.sha256(text.encode()).hexdigest()[:16],'math':text,'misconception':label}
def build(family,index):
 records,manifest,presentations=sources()
 if type(index)is not int or index not in range(10)or records[index]['familyId']!=family:raise ValueError('Outside exact finite repair domain')
 old=copy.deepcopy(records[index]);join=manifest['records'][index]
 match=re.fullmatch(r'a_0=0,\\quad a_\{n\+1\}=\\sqrt\{(\d+)\+a_n\}\.\\quad\\lim a_n=\?',old['statement'])
 if not match:raise ValueError('Unreviewed literal recurrence')
 C=int(match[1]);delta=math.isqrt(1+4*C);assert delta*delta==1+4*C
 m=(1+delta)//2;assert m*(m-1)==C and m==index+4
 # All alternatives are exact outputs of named quadratic/convergence errors.
 routes={
  'absolute-negative':(m-1,'Take the absolute value of the negative fixed-point root.',f'abs((1-sqrt(1+4*{C}))/2)={m-1}'),
  'omit-denominator':(2*m,'Omit division by two in the positive quadratic root.',f'1+sqrt(1+4*{C})={2*m}'),
  'discriminant-only':(2*m-1,'Return the square root of the discriminant without the final addition and division.',f'sqrt(1+4*{C})={2*m-1}'),
  'radicand':(C,'Return the radicand constant instead of solving the fixed-point equation.',f'C={C}'),
  'initial-value':(0,'Treat the initial value as the limiting value without applying the recurrence.',f'a_0=0, but a_1=sqrt({C})>0'),
 }
 if m%2==0:routes['half-root']=(m//2,'Divide the positive quadratic root by two a second time.',f'(1+sqrt(1+4*{C}))/4={m//2}')
 else:routes['half-root']=((m-1)//2,'Divide the magnitude of the negative quadratic root by two a second time.',f'abs(1-sqrt(1+4*{C}))/4={(m-1)//2}')
 # Select concrete finite misconception sets without consulting any problem
 # ID, diagnostic shuffle, training split, or classifier result.
 # Small limits use the initial-value error where it tests a convergence
 # misconception; larger limits include quadratic numerator errors.
 if m in [4,6,8]:keys=['absolute-negative','half-root','initial-value']
 elif m in [5,7,9]:keys=['absolute-negative','half-root','discriminant-only']
 elif m in [10,12]:keys=['half-root','omit-denominator','radicand']
 else:keys=['discriminant-only','omit-denominator','radicand']
 alternatives=[routes[k]for k in keys];values=[m]+[a[0]for a in alternatives]
 assert len(set(values))==4 and all(v>=0 for v in values)
 choices=[choice(m,'correct')]+[choice(value,label)for value,label,_ in alternatives]
 old_correct=next(c['math']for c in old['choices']if c['choiceId']==old['answerChoiceId']);assert int(old_correct)==m
 steps=presentations[old['problemId']]['steps']if old['problemId']in presentations else old['solutionSteps']
 assert steps[-1]==str(m)
 row={k:copy.deepcopy(old[k])for k in ['familyId','topic','difficulty','statement','assumptions','pedagogy']}
 row.update({'parameters':{'limit':m,'radicandConstant':C},'instanceIndex':index,
  'finiteInstanceIndices':next(c['indices']for c in catalog()if c['familyId']==family),
  'constructorVersion':'quality-recurrence-common-integer-options-v1','choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':copy.deepcopy(steps),
  'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':digest(old)},
  'replacesPrivateProblemId':old['problemId'],'provenance':{'kind':'original','theoremReferenceURLs':[]},
  'review':{'status':'candidate-awaiting-independent-parent-review','meaningChanged':False,'answerChanged':False,'newIndependentIdeas':0,
   'easiestOptionsVisibleRoute':'Use the nonnegative invariant interval and monotone convergence, then solve the fixed-point quadratic; the positive root is the limit. The revised menu removes the former fixed second-largest rank.',
   'optionRepairReason':'Every option uses the same canonical integer form. Concrete quadratic and convergence mistakes replace the fixed radical/integer rank pattern; no arbitrary numeric offsets or opposite pairs are used.',
   'semanticLineage':'Same exact finite task and construction; no new idea or effective capacity.',
   'presentationInheritance':{'source':'source-bound-reviewed-presentation'if old['problemId']in presentations else'exact-current-canonical-solution','stepsUnchanged':True,'ambiguousParameterLabelsReintroduced':False}},
  'verificationEvidence':[{'kind':'exact-finite-integer-options','correctLimit':m,'pairDifferences':[values[i]-values[j]for i,j in itertools.combinations(range(4),2)],
   'allSixPairsNonzero':True,'mathematicalOppositePairs':0,'correctNumericRank':sorted(values).index(m)+1,
   'domain':'For u in [0,m], sqrt(C+u) is real and at most m; C=m(m-1). Its square minus u squared is (m-u)(m+u-1), nonnegative. Starting at zero, induction gives nonnegative increasing bounded iterates. Continuity gives L^2-L-C=0, whose other root 1-m is negative.',
   'namedMistakeValues':[{'value':v,'route':label,'exactDerivation':derivation,'key':key}for key,(v,label,derivation)in zip(keys,alternatives)]}]})
 if join['previous']is not None:row['previous']=copy.deepcopy(join['previous'])
 row['contentHash']=digest(row)
 return row
def verify(row):
 try:return canonical(row)==canonical(build(row['familyId'],row['instanceIndex']))
 except(ValueError,KeyError,TypeError):return False
if __name__=='__main__':
 rows=[build(r['familyId'],i)for i,r in enumerate(sources()[0])]
 (P/'candidates.jsonl').write_text(''.join(canonical(r)+'\n'for r in rows))
 print(json.dumps({'records':len(rows),'sixPairChecks':60,'independentPeer':'pending','registered':False}))
