"""Source-bound opposite-pair inspection of the independently reviewed Limits scope."""
from pathlib import Path
import argparse,json,re,itertools,hashlib
from verify_limits import decode,digest,SLUGS
from rigorous_intervals import enclose,add
import sympy as s

def compact(t):return re.sub(r'\\(?:,|!|;|quad|qquad|left|right)|\s','',t)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();rows=[r for r in json.loads((a.stage/'candidates.json').read_text()) if re.sub(r'^q1-limits-(?:olympiad|hard)-','',r['familyId']) in SLUGS];out=[]
 for r in rows:
  values=[decode(c['expression']) for c in r['choices']];lit=[compact(c['math']) for c in r['choices']];actual=[];literal=[]
  for i,j in itertools.combinations(range(4),2):
   # If the two intervals have a common strict sign, opposition is impossible.
   same=(values[i].is_positive is True and values[j].is_positive is True) or (values[i].is_negative is True and values[j].is_negative is True)
   if not same:
    v,w=enclose(values[i]),enclose(values[j]);z=add(v,w)
    if z[0]<=0<=z[1] and s.simplify(values[i]+values[j])==0:actual.append([r['choices'][i]['choiceId'],r['choices'][j]['choiceId']])
   if lit[i]=='-'+lit[j] or lit[j]=='-'+lit[i]:literal.append([r['choices'][i]['choiceId'],r['choices'][j]['choiceId']])
  out.append({'familyId':r['familyId'],'instanceIndex':r['parameters']['instance'],'rawSHA256':digest(r),'mathematicalOppositePairs':actual,'literalOppositePairs':literal,'answerChoiceId':r['answerChoiceId']})
 dest=a.out/'opposite-pair-review.json';dest.write_text(json.dumps({'sourceSHA256':hashlib.sha256((a.stage/'candidates.json').read_bytes()).hexdigest(),'reviewerCodeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'records':out,'counts':{'records':len(out),'mathematicalPairs':sum(len(r['mathematicalOppositePairs']) for r in out),'literalPairs':sum(len(r['literalOppositePairs']) for r in out)},'scope':'Both positive and negative pair-member patterns checked. Literal comparison follows the parent diagnostic; true opposition is independently checked with certified signs and exact expressions.'},indent=2)+'\n');print(json.loads(dest.read_text())['counts'])
if __name__=='__main__':main()
