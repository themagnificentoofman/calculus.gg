"""Finite common-form option repair. No frozen source or live bank is mutated."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import copy,hashlib,itertools,json,re
P=Path(__file__).resolve().parent
FAMILY='q2-repair-m3-limits-easy-rational-sequence-shift'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
@lru_cache(None)
def sources():
 manifest=json.loads((P/'source-manifest.json').read_text())
 assert hashlib.sha256((P/'source-records.jsonl').read_bytes()).hexdigest()==manifest['sourceRecordsSha256']
 records={r['parameters']['instance']:r for r in map(json.loads,(P/'source-records.jsonl').read_text().splitlines())}
 for j in manifest['records']:assert digest(records[j['index']])==j['canonicalRawSha256']
 assert sorted(records)==list(range(10))
 return records
def catalog():return [{'familyId':FAMILY,'indices':list(range(10))}]
def parse_statement(text):
 m=re.fullmatch(r'\\lim_\{n\\to\\infty\}\\left\(\\frac\{(\d+)n\+1\}\{(\d+)n\+2\}\\right\)\^\{(\d+)\}',text)
 if not m:raise ValueError('Unknown literal sequence statement')
 a,c,p=map(int,m.groups());assert a>0 and c>0 and p in[2,3]
 return a,c,p
def power_tex(base,p):return rf'\left(\frac{{{base.numerator}}}{{{base.denominator}}}\right)^{{{p}}}'
def choice(base,p,label):
 math=power_tex(base,p)
 return {'choiceId':'ch_'+hashlib.sha256(math.encode()).hexdigest()[:16],'math':math,'misconception':label}
def parse_old_rational(text):
 m=re.fullmatch(r'\\frac\{(\d+)\}\{(\d+)\}',text)
 if not m:raise ValueError('Unreviewed original answer form')
 return Fraction(int(m[1]),int(m[2]))
def build(family,index):
 if family!=FAMILY or type(index)is not int or index not in sources():raise ValueError('Outside exact finite repair domain')
 old=copy.deepcopy(sources()[index]);a,c,p=parse_statement(old['statement'])
 correct=Fraction(a,c);reciprocal=Fraction(c,a)
 first=Fraction(a+1,c+2)
 # A finite first-term mistake is kept when its ratio is nonintegral.
 # Otherwise, retain the numerator's leading coefficient but incorrectly
 # combine the denominator's constant with its coefficient of n.
 if first.denominator==1:
  mistaken=Fraction(a,c+2);label='Combine the denominator constant with its coefficient of n before taking the limit.'
 else:
  mistaken=first;label='Evaluate the sequence at n=1 instead of taking its limit.'
 alternatives=[(reciprocal,'Invert the limiting leading-coefficient ratio.'),(Fraction(1,2),'Use the constant terms instead of the leading coefficients.'),(mistaken,label)]
 # In the repeated 2/3 cubic case, exercise inversion of the finite first
 # term as well as inversion of the limit. All four bases remain distinct.
 if index==6:
  assert (a,c,p)==(2,3,3)
  alternatives=[(reciprocal,'Invert the limiting leading-coefficient ratio.'),(first,'Evaluate the sequence at n=1 instead of taking its limit.'),(1/first,'Invert the sequence value at n=1 instead of taking the limit.')]
 choices=[choice(correct,p,'correct')]+[choice(base,p,label)for base,label in alternatives]
 values=[correct**p]+[base**p for base,_ in alternatives]
 assert len(set(values))==4 and all(v>0 for v in values)
 old_correct=next(c['math']for c in old['choices']if c['choiceId']==old['answerChoiceId'])
 assert parse_old_rational(old_correct)==values[0]
 # Ordering here is merely serialized authoring order. Serving and the fixed
 # diagnostic independently shuffle it; no source ID or split is changed.
 row={k:copy.deepcopy(old[k])for k in ['familyId','topic','difficulty','statement','assumptions','pedagogy']}
 row.update({'parameters':{'a':a,'c':c,'power':p},'instanceIndex':index,'finiteInstanceIndices':list(range(10)),
  'constructorVersion':'quality-rational-sequence-common-form-options-v1',
  'choices':choices,'answerChoiceId':choices[0]['choiceId'],
  'solutionSteps':old['solutionSteps'][:-1]+[choices[0]['math']],
  'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':digest(old)},
  'replacesPrivateProblemId':old['problemId'],'provenance':{'kind':'original','theoremReferenceURLs':[]},
  'review':{'status':'candidate-awaiting-independent-parent-review','meaningChanged':False,'answerChanged':False,'newIndependentIdeas':0,
   'easiestOptionsVisibleRoute':'Divide numerator and denominator by n, take the ratio of their nonzero leading coefficients, then apply the fixed continuous power. Easy fluency with the actual options visible.',
   'optionRepairReason':'Every choice is a reduced positive rational base raised to the same displayed fixed power. No correct-only expanded-power length or integer/fraction convention remains.',
   'semanticLineage':'Same exact unpublished finite task and construction; no new idea or effective capacity.',
   'conclusionAmendment':{'old':old['solutionSteps'][-1],'new':choices[0]['math'],'exactEquality':True,'reason':'The previous expanded rational equals the common-form power exactly; the existing leading-coefficient and continuity derivation is preserved.'}},
  'verificationEvidence':[{'kind':'exact-finite-rational-options','correctLimit':str(values[0]),'pairDifferences':[str(values[i]-values[j])for i,j in itertools.combinations(range(4),2)],
   'domain':'Positive leading denominator c ensures the sequence denominator is nonzero for every positive integer n. The fixed integer power is continuous at the finite ratio.',
   'allSixPairsNonzero':True,'mathematicalOppositePairs':0,'namedMistakeValues':[{'base':str(base),'power':p,'value':str(base**p),'route':label}for base,label in alternatives]}]})
 row['contentHash']=digest(row)
 return row
def verify(row):
 try:return canonical(row)==canonical(build(row['familyId'],row['instanceIndex']))
 except(ValueError,KeyError,TypeError):return False
if __name__=='__main__':
 rows=[build(FAMILY,i)for i in range(10)]
 (P/'candidates.jsonl').write_text(''.join(canonical(r)+'\n'for r in rows))
 print(json.dumps({'records':len(rows),'sixPairChecks':60,'independentPeer':'pending','registered':False}))
