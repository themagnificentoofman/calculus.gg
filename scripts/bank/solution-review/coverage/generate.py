"""Reproduce all 1256 corrections and mathematical evidence.

Set BANK_AUDIT_ARTIFACT to the exact release JSONL. BANK_AUDIT_CONTENT_DIR can
point at the frozen builder source; in a repository it is inferred. Uses SymPy.
Run with the repository's .bank-venv/bin/python, then node render-check.cjs.
"""
from common import *
from collections import Counter,defaultdict
import traceback,importlib
from solutions import CORRECTION_VERSION,record_digest

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 modules={topic:importlib.import_module(topic+'_solutions') for topic in ['integration','differentiation','limits','series']}
 selected=[json.loads(line) for line in BANK.read_text().splitlines() if line.strip()]
 selected=[r for r in selected if r['familyId'] in FAMILIES]
 groups=defaultdict(list);out=[];errors=[]
 for index,record in enumerate(selected):
  try:
   solution=modules[record['topic']].solve(record)
   if record['familyId']=='m3-series-olympiad-hypergeometric-beta':
    _,m,_=role(record)
    solution['statement']=r'\sum_{k=0}^\infty\frac{(1/2)_k^2}{k!(k+'+tex(m)+r')!},\qquad(a)_0=1,\quad(a)_k=a(a+1)\cdots(a+k-1)\quad(k\ge1).'
    solution['notes'].append('Statement notation only: the original superscript rising-factorial printer and overbar definition are both standardized to the explicitly defined subscript rising factorial. The series is unchanged.')
    solution['issues'].append('rising-factorial-convention-mismatch')
   assert solution['checks'],'Every family must carry an executed or analytic verification route'
   for check in solution['checks']:
    assert check.get('result') not in [False,None],check
   item={'problemId':record['problemId'],'familyId':record['familyId'],'instance':record['parameters']['instance'],'originalContentHash':record['contentHash'],'originalRecordSha256':record_digest(record),'reviewEvidenceId':'coverage-solution-review:'+record['familyId']+':v1','topic':record['topic'],'difficulty':record['difficulty'],**solution}
   out.append(item);groups[record['familyId']].append(item)
  except Exception as e:
   errors.append({'problemId':record['problemId'],'familyId':record['familyId'],'instance':record['parameters']['instance'],'error':repr(e),'traceback':traceback.format_exc()})
  if (index+1)%160==0:print('Reviewed',index+1,'of',len(selected),'errors',len(errors),flush=True)
 (BASE/'generation-errors.json').write_text(json.dumps(errors,indent=2))
 assert not errors,errors[:3]
 assert len(out)==1256 and len(groups)==157
 assert set(groups)==set(FAMILIES)
 assert all(sorted(r['instance'] for r in rows)==list(range(8)) for rows in groups.values())
 family_audit=[]
 for fid,rows in sorted(groups.items()):
  checks=[c for row in rows for c in row['checks']]
  family_audit.append({'familyId':fid,'topic':rows[0]['topic'],'difficulty':rows[0]['difficulty'],'reviewEvidenceId':rows[0]['reviewEvidenceId'],'status':'all-finite-instances-corrected-and-checked','reviewType':'AI-assisted editorial review; no human-review or formal-proof claim','instanceCount':len(rows),'instanceIndices':[r['instance'] for r in rows],'problemIds':[r['problemId'] for r in rows],'originalIssuesAddressed':sorted(set(tag for row in rows for tag in row['issues'])),'correctionScope':('Solution explanation and same-semantic rising-factorial notation clarification. Choices, correct-answer identifiers, and original records are unchanged.' if any('statement' in r for r in rows) else 'Solution explanation only. Statements, choices, correct-answer identifiers and original records are unchanged.'),'verificationDescriptions':sorted(set(c['description'] for c in checks)),'executedExactOrBooleanChecks':sum(c.get('result') in [True,'exact equality'] for c in checks),'analyticTheoremApplications':sum(isinstance(c.get('result'),str) and c['result'].startswith('analytic theorem') for c in checks),'mathematicalJustification':'Each instance in correction-data.json includes the complete revised derivation, explicit domains/branches/convergence justification where needed, and its executed intermediate checks. Analytic theorem applications are separated from symbolic equalities.','notes':sorted(set(n for row in rows for n in row['notes'])),'unresolvedIssues':[]})
 payload={'correctionVersion':CORRECTION_VERSION,'originalArtifactSha256':digest(BANK),'scope':{'families':len(groups),'instances':len(out),'topics':dict(Counter(r['topic'] for r in out))},'corrections':out}
 (BASE/'correction-data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 (BASE/'family-audit.json').write_text(json.dumps({'correctionVersion':CORRECTION_VERSION,'scope':payload['scope'],'families':family_audit},ensure_ascii=False,indent=2)+'\n')
 # Frozen code digests make the authoring inputs reproducible. Runtime requires only the data and lookup module.
 manifest={'correctionVersion':CORRECTION_VERSION,'artifact':{'path':str(BANK),'sha256':digest(BANK)},'frozenBuilderSources':{p.name:digest(p) for p in sorted(SOURCE.glob('*.py'))},'frozenAdmission':digest(SOURCE/'admission.json'),'authoringSources':{p.name:digest(p) for p in sorted(BASE.iterdir()) if p.is_file() and p.suffix in ['.py','.cjs','.md']},'generatedFiles':{name:digest(BASE/name) for name in ['correction-data.json','family-audit.json']},'recordCoverage':payload['scope'],'reviewLimitations':['AI-assisted mathematical/editorial review and executed exact checks, not human review or a formal proof system.','Named standard analytic theorems are applied with displayed hypotheses; their general proofs are not claimed as CAS verification.','Only the exact 157 admitted families and eight existing instances per family are covered. No new instance is implicitly admitted.']}
 (BASE/'source-digest-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'families':len(groups),'instances':len(out),'checks':sum(len(r['checks']) for r in out),'byTopic':payload['scope']['topics'],'errors':len(errors)}),flush=True)
if __name__=='__main__':main()
