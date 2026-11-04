"""Portable content packaging. Admission is owned by the independent release gate."""
from __future__ import annotations
import hashlib,itertools,json
import sympy as s
OPTION_AUDITS={}

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def tex(value):
    return s.latex(s.sympify(value)).replace(r'\log',r'\ln').replace(r'\operatorname{asin}',r'\arcsin').replace(r'\operatorname{atan}',r'\arctan')
def prose(value):
    assert not any(c in value for c in ['_','^','\\']),('mathematics belongs outside prose',value)
    return r'\textnormal{'+value+'}'
def eq(name,left,right=0):
    residual=s.simplify(left-right)
    assert (residual.is_zero_matrix is True if isinstance(residual,s.MatrixBase) else residual==0),(name,residual)
    return {'name':name,'kind':'exact-algebra','passed':True}
def truth(name,condition):
    assert bool(condition),name
    return {'name':name,'kind':'exact-inequality-or-finite-identity','passed':True}
def numeric_options(answer,pool,index,shape):
    """Every option is an authored mistake; balancing cannot invent offsets."""
    answer=s.sympify(answer);clean=[]
    for value,reason in pool:
        value=s.sympify(value)
        if value.has(s.nan,s.zoo,s.oo,-s.oo) or value.is_real is False:continue
        if s.simplify(value-answer)==0 or any(s.simplify(value-v)==0 for v,_ in clean):continue
        clean.append((value,reason))
    buckets={}
    for triple in itertools.combinations(clean,3):
        rank=sum(bool(s.N(v,75)<s.N(answer,75)) for v,_ in triple)
        buckets.setdefault(rank,[]).append(triple)
    assert buckets,shape
    ranks=sorted(buckets);rank=ranks[(index+int(digest(shape)[:8],16))%len(ranks)]
    bucket=buckets[rank];triple=bucket[(index+int(digest([shape,rank])[8:16],16))%len(bucket)]
    vals=[(answer,'correct')]+list(triple)
    for (a,_),(b,_) in itertools.combinations(vals,2):
        d=s.simplify(a-b)
        assert d.is_zero is False or d.equals(0) is False,(shape,'unresolved equality',a,b)
    opts=[(s.srepr(v),tex(v),reason) for v,reason in vals]
    key=digest([[(code,math) for code,math,_ in opts],s.srepr(answer)])
    OPTION_AUDITS[key]={'correctNumericRank':rank,'feasibleCorrectRanks':ranks,'valuesByChoiceId':{'ch_'+digest(s.srepr(v))[:16]:float(s.N(v,30)) for v,_ in vals},'scope':'ordering diagnostic only; never proof of exact equality or correctness'}
    return opts,s.srepr(answer)
def package(meta,index,statement,options,correct,steps,checks,certificate,source=None,parameters=None,lineage=None):
    assert len(options)==4 and len({v[0] for v in options})==4
    assert sum(v[0]==correct for v in options)==1 and checks and all(c['passed'] for c in checks)
    choices=[{'choiceId':'ch_'+digest(code)[:16],'math':math,'misconception':why} for code,math,why in options]
    shift=int(digest([meta['familyId'],index])[:8],16)%4;choices=choices[shift:]+choices[:shift]
    key={'constructorVersion':'quality-series-v1','familyId':meta['familyId'],'instanceIndex':index,'parameters':parameters or {}}
    row=dict(meta,statement=statement,choices=choices,answerChoiceId='ch_'+digest(correct)[:16],solutionSteps=steps,parameters=parameters or {},instanceIndex=index,
        schemaVersion=2,problemId='cn_qs_'+digest(key)[:20],problemRevision=1,semanticHash=digest({'family':meta['familyId'],'statement':statement}),
        automatedChecks=checks,analyticCertificate=certificate,source=source or {'kind':'independently-authored','independentOriginal':True,'thirdPartyProblemAdapted':False,'license':'LicenseRef-CalculusNinja-Original','attribution':'Original Calculus Ninja content; AI-assisted mathematical and editorial review.'},
        validation={'status':'candidate-independently-checkable','humanReviewed':False,'formalProof':False,'analyticCertificateMachineProved':False,'numericalAgreementUsedAsProof':False},
        review={'status':'pending-independent-cross-review','notationVersion':'calculus-ninja-notation-v1','solutionVersion':'worked-solutions-v1','reviewVersion':'quality-series-v1'},
        lineage=lineage or {'relationship':'new-construction'})
    row['pedagogy']={k:meta[k] for k in ('relatedIdeaGroupId','primaryTechnique','difficultyRationale','prerequisites')}
    row['pedagogy'].update(constructionId=meta['familyId'],responseFormat='multiple-choice',reasoningDemand=['recognition'] if meta['difficulty']=='easy' else ['method-selection','synthesis'],alternativeTechniques=[],sourceRecordIds=meta.get('sourceRecordIds',[]),structuralSignature=meta['familyId'],answerForm='exact-expression')
    row['optionAudit']=OPTION_AUDITS.get(digest([[(code,math) for code,math,_ in options],correct]),{'correctNumericRank':None,'scope':'categorical or extended-real choices; numeric-rank heuristic is not applicable'})
    if row['source']['kind']=='adapted':row['provenance']=dict(row['source'])
    row['contentHash']=digest(row)
    return row
