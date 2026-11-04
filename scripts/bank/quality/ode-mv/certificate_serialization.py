"""Narrow, exact equivalence guard for two frozen Green proof serializations.
No problem expression, option, answer, solution or mathematical claim changes.
"""
from pathlib import Path
import copy,hashlib,json
import sympy as s
BASE=Path(__file__).resolve().parent
SPEC=json.loads((BASE/'green-certificate-serialization-forms.json').read_text())
def canonical(r):return json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def normalize_generated(record,expected):
 if canonical(record)==canonical(expected):return record,[]
 if record.get('familyId')!=SPEC['familyId'] or expected.get('familyId')!=SPEC['familyId']:return record,[]
 index=record.get('instanceIndex');bound=next((q for q in SPEC['records'] if q['instanceIndex']==index),None)
 if bound is None or expected['contentHash']!=bound['sourceContentHash'] or expected['problemId']!=bound['problemId']:raise ValueError('Unbound Green serialization input')
 got=record['verificationEvidence'][2];want=expected['verificationEvidence'][2]
 if got['name']!=SPEC['checkName'] or want['name']!=SPEC['checkName']:raise ValueError('Unexpected proof slot')
 if got['left'] not in SPEC['allowedForms'] or want['left'] not in SPEC['allowedForms']:raise ValueError('Unreviewed CAS serialization form')
 lhs=s.sympify(got['left']);rhs=s.sympify(want['left'])
 if s.simplify(lhs-rhs)!=0:raise ValueError('Proof serializations are not exactly equal')
 generated=copy.deepcopy(record);frozen=copy.deepcopy(expected)
 generated.pop('contentHash');frozen.pop('contentHash')
 generated['verificationEvidence'][2]['left']=want['left']
 if canonical(generated)!=canonical(frozen):raise ValueError('Additional source difference outside the one proven proof serialization')
 # Reproduce common.H, the frozen source content-hash convention.
 digest=hashlib.sha256(json.dumps(generated,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
 if digest!=expected['contentHash']:raise ValueError('Frozen content hash did not reconstruct')
 generated['contentHash']=digest
 return generated,[{'scope':'one proof-description serialization only','checkName':SPEC['checkName'],'generatedLeft':got['left'],'frozenLeft':want['left'],'exactResidual':'0','allOtherNonhashFieldsIdentical':True,'originalContentHashRecomputed':digest}]
