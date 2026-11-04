"""Portable input discovery for the supplemental solution-review scripts.

Explicit overrides: CN_SOLUTION_SOURCE_REPO and CN_SOLUTION_SOURCE_ARTIFACT.
No network access or writes to the selected source repository are performed.
"""
import json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent

def source_repo():
 explicit=os.environ.get('CN_SOLUTION_SOURCE_REPO')
 if explicit:
  repo=Path(explicit).expanduser().resolve()
  if not (repo/'scripts/bank/content').is_dir():raise FileNotFoundError('CN_SOLUTION_SOURCE_REPO must contain scripts/bank/content')
  return repo
 candidates=[*HERE.parents,HERE.parents[1]/'solution-audit',Path.cwd()]
 for repo in candidates:
  if (repo/'scripts/bank/content').is_dir():return repo
 raise FileNotFoundError('Set CN_SOLUTION_SOURCE_REPO to the inspected repository checkout')

def source_artifact():
 explicit=os.environ.get('CN_SOLUTION_SOURCE_ARTIFACT')
 if explicit:
  artifact=Path(explicit).expanduser().resolve()
  if not artifact.is_file():raise FileNotFoundError('CN_SOLUTION_SOURCE_ARTIFACT is not a readable file')
  return artifact
 suffix=Path('.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl')
 candidates=[]
 try:candidates.append(source_repo()/suffix)
 except FileNotFoundError:pass
 candidates += [HERE.parents[1]/'milestone3'/suffix]
 for artifact in candidates:
  if artifact.is_file():return artifact
 # An inspected evidence manifest may record its original input location.
 manifest=HERE/'manifest.json'
 if manifest.is_file():
  recorded=Path(json.loads(manifest.read_text()).get('artifact',''))
  if recorded.is_file():return recorded
 raise FileNotFoundError('Set CN_SOLUTION_SOURCE_ARTIFACT to the immutable JSONL artifact')
