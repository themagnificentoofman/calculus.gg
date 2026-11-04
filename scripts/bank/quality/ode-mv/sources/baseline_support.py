"""Read-only access to pinned constructors and independently encoded solutions.
No frozen source is changed. Parent packaging may set the two explicit roots.
"""
from pathlib import Path
import importlib.util,os,sys
ROOT=Path(__file__).resolve().parent
def locate(relative,fallback):
 for ancestor in ROOT.parents:
  p=ancestor/relative
  if p.exists():return p
 return Path(fallback)
CONTENT=Path(os.environ.get('QUALITY_BASELINE_CONTENT_DIR',str(locate('scripts/bank/content',ROOT.parents[1]/'problem-quality/scripts/bank/content'))))
REVIEW=Path(os.environ.get('QUALITY_BASELINE_REVIEW_DIR',str(locate('scripts/bank/solution-review/supplemental',ROOT.parents[1]/'solution-research/supplemental'))))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mo=importlib.util.module_from_spec(spec);spec.loader.exec_module(mo);return mo

# coverage.py uses unqualified sibling imports. Temporarily bind exactly those
# pinned siblings, restoring every previous binding after the frozen load.
names=['multivariable','extra','certificates','distractors','editorial']
saved={k:sys.modules.get(k) for k in names};oldpath=list(sys.path)
try:
 sys.path.insert(0,str(CONTENT))
 for name in names:sys.modules[name]=load('quality_pinned_'+name,CONTENT/(name+'.py'))
 coverage=load('quality_pinned_coverage',CONTENT/'coverage.py')
 frozen_ode=load('quality_pinned_ode',CONTENT/'ode.py')
finally:
 sys.path[:]=oldpath
 for name,value in saved.items():
  if value is None:sys.modules.pop(name,None)
  else:sys.modules[name]=value
oldpath=list(sys.path)
try:
 sys.path.insert(0,str(REVIEW));solutions=load('quality_pinned_supplemental_solutions',REVIEW/'solutions.py');checks=load('quality_pinned_supplemental_checks',REVIEW/'substantive_checks.py')
finally:sys.path[:]=oldpath
FAMILIES={f['familyId']:f for f in coverage.FAMILIES if f['topic']=='multivariable' and f['editorialStatus']=='admitted'}
FAMILIES.update(frozen_ode.FAMILIES)

