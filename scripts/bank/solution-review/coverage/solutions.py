"""Exact-original, versioned solution repairs. Standard library only at runtime.

The active release and all original answers/IDs remain immutable. This lookup
only applies to the precise audited original record; it never rewrites an
unrecognized version or extrapolates a builder to new parameter values.
"""
from pathlib import Path
from functools import lru_cache
from copy import deepcopy
import hashlib,json
BASE=Path(__file__).resolve().parent
CORRECTION_VERSION='coverage-solutions-2026-11-03-v1'

def record_digest(record):
 return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

@lru_cache(None)
def _data():
 data=json.loads((BASE/'correction-data.json').read_text())
 assert data['correctionVersion']==CORRECTION_VERSION
 return {r['problemId']:r for r in data['corrections']}

def supports(record):
 if not isinstance(record,dict):return False
 item=_data().get(record.get('problemId'))
 return bool(item and record.get('contentHash')==item['originalContentHash'] and record.get('familyId')==item['familyId'] and record.get('parameters',{}).get('instance')==item['instance'])

def _guarded(record):
 if not supports(record):raise ValueError('No correction for this exact problem, family, instance, and original content hash')
 item=_data()[record['problemId']]
 if record_digest(record)!=item['originalRecordSha256']:raise ValueError('Original record differs from the completely audited immutable input')
 return item

def corrected_solution(record):
 return list(_guarded(record)['solutionSteps'])

def audit_evidence(record):
 return deepcopy(_guarded(record))


def corrected_statement(record):
 """Return the same-semantic notation repair, or None when none is needed."""
 return _guarded(record).get('statement')
