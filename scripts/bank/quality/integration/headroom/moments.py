"""Explicit additional mass/first-moment constraints; zero new idea groups.
Frozen original source is unchanged. Load in an isolated offline process only.
"""
from pathlib import Path
import json,sys
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'frozen'))
import integrals,verify_integrals
R=integrals.R
FID='quality-integration-olympiad-capped-two-moment-extrema'
CASES=[(R(5,8),R(1,8)),(R(7,12),R(1,6)),(R(2,7),R(1,14)),(R(3,8),R(1,8)),(R(5,9),R(1,9)),(R(7,15),R(2,15)),(R(4,9),R(1,9)),(R(5,11),R(2,11))]
assert len(integrals.BATHTUB_CASES)==10
assert not {m for m,r in CASES}&{m for m,r in integrals.BATHTUB_CASES}
integrals.BATHTUB_CASES+=CASES
integrals.FAMILIES[FID]['finiteInstanceIndices']=list(range(10,18))
integrals.FAMILIES[FID]['constructorVersion']='quality-integration-purposeful-moment-headroom-v1'
def catalog():return [{k:v for k,v in integrals.FAMILIES[FID].items() if k!='fn'}]
def build(fid,index):
 if fid!=FID or type(index)is not int or index not in range(10,18):raise ValueError('Outside explicit additional moment domain')
 return integrals.build(fid,index)
def verify(r):
 expected=build(r['familyId'],r['instanceIndex']);assert r==expected
 report=verify_integrals.verify(r);assert report['status']=='passed' and report['sourceContentHash']==r['contentHash'] and report['checks']
 return report
if __name__=='__main__':
 rows=[]
 for i in range(10,18):
  r=build(FID,i);verify(r);rows.append(r)
 Path(sys.argv[1]).write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n' for r in rows));print('8 additional moment cases; separate independent peer and final-ID screen required')
