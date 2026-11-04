"""Proposed selector patch for parent review; does not edit frozen modules.

Add select_authored_triple after de-duplicating the authored pool, then keep the
existing pairwise symbolic inequivalence checks on its returned expressions.
Numerical ordering is solely an editorial sampling criterion, never a proof.
"""
import hashlib,itertools,json
import sympy as s

def _digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def numeric_key(value):
 values=list(value) if isinstance(value,s.Tuple) else [value]
 return tuple(s.N(v,90) for v in values)

def select_authored_triple(answer,clean,m,structure):
 """Select from every 3-subset, cycling all feasible correct-answer ranks."""
 akey=numeric_key(answer);buckets={}
 for combination in itertools.combinations(clean,3):
  rank=sum(bool(numeric_key(w)<akey) for w,_ in combination)
  buckets.setdefault(rank,[]).append(combination)
 assert buckets,'need three authored inequivalent distractors'
 ranks=sorted(buckets) # Every feasible count from 0,1,2,3 is retained.
 index=int(m)-4
 target=ranks[(index+int(_digest(structure)[:8],16))%len(ranks)]
 candidates=buckets[target]
 chosen=candidates[(index+int(_digest([structure,target])[8:16],16))%len(candidates)]
 return list(chosen)

def supplement_differentiation_pool(structure,m,pool):
 """Authored errors supplying the previously absent scalar-minimum rank.

All four scalar families now have >=3 higher and >=3 lower wrong answers on
m=4..11. The regularity pair family is unchanged. Existing choices remain.
"""
 pool=list(pool)
 if structure=='sharp-uniform-polynomial-endpoint-derivative':
  pool.append((2**(m-1)*m*m,'Multiply by the Chebyshev leading coefficient despite the unit uniform norm'))
 elif structure=='cycle-Laplacian-second-diagonal-determinant-derivative':
  pool.append((m**3*(m*m-1)/6,'Count the cyclic starting-vertex factor twice'))
 elif structure=='Newton-three-compositions-first-surviving-eighth-derivative':
  pool.append((s.factorial(8)*((m-1)/2)**15,'Perform a fourth Newton error update while retaining the eighth-derivative factorial'))
 elif structure=='second-Leibniz-derivative-collapsing-moving-interval':
  pool.extend([((2*m*m+3*m-5)*s.E,'Differentiate only the exponential numerator of the closed integral and omit derivatives of the factor one over x'),((2*m*m+2*m-4)*s.E,'Count the remaining integral moving-boundary contribution twice')])
 return pool
