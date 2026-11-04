"""Question-blind train/held-out heuristics; no mathematical answer access in features."""
import argparse,json,math,re
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent
def features(r,c):
 t=c['math'];v=r.get('optionAudit',{}).get('valuesByChoiceId',{}).get(c['choiceId']);values=r.get('optionAudit',{}).get('valuesByChoiceId',{})
 nums=re.findall(r'(?<![A-Za-z])\d+',t)
 return {'texLength':len(t),'fractionCount':t.count('\\frac'),'radicalCount':t.count('\\sqrt'),'operatorCount':sum(t.count(q) for q in ['+','-','^']),'integerTokenCount':len(nums),'largestIntegerToken':max(map(int,nums),default=0),'hasPi':int('\\pi' in t),'hasLn':int('\\ln' in t),'hasGamma':int('\\Gamma' in t),'isPlainInteger':int(bool(re.fullmatch(r'-?\d+',t))),'numericRank':sum(x<v for x in values.values()) if v is not None else None,'numericSign':(1 if v>0 else -1 if v<0 else 0) if v is not None else None,'nearInteger':int(abs(v-round(v))<1e-10) if v is not None and abs(v)<1e14 else None}
def predict(r,feature,mode):
 vals=[features(r,c)[feature] for c in r['choices']]
 if any(v is None for v in vals):return None
 target=min(vals) if mode=='min' else max(vals);ids=[i for i,v in enumerate(vals) if v==target]
 return r['choices'][ids[0]]['choiceId'] if len(ids)==1 else None
def score(rows,feature,mode):
 selected=[(r,predict(r,feature,mode)) for r in rows];decided=[(r,p) for r,p in selected if p is not None];correct=sum(p==r['answerChoiceId'] for r,p in decided)
 return {'items':len(rows),'decided':len(decided),'correct':correct,'accuracyWhenDecided':correct/len(decided) if decided else None,'chanceFilledExpectedAccuracy':(correct+(len(rows)-len(decided))/4)/len(rows) if rows else None}
def audit(rows):
 train=[r for r in rows if r['instanceIndex']%8<4];held=[r for r in rows if r['instanceIndex']%8>=4]
 if not held:held=rows;train=[]
 names=list(features(rows[0],rows[0]['choices'][0]));tests=[]
 for f in names:
  for mode in ['min','max']:tests.append({'feature':f,'mode':mode,'development':score(train,f,mode),'heldOut':score(held,f,mode)})
 family=[]
 for fid in sorted({r['familyId'] for r in rows}):
  rs=[r for r in rows if r['familyId']==fid];ranks=[r.get('optionAudit',{}).get('correctNumericRank') for r in rs];risks=[]
  for f in names:
   for mode in ['min','max']:
    sc=score(rs,f,mode)
    if sc['decided']==len(rs) and sc['correct']==len(rs):risks.append({'feature':f,'mode':mode,'scope':'all finite instances'})
  family.append({'familyId':fid,'instances':len(rs),'correctNumericRanks':ranks,'perfectOptionOnlyRules':risks,'blindDifficultyReview':'separate independent reviewer; these syntax/number heuristics cannot judge a proof'})
 ranked=sorted([t for t in tests if t['development']['items']],key=lambda t:t['development']['chanceFilledExpectedAccuracy'],reverse=True)
 return {'developmentItems':len(train),'heldOutItems':len(held),'split':'indices 0..3 development, 4..7 held out, applied before testing; new 8/9 extension is development only and separately labeled','ruleSelection':'rank fixed question-blind rules by development success; evaluate same rule on held-out items without retuning','bestDevelopmentRule':ranked[0] if ranked else None,'allRules':tests,'families':family,'limitations':['This is a bounded heuristic screen, not proof that no cue exists.','Unresolved numeric data are excluded from numeric rules; numerical values are presentation diagnostics only.','No statement or solution text is used by any heuristic.','A flagged family must receive authored option repair or be withheld; passing this screen does not establish Olympiad fit.']}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--out',type=Path,default=ROOT/'option-audit.json');a=ap.parse_args();rows=[json.loads(l) for l in a.input.read_text().splitlines()];report=audit(rows);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'bestDevelopmentRule':report['bestDevelopmentRule'],'perfectFamilyRules':[{k:v for k,v in f.items() if k in ['familyId','perfectOptionOnlyRules']} for f in report['families'] if f['perfectOptionOnlyRules']]}))
