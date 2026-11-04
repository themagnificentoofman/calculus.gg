"""Two actual item-scoped CC BY-SA 4.0 adaptations; no network or app imports."""
from __future__ import annotations
import json
from pathlib import Path
import sympy as s
from .common import package,tex,prose,eq,truth,digest

ROOT=Path(__file__).resolve().parent
CONTRACT=json.loads((ROOT/'adaptation-contract.json').read_text())
METADATA=[dict(familyId=p['destinationFamilyId'],topic='series',difficulty='medium',finiteInstanceIndices=[0],relatedIdeaGroupId=('alternating-series-error' if i==0 else 'integrated-exponential-Taylor'),primaryTechnique=('minimal-alternating-remainder' if i==0 else 'termwise-integration-and-radius'),difficultyRationale=p['centralDecision'],prerequisites=p['prerequisites'],sourceRecordIds=[p['sourceRecordId']]) for i,p in enumerate(CONTRACT['plannedPilot'])]
def catalog():return METADATA
def source(i):
    p=CONTRACT['plannedPilot'][i]
    return dict(kind='adapted',independentOriginal=False,thirdPartyProblemAdapted=True,sourceTextReused=True,
        sourceRecordId=p['sourceRecordId'],sourceItemLocator=p['sourceItemLocator'],sourceUrl=p['sourceUrl'],solutionUrl=p['solutionUrl'],solutionLocator=p['solutionLocator'],
        upstreamCreators=['Matthew Boelkins','David Austin','Christina Safranski','Steven Schlicker'],upstreamCopyright='©2012–2025 Matthew Boelkins',
        sourceTitle='Active Calculus (Single Variable), Second Edition',sourceLicense='CC-BY-SA-4.0',adapterLicense='CC-BY-SA-4.0',license='CC-BY-SA-4.0',licenseUrl=CONTRACT['licenseUrl'],licenseScope=CONTRACT['licenseScope'],
        attribution='Adapted from '+p['sourceItemLocator']+' of Active Calculus (Single Variable), Second Edition, by Matthew Boelkins with David Austin, Christina Safranski and Steven Schlicker. ©2012–2025 Matthew Boelkins. Source and this adapted mathematical content are licensed CC BY-SA 4.0. Adaptation by Calculus Ninja; AI-assisted review. No endorsement is implied.',
        modificationNotice='; '.join(p['modifications']),sourceInspectionEvidenceId=p['sourceRecordId']+'-inspection-2026-11-03',permissionEvidenceId='active-calculus-2e-native-activities-cc-by-sa-4.0-2026-11-03',reviewVersion='quality-series-adaptation-v1',humanReviewed=False)
def build(family_id,index):
    i=next((j for j,m in enumerate(METADATA) if m['familyId']==family_id),None)
    if i is None or type(index)is not int or index!=0:raise ValueError('unknown finite adapted instance')
    if i==0:
        statement=prose('Approximate the integral by the first N terms of the displayed series, beginning with ')+r'n=0'+prose('. What is the least positive integer N for which the alternating-series remainder bound guarantees absolute error less than the stated tolerance?')+r'\quad I=\int_0^1 e^{-x^2}\,\mathrm{d}x=\sum_{n=0}^{\infty}\frac{(-1)^n}{n!(2n+1)},\qquad\varepsilon=10^{-4}.'
        options=[('5','5','Use the factorial alone and miscount the included zero-index term'),('6','6','Return the last included index rather than the number of terms'),('7','7','correct'),('8','8','Add an unnecessary term after the first omitted term already satisfies the tolerance')]
        steps=[prose('Let ')+r'S_N'+prose(' include the terms with indices zero through N minus one. The first omitted magnitude is ')+r'b_N'+prose('.'),r'S_N=\sum_{n=0}^{N-1}\frac{(-1)^n}{n!(2n+1)},\qquad b_N=\frac1{N!(2N+1)}.',prose('The magnitudes decrease to zero. The alternating-series theorem therefore bounds the error by the first omitted magnitude.'),r'\frac{b_{n+1}}{b_n}=\frac{2n+1}{(n+1)(2n+3)}<1\quad(n\ge0),\qquad |I-S_N|\le b_N.',r'b_6=\frac1{9360}>10^{-4},\qquad b_7=\frac1{75600}<10^{-4}.',prose('Since these bounds decrease with N, every smaller positive N also fails the requested guarantee.'),r'N=7.',r'7']
        checks=[eq('first omitted magnitude N=6',1/(s.factorial(6)*13),s.Rational(1,9360)),eq('first omitted magnitude N=7',1/(s.factorial(7)*15),s.Rational(1,75600)),truth('strict tolerance separates consecutive counts',s.Rational(1,9360)>s.Rational(1,10000)>s.Rational(1,75600)),eq('source finite partial sum independently recomputed',sum((-1)**n/(s.factorial(n)*(2*n+1)) for n in range(7)),s.Rational(1614779,2162160))]
        cert=['Uniform convergence of the exponential series on [0,1] permits termwise integration. The displayed positive magnitude ratio is below one for every nonnegative integer n and tends to zero, so the alternating remainder theorem applies. The bound, not the actual numerical quadrature error, is minimized. The source answer-key denominator 756600 is corrected independently to 75600; its factorization and decimal support this correction.']
        return package(METADATA[i],0,statement,options,'7',steps,checks,cert,source(i))
    statement=r'\operatorname{erf}(x)=\frac2{\sqrt\pi}\int_0^x e^{-t^2}\,\mathrm{d}t=\sum_{k=0}^{\infty}a_kx^k.'+prose('For this Taylor series centered at zero, choose the ordered pair consisting of the coefficient of x to the seventh power and the radius of convergence R.')+r'\quad(a_7,R)=?'
    options=[('correct',r'\left(-\frac1{21\sqrt\pi},\ \infty\right)','correct'),('omit-integration',r'\left(-\frac1{3\sqrt\pi},\ \infty\right)','Omit division by the new power seven during integration'),('sign',r'\left(\frac1{21\sqrt\pi},\ \infty\right)','Lose the third alternating sign'),('radius',r'\left(-\frac1{21\sqrt\pi},\ 1\right)','Transfer the unit radius of a geometric series to an exponential series')]
    steps=[prose('The exponential series converges uniformly on every bounded real interval, so it may be integrated term by term.'),r'e^{-t^2}=\sum_{n=0}^{\infty}\frac{(-1)^nt^{2n}}{n!},\qquad \operatorname{erf}(x)=\frac2{\sqrt\pi}\sum_{n=0}^{\infty}\frac{(-1)^nx^{2n+1}}{n!(2n+1)}.',prose('The seventh power comes from index three. Its coefficient retains both the factorial and the integration factor.'),r'a_7=\frac{2(-1)^3}{\sqrt\pi\,3!\,7}=-\frac1{21\sqrt\pi}.',prose('For any fixed nonzero x, the ratio of successive nonzero term magnitudes tends to zero. At zero convergence is immediate, so the radius is infinite.'),r'\frac{|x|^2(2n+1)}{(n+1)(2n+3)}\longrightarrow0,\qquad (a_7,R)=\left(-\frac1{21\sqrt\pi},\ \infty\right).',r'\left(-\frac1{21\sqrt\pi},\ \infty\right)']
    x=s.symbols('x');n=s.symbols('n',integer=True,positive=True)
    checks=[eq('coefficient checked by differentiating defining derivative six times',s.diff(2*s.exp(-x*x)/s.sqrt(s.pi),x,6).subs(x,0)/s.factorial(7),-1/(21*s.sqrt(s.pi))),eq('ratio limit',s.limit(x*x*(2*n+1)/((n+1)*(2*n+3)),n,s.oo),0)]
    return package(METADATA[i],0,statement,options,'correct',steps,checks,['Entire exponential Taylor convergence gives uniform convergence on compact intervals. Termwise integration preserves the odd-power series; the independent derivative of the defining integrand checks the seventh coefficient without reusing the integrated-series formula.'],source(i))
def verification_report(record):
    """Independent finite mathematical checks, separate from record reconstruction."""
    fid=record['familyId'];out=[]
    if fid==METADATA[0]['familyId']:
        from fractions import Fraction
        import math
        bounds=[Fraction(1,math.factorial(N)*(2*N+1)) for N in range(1,9)]
        out.append(truth('independent exact first passing remainder count',next(N for N,v in enumerate(bounds,1) if v<Fraction(1,10000))==7))
        out.append(truth('independent rational partial sum',sum(Fraction((-1)**n,math.factorial(n)*(2*n+1)) for n in range(7))==Fraction(1614779,2162160)))
    elif fid==METADATA[1]['familyId']:
        x=s.symbols('x');series=s.series(s.erf(x),x,0,8).removeO()
        out.append(eq('independent symbolic erf series coefficient',series.coeff(x,7),-1/(21*s.sqrt(s.pi))))
        n=s.symbols('n',integer=True,positive=True)
        out.append(eq('independent factorial-coefficient ratio limit',s.limit(s.factorial(n)*(2*n+1)/(s.factorial(n+1)*(2*n+3)),n,s.oo),0))
    else:raise ValueError('unknown adaptation')
    correct=next(c for c in record['choices'] if c['choiceId']==record['answerChoiceId'])
    out.append(truth('correct displayed choice matches derived result',correct['math']==('7' if fid==METADATA[0]['familyId'] else r'\left(-\frac1{21\sqrt\pi},\ \infty\right)')))
    return {'status':'passed','checks':out,'limitations':'Finite algebra and coefficient checks executed; convergence justifications are the recorded analytic proof, not a formal proof. AI review, not human certification.'}
def verify(record):
    result=verification_report(record)
    return result.get('status')=='passed' and bool(result.get('checks')) and all(c.get('passed') is True for c in result['checks'])

if __name__=='__main__':
    rows=[build(m['familyId'],0) for m in catalog()];reports=[dict(problemId=r['problemId'],contentHash=r['contentHash'],verification=verification_report(r)) for r in rows]
    (ROOT/'adapted-pilot.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
    (ROOT/'adapted-pilot-verification.json').write_text(json.dumps({'items':reports,'imported':0,'active':0,'sourceDigest':digest(Path(__file__).read_text())},indent=2)+'\n')
    print(json.dumps({'authored':len(rows),'independentlyVerified':len(reports),'imported':0,'active':0}))
