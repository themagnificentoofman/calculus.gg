"""Finite literal function-domain inventory; no author answer calls."""
from pathlib import Path
import argparse,hashlib,json
import sympy as s
import literal_math
from enclosures import enclose
from audit_pairs import CATEGORICAL,H
def inspect(record):
 if record['familyId']in CATEGORICAL:return {'problemId':record['problemId'],'optionInputSHA256':H(record),'status':'categorical-literal-scope','reason':CATEGORICAL[record['familyId']],'choices':len(record['choices'])}
 details=[];functions=dict(literal_math.FUNCTIONS)
 for choice in record['choices']:
  seen=[]
  def wrapper(name,fn):
   def apply(a):
    assert a.is_real is not False
    condition='real argument'
    if name in ['ln','log','Gamma']:
     assert enclose(a)[0]>0;condition='strictly positive real argument; matches the positive Gamma definition where supplied'
    elif name=='zeta':assert a.is_Rational and a>1;condition='real argument greater than one'
    elif name=='K':assert a.is_Rational and 0<=a<1;condition='elliptic parameter in [0,1); source definition uses parameter rather than modulus'
    elif name in ['arcsin','arccos']:assert a.is_Rational and -1<=a<=1;condition='principal real inverse on [-1,1]'
    elif name=='dilog':assert a.is_Rational and -1<=a<=1;condition='real power-series argument in [-1,1]'
    elif name in ['tan','cot','coth']:
     den={'tan':s.cos,'cot':s.sin,'coth':s.sinh}[name](a);lo,hi=enclose(den);assert lo>0 or hi<0;condition='real denominator certified nonzero'
    seen.append({'function':name,'argument':s.srepr(a),'condition':condition,'passed':True});return fn(a)
   return apply
  try:
   literal_math.FUNCTIONS.update({name:wrapper(name,fn)for name,fn in functions.items()});v=literal_math.parse(choice['math'])
  finally:literal_math.FUNCTIONS.update(functions)
  for x in list(v)if isinstance(v,s.Tuple)else[v]:assert x in [s.oo,-s.oo]or x.is_real is not False
  details.append({'choiceId':choice['choiceId'],'functionArguments':seen,'literalParseComplete':True})
 return {'problemId':record['problemId'],'optionInputSHA256':H(record),'status':'literal-domain-obligations-checked','choices':details}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();rows=list(map(json.loads,a.input.read_text().splitlines()));checks=[inspect(r)for r in rows];out={'records':len(checks),'inputSHA256':hashlib.sha256(a.input.read_bytes()).hexdigest(),'recordsEvidence':checks,'scope':'Checks every parsed numeric function argument before symbolic evaluation. Does not replace source proof hypotheses or assert a new independent answer derivation. Categorical labels have explicitly separate scope.'};a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'records':len(checks),'numericOrTuple':sum(r['status']=='literal-domain-obligations-checked'for r in checks)}))
