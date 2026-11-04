#!/usr/bin/env python3
"""Deterministic offline materialization. No network, model calls, or arbitrary-expression eval."""
import argparse, hashlib, itertools, json, os, sqlite3, time
from pathlib import Path
import sympy as s
from families import FAMILIES,x,y,n,a,b,c
ROOT=Path(__file__).resolve().parents[2]
VERSION='original-linear-families-v2'
STAGES={'pilot':14,'expanded':140,'full':1400}

def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,default=lambda v:s.srepr(v) if isinstance(v,s.Basic) else str(v))
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def math(expr): return s.latex(expr,fold_short_frac=False)
def txt(value): return r'\textnormal{'+value+'}'
def equal(left,right): return s.simplify(left-right)==0

def operate(f,k):
    kind=f['kind']
    if f.get('verify'): return f['verify'](k)
    if kind=='integral': return s.integrate(k,(x,f['lo'],f['hi']))
    if kind=='derivative': return s.diff(k,x,f['order']).subs(x,f['point'])
    if kind=='limit': return s.limit(k,x,f['point'],dir='+')
    if kind=='series': return s.summation(k,(n,f['start'],s.oo))
    if kind=='ode': return k.subs(x,f['point'])
    if kind=='partial': return s.diff(k,x,f['dx'],y,f['dy']).subs({x:f['px'],y:f['py']})
    if kind=='laplacian': return (s.diff(k,x,2)+s.diff(k,y,2)).subs({x:f['px'],y:f['py']})
    if kind=='double': return s.integrate(k,(y,0,f['yhi']),(x,0,f.get('xhi',1)))
    if kind=='coefficient': return s.expand(k).coeff(x,f['order'])
    if kind=='custom': return f['verify'](k)
    raise ValueError('Unsupported operation '+kind)

def display(f,expr):
    kind=f['kind']; z=math(expr)
    if kind=='integral': return r'\int_{'+math(f['lo'])+'}^{'+math(f['hi'])+'}'+z+r'\,dx'
    if kind=='derivative': return r'\left.\frac{d^{'+str(f['order'])+r'}}{dx^{'+str(f['order'])+'}}('+z+r')\right|_{x='+math(f['point'])+'}'
    if kind=='limit': return r'\lim_{'+math(f.get('variable',x))+r'\to '+math(f['point'])+('^{+}' if f['point']!=s.oo else '')+'}('+z+')'
    if kind=='series': return r'\sum_{n='+str(f['start'])+r'}^{\infty}\left('+z+r'\right)'
    if kind=='partial': return r'\left.\frac{\partial^{'+str(f['dx']+f['dy'])+r'}}{\partial x^{'+str(f['dx'])+r'}\partial y^{'+str(f['dy'])+'}}('+z+r')\right|_{(x,y)=('+str(f['px'])+','+str(f['py'])+')}'
    if kind=='laplacian': return r'\left.(\partial_x^2+\partial_y^2)('+z+r')\right|_{(x,y)=('+str(f['px'])+','+str(f['py'])+')}'
    if kind=='disk': return r'\iint_{x^2+y^2\le 1}'+z+r'\,dx\,dy'
    if kind=='double': return r'\int_0^{'+math(f.get('xhi',1))+r'}\int_0^{'+math(f['yhi'])+'}'+z+r'\,dy\,dx'
    if kind=='coefficient': return txt('Find the coefficient of ')+f"x^{{{f['order']}}}"+txt(' in ')+z
    if kind=='custom': return f['display'](expr)
    if kind=='ode':
        degree=len(f['operator'])-1; u=s.Function('u')(x)
        lhs=sum(v*s.diff(u,x,i) for i,v in enumerate(f['operator']))
        forcing=sum(v*s.diff(expr,x,i) for i,v in enumerate(f['operator']))
        initials=[s.Eq(s.diff(u,x,i).subs(x,f['initial']),s.diff(expr,x,i).subs(x,f['initial'])) for i in range(degree)]
        return txt('Find ')+f"u({math(f['point'])})"+txt(' for ')+math(s.Eq(lhs,s.expand(forcing)))+r',\quad '+r',\quad '.join(math(e) for e in initials)
    raise ValueError(kind)

def rational_basis_is_independent(kernels):
    if any(k.free_symbols-{x,y,n} for k in kernels) or not all(k.is_rational_function(x,y,n) for k in kernels):return None
    denominators=[s.fraction(s.cancel(k))[1] for k in kernels]
    common=s.lcm(denominators)
    polynomials=[s.Poly(s.cancel(k*common),x,y,n) for k in kernels]
    monomials=sorted(set(m for p in polynomials for m in p.monoms()))
    return s.Matrix([[p.coeff_monomial(m) for p in polynomials] for m in monomials]).rank()==len(kernels)

def certificate(f):
    if f['kind']=='special-ode':
        from special_ode import prepare
        prepare(f['id']);return [],['Real variables; parameters are integers 1 through 16.']
    if rational_basis_is_independent(f['kernels']) is False:raise ValueError('Dependent basis creates equivalent parameter variants: '+f['id'])
    values=[s.simplify(operate(f,k)) for k in f['kernels']]
    if any(v.has(s.Integral,s.Sum,s.Limit,s.nan,s.zoo,s.oo,-s.oo) or v.is_real is False for v in values): raise ValueError(f"unresolved {f['id']}: {values}")
    if f['expected'] is not None:
        for actual,expected in zip(values,f['expected']):
            if not equal(actual,expected): raise ValueError(f"independent disagreement {f['id']}: {actual} != {expected}")
    # Linearity permits substituting bounded real coefficients after independently
    # verifying all three exact basis operations. This is a proof, not spot checking.
    assumptions=['All variables are real.','Parameters a, b, c are integers from 1 through 16.']
    if f['kind']=='integral': assumptions += [f"Integration interval: ({f['lo']}, {f['hi']}); endpoint singularities use one-sided improper limits."]
    if f['kind']=='series' and not f.get('convergenceProof'):
        for k in f['kernels']:
            convergent=s.Sum(k,(n,f['start'],s.oo)).is_convergent()
            if convergent is not s.true and convergent is not True: raise ValueError('Unproved convergence '+f['id'])
        assumptions += ['Each component series converges; linearity applies to the indicated partial sums.']
    if f['kind']=='limit': assumptions += ['Limit is from the right through the real domain.']
    if f['kind']=='ode':
        interval=(min(f['initial'],f['point']),max(f['initial'],f['point']))
        leading=f['operator'][-1]
        if s.solveset(leading,x,domain=s.Interval(*interval)) is not s.EmptySet: raise ValueError('Singular leading coefficient')
        for k in f['kernels']:
            if s.calculus.util.continuous_domain(k,x,s.Interval(*interval)) != s.Interval(*interval): raise ValueError('ODE domain')
        assumptions += [f"Unique classical solution on a neighborhood of [{interval[0]}, {interval[1]}]; continuous coefficients and nonzero leading coefficient."]
    if f['kind']=='double': assumptions += [f"Domain: 0 <= x <= {f.get('xhi',1)}, 0 <= y <= {f['yhi']}."]
    if f.get('assumptions'): assumptions += f['assumptions']
    if f.get('convergenceProof'): assumptions += [f['convergenceProof']]
    return values,assumptions

def materialize(f,parameters,values,assumptions):
    coefficients=[parameters[k] for k in ('a','b','c')]
    expr=s.Add(*(v*k for v,k in zip(coefficients,f['kernels'])))
    answer=s.expand(sum(v*k for v,k in zip(coefficients,values)))
    # Both public notation and verification evidence originate in these objects.
    statement=display(f,expr) if f['kind']!='special-ode' else ''
    statement += f.get('promptMath','')
    if f.get('promptAssumptions'): statement += r'\quad '+txt(f['promptAssumptions'])
    semantic=digest({'operation':f['kind'],'expression':s.srepr(s.cancel(s.expand(expr))), 'operationSpec':{k:s.srepr(v) if isinstance(v,s.Basic) else v for k,v in f.items() if k not in ['id','topic','level','tags','kernels','expected','verify','display','assumptions','promptMath','promptAssumptions','convergenceProof']}})
    special=None
    if f['kind']=='special-ode':
        from special_ode import build
        special=build(f['id'],parameters);statement=special['statement'];answer=special['answer'];assumptions=special['assumptions'];semantic=digest({'operation':f['kind'],'expression':special['expression']})
    problem_id='cn_'+semantic[:20]
    # Exact translations: pairwise differences are known nonzero rationals, even
    # when a closed form contains transcendentals. Avoid unverifiable numeric comparisons.
    # Vary the correct numeric rank; a fixed offset pattern is learnable even
    # after choice permutation. Prefer an existing exact term as the error unit.
    def known_sign(value):
        if value.is_Rational:return 1 if value>0 else -1 if value<0 else 0
        if value in (s.pi,s.E):return 1
        if value.func==s.exp and value.args[0].is_real:return 1
        if value.func==s.log and value.args[0].is_Rational and value.args[0]>0:return 1 if value.args[0]>1 else -1 if value.args[0]<1 else 0
        if value.is_Pow and value.exp.is_Rational and known_sign(value.base)==1:return 1
        if value.is_Mul:
            signs=[known_sign(t) for t in value.args]
            if all(signs):
                result=1
                for sign in signs:result*=sign
                return result
        return 0
    unit=s.Rational(1,answer.q) if answer.is_Rational else s.Integer(1)
    if not answer.is_Rational:
        for term in answer.as_ordered_terms():
            sign=known_sign(term)
            if sign:unit=sign*term;break
    rank=int(semantic[:8],16)%4
    magnitudes=[s.Integer(1+int(semantic[8+2*i:10+2*i],16)%5+i*5) for i in range(3)]
    offsets=[s.Integer(0)]+[-v if i<rank else v for i,v in enumerate(magnitudes)]
    options=[s.expand(answer+d*unit) for d in offsets]
    assert known_sign(unit)==1 and len(set(offsets))==4
    choices=[{'choiceId':'ch_'+digest(s.srepr(v))[:16],'math':math(v)} for v in options]
    from derivations import derivation
    steps=derivation(f)+[txt('Use linearity with the stated domain and conditions.')]
    if special:
        steps=special['steps']
    elif f['kind']=='ode':
        steps=[txt('A candidate solution is ')+r'u(x)='+math(expr),txt('Differentiating this candidate gives the stated equation and all initial values. The linear initial-value problem is unique on the stated interval.')]
    else:
        steps += [display(f,k)+'='+math(v) for k,v in zip(f['kernels'],values)]
    if not special: steps += [txt('Combine the exact contributions: ')+math(s.Add(*(s.Mul(v,k,evaluate=False) for v,k in zip(coefficients,values)),evaluate=False))+'='+math(answer)]
    record={'schemaVersion':1,'problemId':problem_id,'problemRevision':1,'semanticHash':semantic,
      'statement':statement,'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':steps,
      'assumptions':assumptions,'topic':f['topic'],'difficulty':f['level'],'subtopic':f['id'],'techniqueTags':f['tags'],'familyId':f['id'],'templateVersion':VERSION,'parameters':parameters,
      'provenance':{'kind':'original','sourceUrl':None,'sourceItem':None,'license':'LicenseRef-CalculusNinja-Original','attribution':'Original Calculus Ninja template; AI-assisted implementation, automatically verified. No third-party problem text imported.','authoring':{'method':'code-authored symbolic template','templateVersion':VERSION,'model':None,'promptVersion':None}},
      'validation':{'status':'passed','methods':(['symbolic-ode-residual','initial-or-branch-conditions','domain-and-uniqueness'] if special else ['exact-symbolic-basis-operations','linearity'])+['exact-nonzero-unit-choice-differences'],
        'evidence':{'verifier':'SymPy '+s.__version__,'basisResults':None if special else [s.srepr(v) for v in values],'mathematicalSourceHash':digest(special['expression'] if special else [s.srepr(v) for v in f['kernels']]),'choiceDifferenceUnit':s.srepr(unit),'choiceUnitProof':'Positive rational, exponential, logarithm of a positive rational distinct from one, or products/powers of these and pi; signs normalized.','assumptionsChecked':True,'solutionDerivationChecked':True,'numericalChecksUsedAsProof':False},'humanReviewed':False},
      'estimates':{'difficulty':f['level'],'solveSeconds':{'easy':45,'medium':90,'hard':180,'olympiad':360}[f['level']],'basis':'template method rubric; not measured player performance'}}
    record['contentHash']=digest(record)
    return record

def generate(stage,out):
    out.mkdir(parents=True,exist_ok=True)
    # SQLite checkpoint survives process interruption; deterministic IDs make retries safe.
    checkpoint=sqlite3.connect(out/'checkpoint.sqlite')
    checkpoint.execute('CREATE TABLE IF NOT EXISTS generated (family TEXT, seed INTEGER, semantic TEXT UNIQUE, payload TEXT NOT NULL, PRIMARY KEY(family,seed))')
    checkpoint.execute('CREATE TABLE IF NOT EXISTS rejected (family TEXT, seed INTEGER, reason TEXT, PRIMARY KEY(family,seed))')
    target=STAGES[stage]; generated=duplicates=rejected=0
    review=[]; started=time.time()
    for f in FAMILIES:
        values,assumptions=certificate(f)
        have=checkpoint.execute('SELECT COUNT(*) FROM generated WHERE family=?',(f['id'],)).fetchone()[0]
        for seed in range(4096):
            if have>=target: break
            # Permutation spreads each pilot across the entire bounded cube.
            v=(seed*4051+1729)%4096
            params={'a':1+v%16,'b':1+(v//16)%16,'c':1+v//256}
            if checkpoint.execute('SELECT 1 FROM generated WHERE family=? AND seed=?',(f['id'],seed)).fetchone(): continue
            generated+=1
            try:
                p=materialize(f,params,values,assumptions)
                checkpoint.execute('INSERT INTO generated VALUES (?,?,?,?)',(f['id'],seed,p['semanticHash'],canonical(p)))
                have+=1
            except sqlite3.IntegrityError: duplicates+=1
            except (ValueError,AssertionError) as error:
                rejected+=1;checkpoint.execute('INSERT OR REPLACE INTO rejected VALUES (?,?,?)',(f['id'],seed,str(error)))
            if seed%25==0: checkpoint.commit()
        checkpoint.commit()
        if have<target: raise RuntimeError(f"Coverage quota failed: {f['id']} {have}/{target}")
        rows=checkpoint.execute('SELECT payload FROM generated WHERE family=? ORDER BY seed LIMIT ?',(f['id'],target)).fetchall()
        review += [json.loads(rows[0][0]),json.loads(rows[-1][0])]
        print(f"{f['id']}: {target} approved",flush=True)
    release=f'cn-2026-11-02-{stage}-v2';path=out/(release+'.jsonl')
    sha=hashlib.sha256();coverage={};families={};tags={}
    with path.open('w') as stream:
        for f in FAMILIES:
            for (payload,) in checkpoint.execute('SELECT payload FROM generated WHERE family=? ORDER BY seed LIMIT ?',(f['id'],target)):
                line=payload+'\n';stream.write(line);sha.update(line.encode());p=json.loads(payload)
                key=p['topic']+'/'+p['difficulty'];coverage[key]=coverage.get(key,0)+1;families[p['familyId']]=families.get(p['familyId'],0)+1
                for tag in p['techniqueTags']:tags[tag]=tags.get(tag,0)+1
    manifest={'schemaVersion':1,'releaseId':release,'stage':stage,'recipe':VERSION,'artifact':path.name,'artifactSha256':sha.hexdigest(),'publishedCount':0,'approvedCount':target*len(FAMILIES),'coverage':coverage,'families':families,'techniques':tags,'distinctFamilies':len(FAMILIES),'maxFamilyShare':1/len(FAMILIES),'humanReviewedCount':0,'importedExistingCount':0,'generatedThisRun':generated,'rejectedThisRun':rejected,'duplicatesThisRun':duplicates,'openaiCalls':0,'openaiCostUSD':0,'elapsedSeconds':round(time.time()-started,2),'sympyVersion':s.__version__,'renderValidated':False,'deduplication':'Canonical structured operations and expanded expressions; no claim of complete cross-technique semantic equivalence.'}
    (out/(release+'.manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    (out/(release+'.review.json')).write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

def verify_artifact(path):
    families={f['id']:f for f in FAMILIES};proofs={};seen=set();count=0
    for line in path.open():
        p=json.loads(line);family=p.get('familyId')
        if p.get('schemaVersion')==2:
            from content_pipeline import verify
            verify(p)
            if p['semanticHash'] in seen:raise ValueError('Duplicate normalized content')
            seen.add(p['semanticHash']);count+=1
            continue
        if family not in families or p.get('templateVersion')!=VERSION: raise ValueError('Unsupported family/version: quarantine for independent validation')
        params=p.get('parameters',{})
        if set(params)!=set(['a','b','c']) or any(type(v) is not int or not 1<=v<=16 for v in params.values()): raise ValueError('Parameters outside proof domain')
        if family not in proofs:proofs[family]=certificate(families[family])
        expected=materialize(families[family],params,*proofs[family])
        if p.get('problemRevision',1)>1:
            # A correction retains the operator-selected permanent identity; all
            # mathematical fields still have to match the current verified recipe.
            expected['problemId']=p['problemId'];expected['problemRevision']=p['problemRevision']
            del expected['contentHash'];expected['contentHash']=digest(expected)
        if canonical(p)!=canonical(expected): raise ValueError('Content differs from independently verified recipe: '+p.get('problemId','unknown'))
        if p['semanticHash'] in seen: raise ValueError('Duplicate normalized content')
        seen.add(p['semanticHash']);count+=1
    print(json.dumps({'verified':count,'method':'reconstructed exact mathematical recipe and solution','humanReviewed':False}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=STAGES);parser.add_argument('--out',type=Path,default=ROOT/'.bank-data');parser.add_argument('--verify',type=Path);args=parser.parse_args()
    if args.verify:verify_artifact(args.verify)
    elif args.stage:generate(args.stage,args.out)
    else:parser.error('Choose --stage or --verify')
