"""Portable full finite reproduction into a NEW scratch directory."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
BASE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
 print('Running '+Path(str(args[2]if args[1]=='-B'else args[1])).name,flush=True)
 subprocess.run(args,check=True,cwd=BASE)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--repo',type=Path,help='Optional source repository containing installed KaTeX');a=ap.parse_args();a.output=a.output.resolve();assert not a.output.exists(),'Use a new output directory';a.output.mkdir(parents=True)
 for item in read(BASE/'copy-manifest.json')['files']:assert sha(BASE/item['path'])==item['sha256'],item['path']
 if(BASE/'delivery-manifest.json').exists():
  for name,digest in read(BASE/'delivery-manifest.json')['files'].items():assert sha(BASE/name)==digest,name
 run([sys.executable,'-B',BASE/'verify_bundle.py','--output',a.output/'reconstruction.json'])
 source=BASE/'review/effective705-final-v3.jsonl';checks={}
 for code,target in [('audit_pairs.py','mathematical-pairs-final-v3.json'),('audit_ranks.py','mathematical-ranks-final-v3.json'),('domain_inventory.py','domain-inventory-final.json')]:
  result=a.output/target;run([sys.executable,'-B',BASE/'review-code'/code,'--input',source,'--output',result]);assert read(result)==read(BASE/'review'/target),target;checks[target]='exact semantic report parity'
 result=a.output/'root-option-screen-final-v3.json';run(['node',BASE/'review-code/option-audit.mjs',source,result]);assert read(result)==read(BASE/'review/root-option-screen-final-v3.json');checks[result.name]='exact semantic report parity with frozen actual-source IDs'
 # Independently authored mathematics remains a separate executable path.
 first=BASE/'evidence/last76-statement-first-review.json';shutil.copyfile(first,a.output/first.name)
 for code,folder,expected in [('series_domain_patch.py','six-row-frozen-v1','domain-option-peer-v1.json'),('series_bracket_patch.py','eighty-row-frozen-v1','bracket-option-peer-v1.json'),('series_last76_peer.py','last76-frozen-v1','last76-independent-peer.json')]:
  result=a.output/expected;run([sys.executable,'-B',BASE/'evidence/independent-code'/code,BASE/'frozen'/folder,result]);actual=read(result);previous=read(BASE/'evidence'/expected);assert actual['records']==previous['records'];assert actual.get('reviewCodeSHA256',actual.get('reviewSources'))==previous.get('reviewCodeSHA256',previous.get('reviewSources'));checks[expected]='all independently reconstructed finite record certificates exactly match; source folder path may differ'
 result=a.output/'capacity-after-options.json';run([sys.executable,'-B',BASE/'review-code/capacity_after_options.py','--ledger',BASE/'evidence/previous-capacity-ledger.json','--records',BASE/'full-source-records.jsonl','--changes',BASE/'difficulty-changes.json','--output',result]);actual=read(result);expected=read(BASE/'capacity-after-options.json');assert actual['afterCounts']==expected['afterCounts']and actual['recordsEvidence']==expected['recordsEvidence'];checks[result.name]='all705 unchanged normalized keys joined to reviewed levels'
 if a.repo:
  render=a.output/'render';render.mkdir();shutil.copyfile(BASE/'review-code/render_final_patches.cjs',render/'render_final_patches.cjs')
  for folder,artifact in [('six-row-frozen-v1','option-patches.json'),('eighty-row-frozen-v1','bracket-option-patches.json'),('last76-frozen-v1','support-option-patches.json')]:shutil.copyfile(BASE/'frozen'/folder/artifact,render/artifact)
  run(['node',render/'render_final_patches.cjs',a.repo.resolve()]);assert read(render/'patch-render-report-final.json')==read(BASE/'review/patch-render-report-final.json');checks['strictKaTeX']='all648 amended math fields pass and match the frozen report'
 report={'status':'portable-reproduction-passed','patches':162,'completeMenuScope':705,'checks':checks,'inputBundle':str(BASE),'scope':'Local mathematical reconstruction and bounded option checks; no destination admission, registry edit, horizon rerun, import or deployment.'};(a.output/'reproduction-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
