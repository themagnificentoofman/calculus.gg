"""Standard-library runtime compatibility and immutable-input guard verification."""
from pathlib import Path
from copy import deepcopy
import os,json,hashlib
from solutions import supports,corrected_solution,corrected_statement,audit_evidence,record_digest
BASE=Path(__file__).resolve().parent

def normalize(value):
 return value.replace(r'\log',r'\ln').replace(r'\operatorname{atan}',r'\arctan').replace(r'\operatorname{asin}',r'\arcsin').replace(r'\operatorname{acos}',r'\arccos').replace(r'\operatorname{asinh}',r'\operatorname{arsinh}').replace(r'\operatorname{acosh}',r'\operatorname{arcosh}').replace(r'\operatorname{atanh}',r'\operatorname{artanh}')

def main():
 manifest=json.loads((BASE/'source-digest-manifest.json').read_text())
 source=Path(os.environ.get('BANK_AUDIT_ARTIFACT',manifest['artifact']['path']))
 assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['artifact']['sha256']
 rows=[json.loads(v) for v in source.read_text().splitlines() if v.strip()];selected=[r for r in rows if supports(r)]
 assert len(selected)==1256
 statements=0;guardChecks=0
 for record in selected:
  before=record_digest(record);steps=corrected_solution(record);override=corrected_statement(record);evidence=audit_evidence(record)
  originalAnswer=next(v['math'] for v in record['choices'] if v['choiceId']==record['answerChoiceId'])
  assert steps[-1]==normalize(originalAnswer)
  assert before==record_digest(record),'The runtime API mutated the immutable input'
  assert evidence['originalRecordSha256']==before
  if override is not None:
   assert record['familyId']=='m3-series-olympiad-hypergeometric-beta';statements+=1
  mutant=deepcopy(record);mutant['statement']+=' '
  try:corrected_solution(mutant)
  except ValueError:guardChecks+=1
  else:raise AssertionError('A changed original statement bypassed the digest guard')
  mutant=deepcopy(record);mutant['contentHash']='wrong'
  assert not supports(mutant);guardChecks+=1
  mutant=deepcopy(record);mutant['problemId']='unknown'
  assert not supports(mutant);guardChecks+=1
 assert statements==8
 report={'records':len(selected),'answerMatches':len(selected),'unchangedInputRecords':len(selected),'sameSemanticStatementOverrides':statements,'successfulNegativeGuardChecks':guardChecks,'runtimeDependencies':'Python standard library only','correctionDataSha256':hashlib.sha256((BASE/'correction-data.json').read_bytes()).hexdigest()}
 (BASE/'api-verification-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
