"""Bounded, source-bound grouping recommendations; no serving-map mutation."""
import argparse, collections, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(x): return hashlib.sha256(x.encode()).hexdigest()
def artifact(p): return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def load(p):
    r=[json.loads(x)for x in p.read_text().splitlines()]if p.suffix=='.jsonl'else json.loads(p.read_text())
    return r if isinstance(r,list)else r['records']

# Existing descriptive labels, restricted to a reviewed construction. These are
# aliases for its current method, not invented additional methods or ideas.
METHOD_TARGETS={
'm3-integration-easy-absolute-area':'split-at-zero',
'm3-integration-easy-piecewise-accumulation':'interval-decomposition',
'm3-integration-hard-beta-polynomial':'beta-integral',
'm3-integration-hard-half-angle-quadratic':'half-angle-substitution',
'm3-integration-medium-exponential-trig':'integration-by-parts',
'm3-integration-medium-piecewise-absolute-root':'split-at-root',
'm3-integration-easy-accumulation-from-derivative':'fundamental-theorem-of-calculus',
'm3-integration-hard-Frullani-rectangle':'Tonelli-parameterization',
'm3-integration-hard-improper-rational-beta':'rational-substitution',
'm3-integration-hard-logarithmic-moment':'integration-by-parts',
'm3-integration-medium-inverse-tangent':'completing-the-square',
'm3-integration-medium-trig-odd-power':'trig-substitution',
'm3-series-easy-arithmetic-triangle':'pairing',
'm3-series-easy-ratio-test-data':'ratio-test',
'm3-series-medium-weighted-geometric':'differentiate-geometric-series',
'm3-series-medium-exponential-Taylor':'Taylor-recognition',
'm3-series-medium-cosine-series':'parity-filter',
'm3-series-medium-weighted-binomial-total':'differentiate-binomial-theorem',
'm3-series-hard-harmonic-generating':'interchange-positive-sums',
'm3-series-hard-Catalan-generating':'quadratic-generating-function',
'm3-series-medium-negative-binomial':'binomial-series',
'm3-series-hard-borderline-exponential-comparison':'second-order-log-and-limit-comparison',
'm3-series-medium-integral-tail-bound':'comparison-integral',
'm3-series-medium-alternating-error':'Leibniz-remainder',
'm3-series-hard-floor-geometric-count':'Tonelli-counting',
'm3-series-hard-dyadic-infinite-product':'finite-product-induction',
'm3-series-medium-quadratic-weight':'differentiate-generating-function',
'm3-series-easy-power-series-radius':'ratio-test',
'm3-series-medium-power-series-ratio-radius':'ratio-test',
'm3-series-easy-nth-term-test':'nth-term-test',
'm3-multivariable-easy-partial-hold-fixed':'partial-differentiation',
'm3-multivariable-easy-mixed-partial':'partial-differentiation',
'm3-multivariable-easy-linearization-two-inputs':'local-linear-approximation',
'm3-multivariable-easy-triangular-region':'variable-boundary',
'm3-multivariable-easy-chain-curve':'chain-rule',
'm3-multivariable-easy-divergence':'sum-coordinate-derivatives',
'm3-multivariable-medium-change-order':'changing-order-of-integration',
'm3-multivariable-medium-ellipse-transform':'change-of-variables',
'm3-multivariable-medium-surface-graph-area':'cross-product-Jacobian',
'm3-multivariable-medium-spherical-moment':'radial-volume-Jacobian',
'm3-multivariable-hard-quadratic-eigenconstraint':'eigenvalue-optimization',
'm3-multivariable-hard-moving-domain-derivative':'differentiate-transformed-domain',
'm3-multivariable-hard-ellipsoid-inertia':'affine-transform-and-symmetry',
'm3-multivariable-hard-simplex-beta':'beta-integral',
'm3-multivariable-hard-Stokes-tilted-surface':'Stokes-theorem',
'm3-multivariable-hard-boundary-versus-interior':'boundary-critical-analysis',
'm3-multivariable-hard-mixed-Hessian-coordinate':'chain-rule',
'm3-multivariable-hard-Gaussian-precision':'completing-the-square',
'm3-differential-equations-easy-primitive-initial-value':'integrate-and-use-initial-value',
'm3-differential-equations-easy-doubling-data':'multiplicative-growth',
'm3-differential-equations-easy-cooling-limit':'equilibrium-plus-decay',
'm3-differential-equations-easy-mixing-inflow':'inflow-minus-outflow',
'm3-differential-equations-easy-constant-acceleration':'two-integrations',
'm3-differential-equations-easy-transfer-conservation':'conservation-laws',
'm3-differential-equations-medium-logistic-hitting':'separation-and-log-odds',
'm3-differential-equations-medium-bernoulli-reciprocal':'reciprocal-substitution',
'm3-differential-equations-medium-homogeneous-ratio':'scale-ratio-substitution',
'm3-differential-equations-medium-harvest-bifurcation':'completing-the-square',
'm3-differential-equations-medium-critical-damping':'discriminant-condition',
'm3-differential-equations-hard-riccati-particular':'subtract-particular-solution',
'm3-differential-equations-hard-remove-first-derivative':'Gaussian-conjugation',
'm3-differential-equations-hard-rotating-linear-system':'linear-systems',
'm3-differential-equations-hard-jordan-system':'linear-systems',
'm3-differential-equations-hard-linear-stability-bound':'trace-determinant',
'm3-differential-equations-easy-oscillator-initial-data':'initial-data-in-basis',
'm3-differential-equations-hard-euler-cauchy-resonance':'log-time-substitution',
'm3-differential-equations-hard-nonlinear-energy-speed':'energy-first-integral',
'm3-differential-equations-hard-wronskian-transport':'determinant-differentiation',
'm3-differential-equations-medium-distinct-characteristic-roots':'characteristic-equation',
'm3-multivariable-hard-nonconservative-hole':'winding-number',
'm3-multivariable-hard-surface-flux-graph':'normal-area-vector',
'm3-multivariable-medium-Green-circulation':'Green-theorem',
'm3-multivariable-medium-divergence-flux':'divergence-theorem',
}
RELATED=[
('peano-kernel-sharp-error',['peano-kernel-sharp-error','Peano-kernel-total-variation'],
 'Both derive an affine-exact quadrature error as an integral against f″, integrate the absolute Peano kernel and justify sharpness by its sign. Two-interior-node versus three-node/endpoints rules and explicit attainment outputs are distinct constructions and tasks.'),
('hilbert-schur-sharpness',['hilbert-schur-sharpness','sharp-Hilbert-series-inequality'],
 'Both establish a sharp homogeneous Hilbert-kernel operator bound using weighted correlation/Schur estimates and long logarithmic-scale extremizing sequences. Continuous quadratic and discrete asymmetric bilinear problems remain distinct constructions.'),
('hilbert-moment-projection',['hilbert-moment-projection','Hilbert-sequence-two-moment-projection','Gram-moment-projection'],
 'The decisive minimization in all three is the inverse Gram matrix of two independent moment vectors and an orthogonal-remainder proof. Polynomial integral moments, weighted sequence moments and Duhamel endpoint moments are distinct literal tasks.'),
('Hilbert-representer-sharp-functional',['Hilbert-representer-sharp-functional','derivative-functional-Hilbert-space-norm'],
 'The sharp linear-functional norm is obtained by finding its Hilbert-space representer and proving equality in Cauchy-Schwarz. Polynomial derivative, harmonic boundary Fourier and Poisson/Dirichlet-energy spaces require distinct constructions; this does not collapse them into the two-constraint minimum-energy family.'),
('abel-integral-inversion',['abel-integral-inversion','inverse-period-Abel-potential'],
 'Compose the inverse-square-root convolution and use the constant Beta kernel. The ODE family first derives the period-energy Abel transform and imposes evenness; its energy-to-turning-coordinate output differs from recovering a density derivative or total integral.'),
('roots-of-unity-filter',['root-of-unity-filter-derivatives','roots-of-unity-series'],
 'The same finite cyclic filter selects one congruence class of Taylor coefficients. Derivative extraction at zero and evaluating the full filtered exponential series remain distinct tasks. This alias is a shared parent only and adds no idea.'),
('Gibbs-relative-entropy-extremality',['Gibbs-relative-entropy-extremality','countable-Gibbs-entropy-extremum'],
 'Match prescribed moments with a Gibbs law and prove extremality using nonnegative relative entropy. Countable entropy needs tail coarsening; continuous Gaussian entropy needs covariance matching. Preserve these proof obligations and structures.'),
('envelope-theorem',['envelope-theorem','implicit-optimizer-envelope-jet'],
 'Both differentiate an optimum through the stationary minimizer relation. Higher implicit jets add work but do not make the envelope identity unrelated. First-derivative and fourth-derivative constructions and normalized tasks remain separate.'),
('Osgood-integral-criterion',['Osgood-integral-blowup-threshold','Osgood-integral-uniqueness'],
 'Both use the reciprocal vector-field integral as the escape-time criterion. Integrability near a zero controls waiting-time nonuniqueness; integrability toward infinity controls finite-time uniform bounds. Distinct endpoints, conclusions and structures are preserved.'),
('Green-operator-spectrum',['Green-operator-spectrum','green-kernel-integral-equation'],
 'Recover a boundary-value problem from an integral/difference Green operator before solving. A forced Fredholm equation, continuous eigenproblem and discrete norm limit remain distinct constructions. The existing differentiation/limits shared group is retained.'),
('simple-eigenvalue-perturbation',['simple-eigenvalue-perturbation','simple-eigenvalue-Hellmann-Feynman'],
 'Both vary a simple self-adjoint eigenvalue and remove the unknown eigenvector derivative by normalization/adjoint cancellation. Second matrix derivatives with signed gaps and first potential derivatives in a boundary ODE remain distinct tasks.'),
('frullani-scaling-cancellation',['frullani-scaling-cancellation','Frullani-parameter-integration'],
 'The same integration construction m3-integration-hard-Frullani-rectangle uses both strings. This is label drift within one construction, also related to the retained scaled-Frullani construction.'),
('beta-parameter-moments',['beta-parameter-moments','mixed-beta-logarithmic-moment'],
 'The same integration construction m3-integration-hard-mixed-log-endpoints uses both strings. Parameter differentiation of beta integrals supplies the mixed endpoint logarithmic moments.'),
]

def main():
    cli=argparse.ArgumentParser();cli.add_argument('--output',type=Path,required=True);args=cli.parse_args()
    out=args.output.resolve();assert not out.exists(),'Preserve prior evidence';out.mkdir(parents=True)
    sources={
     'integration':ROOT/'docs/bank/problem-quality/integration/final-group-map-v5.json',
     'diff-limits':ROOT/'docs/bank/problem-quality/diff-limits/final-v4/normalized-record-map.jsonl',
     'series':ROOT/'docs/bank/problem-quality/series/final-v7/item-group-map.json',
     'ode-mv':ROOT/'docs/bank/problem-quality/ode-mv/final-v7/group-map.json'}
    all=[];counts={}
    for key,path in sources.items():
        rows=load(path);counts[key]=len(rows)
        for row in rows:all.append({**row,'_sourceMap':key,'_topic':row.get('topic',key)})
    assert counts=={'integration':766,'diff-limits':1405,'series':705,'ode-mv':1531}
    assert len(all)==4407 and len({r['problemId']for r in all})==4407
    families=collections.defaultdict(list)
    for r in all:families[r['familyId']].append(r)
    def bind(row):
        return {'problemId':row['problemId'],'contentHash':row['contentHash'],'topic':row['_topic'],
         'familyId':row['familyId'],'sourceMap':row['_sourceMap'],
         'sourceMapRecordSHA256':digest(canonical({k:v for k,v in row.items()if not k.startswith('_')}))}
    def evidence(rows):
        return [{'familyId':f,'centralDecisions':sorted({r['centralDecision']for r in rows if r['familyId']==f}),
          'constructionIds':sorted({r['canonicalConstruction']for r in rows if r['familyId']==f}),
          'structures':sorted({r['structuralSignature']for r in rows if r['familyId']==f})}for f in sorted({r['familyId']for r in rows})]
    related=[]
    for target,aliases,reason in RELATED:
        rows=[r for r in all if r['relatedIdeaGroupId']in aliases]
        assert set(aliases)=={r['relatedIdeaGroupId']for r in rows}
        related.append({'canonicalRelatedIdeaGroupId':target,'sourceAliases':aliases,
          'recommendation':'unify-related-idea-history-without-unifying-constructions-or-tasks',
          'reason':reason,'families':evidence(rows),'sourceRecords':[bind(r)for r in rows],
          'newIndependentIdeas':0,'canonicalConstructionChanges':0,'normalizedTaskKeyChanges':0})
    method=[];structures=[];preserve=[]
    for fid,rows in families.items():
        methods=sorted({r['primaryTechnique']for r in rows});sigs=sorted({r['structuralSignature']for r in rows})
        if len(methods)>1:
            if fid=='quality-series-olympiad-finite-cycle-resolvent':
                preserve.append({'familyId':fid,'field':'primaryTechnique','values':methods,
                 'reason':'Two finite instances were independently demoted using cosine-moment bounds; do not replace that demonstrated easier route with the intended root/logarithmic derivative method.'})
            else:
                assert fid in METHOD_TARGETS,fid
                target=METHOD_TARGETS[fid];assert target in methods
                protected={'positive-partial-product-bound'}if fid=='m3-series-hard-dyadic-infinite-product'else set()
                applicable=[r for r in rows if r['primaryTechnique']not in protected]
                method.append({'familyId':fid,'canonicalPrimaryTechnique':target,
                  'sourceAliases':sorted({r['primaryTechnique']for r in applicable}),
                  'scope':'Only this construction and listed source records; do not globally replace generic labels such as substitution, symmetry or linear-systems.',
                  'reason':'The exact map gives the same construction and central task with generic versus specific method labels. Use one existing label consistently for method-recurrence accounting; this creates no new method/idea credit.',
                  'centralDecisionEvidence':evidence(applicable),'sourceRecords':[bind(r)for r in applicable],
                  'protectedEasierRouteLabels':sorted(protected)})
                if protected:preserve.append({'familyId':fid,'field':'primaryTechnique','values':sorted(protected),
                    'reason':'Preserve the three independently justified Medium partial-product-bound cases; normalize only the remaining finite-product method spellings.'})
        if len(sigs)>1:
            if fid in sigs and len(sigs)==2:
                target=next(s for s in sigs if s!=fid)
                structures.append({'familyId':fid,'canonicalStructuralSignature':target,'sourceAliases':sigs,
                 'reason':'A family-ID fallback and a descriptive structural signature describe the same reviewed finite construction. A new extension or option revision does not supply a new structural form.',
                 'sourceRecords':[bind(r)for r in rows],'newStructureCredit':0})
            else:
                assert fid=='q1-differentiation-olympiad-critical-level-absolute-integral',fid
                preserve.append({'familyId':fid,'field':'structuralSignature','values':sigs,
                 'reason':'Quadratic critical sublevels and a mixture of quartic and quadratic critical sublevels have genuinely different local scaling. Do not collapse this reviewed distinction as a spelling change.'})
    # The within-family map uses existing shared canonical constructions for
    # extension aliases; do not reintroduce q2-prefix families as new caps.
    canonical_aliases=[]
    for construction in sorted({r['canonicalConstruction']for r in all}):
        rs=[r for r in all if r['canonicalConstruction']==construction];fs=sorted({r['familyId']for r in rs})
        if len(fs)>1:canonical_aliases.append({'canonicalConstruction':construction,'familyAliases':fs,'records':len(rs),'action':'preserve-already-established-construction-alias'})
    shared=collections.defaultdict(lambda:collections.defaultdict(set))
    for r in all:shared[r['relatedIdeaGroupId']][r['_topic']].add(r['familyId'])
    already=[{'relatedIdeaGroupId':g,'topics':{t:sorted(fs)for t,fs in ts.items()},'action':'preserve-existing-cross-topic-related-group'}for g,ts in shared.items()if len(ts)>1]
    lexical={}
    for field in ['relatedIdeaGroupId','primaryTechnique','structuralSignature']:
        d=collections.defaultdict(set)
        for r in all:d[re.sub('[^a-z0-9]','',r[field].lower())].add(r[field])
        lexical[field]=[sorted(v)for v in d.values()if len(v)>1]
    collisions={}
    for field in ['semanticHash','normalizedTaskKey','problemId']:
        d=collections.defaultdict(list)
        for r in all:d[r.get(field)].append(r)
        collisions[field]=[{'value':k,'sourceRecords':[bind(r)for r in rs]}for k,rs in d.items()if k and len({r['_topic']for r in rs})>1]
        assert not collisions[field]
    must_keep=[
     {'families':['io3-agm-parameter','q1-limits-hard-AGM-normalized-gap-prefactor','m3-series-olympiad-elliptic-central-binomial-square'],
      'reason':'AGM invariance is already shared across integration/limits. Recognizing an elliptic integral from a binomial-square series does not itself require AGM iteration; a shared special function is insufficient to merge the series group.'},
     {'families':['q1-differentiation-olympiad-abel-density-recovery','quality-series-olympiad-lacunary-Abel-growth','quality-series-olympiad-Abel-logarithmic-sum','m3-differential-equations-hard-wronskian-transport'],
      'reason':'Abel integral inversion, Abelian radial summation, lacunary counting and the Wronskian identity are different decisions despite the name Abel.'},
     {'families':['quality-integration-olympiad-support-function-perimeter','q4-multivariable-support-function-area'],
      'reason':'Both involve support functions, but one switches active polygon vertices to recover perimeter and the other differentiates a smooth envelope and uses Green area. Keep structures and primary routes separate; no equivalence established.'},
     {'families':['q1-limits-olympiad-hilbert-determinant-rate','q1-differentiation-olympiad-moment-hankel-vandermonde','quality-series-olympiad-geometric-moment-determinant','q4-multivariable-Vandermonde-Gram-integral'],
      'reason':'The last three already share moment-determinant-antisymmetrization. The limit family adds a growing-dimensional singular logarithmic-energy asymptotic; do not collapse its task/structure because Cauchy determinants appear in both.'},
     {'families':['quality-series-olympiad-rooted-tree-weighted-series','q1-limits-olympiad-implicit-exponential-saddle','q4-differential-equations-inverse-ODE-coefficient-asymptotic','m3-differentiation-olympiad-implicit-series-inversion'],
      'reason':'Lagrange inversion can be shared sub-work, but branch continuation, a global saddle, sparse ODE asymptotics and an elementary quadratic/binomial inversion have different central decisions. Do not identify normalized tasks from a theorem name.'}]
    report={'status':'source-bound-cross-topic-grouping-recommendations-not-applied','reviewer':'series_final_review',
     'sourceArtifacts':{k:artifact(v)for k,v in sources.items()},'reviewCode':artifact(Path(__file__).resolve()),
     'summary':{'records':len(all),'mapCounts':counts,'crossTopicRelatedAliasSets':sum(len({r['topic']for r in a['sourceRecords']})>1 for a in related),
      'withinTopicRelatedAliasSets':sum(len({r['topic']for r in a['sourceRecords']})==1 for a in related),
      'scopedWithinFamilyMethodAliasSets':len(method),'scopedWithinFamilyStructureAliasSets':len(structures),
      'alreadySharedCrossTopicGroups':len(already),'newExactOrScaledTaskEquivalencesDemonstrated':0,
      'canonicalConstructionChangesProposed':0,'normalizedTaskChangesProposed':0,'newIdeaOrCapacityCredit':0},
     'relatedIdeaAliases':related,'primaryMethodAliases':method,'structuralAliases':structures,
     'preserveMeaningfulDifferences':preserve,'alreadyUnifiedCrossTopicGroups':already,'alreadyUnifiedConstructionAliases':canonical_aliases,
     'lexicalCasePunctuationCollisions':lexical,'crossTopicIdentityCollisions':collisions,
     'doNotMergeFromSharedWordsAlone':must_keep,
     'exactAndScaledEquivalenceDisposition':{'demonstratedNewPairs':[],'status':'none-established-in-this-bounded-pass',
      'evidence':'No cross-topic task-ID, semantic-hash or existing normalized-key collision occurs. Comparison of the known overlap constructions establishes related ideas, not equality of their questions, hypotheses, requested outputs or scalar-normalized tasks.',
      'limitation':'No general symbolic cross-topic equivalence search was performed. Absence of hash collisions is not proof that no unrecognized equivalent task exists. Existing per-topic scale aliases and historical semantic lineages must remain intact.'},
     'scope':'All final map entries were inspected for field consistency and identity collisions. Semantic grouping uses their source-bound reviewed central decisions and bounded literal inspection of the known overlap constructions, not 4,407 fresh solutions. Root owns the global mapping and actual selector evaluation.',
     'applicationRules':['Apply family-scoped method and structural aliases only to matching exact content hashes. Preserve raw labels for provenance.',
      'Related-idea history may span different constructions and topics; never automatically reuse it as a canonical-construction or normalized-task equivalence key.',
      'Aliases reduce spurious diversity and earn zero new idea, method or capacity credit. Preserve the independently demonstrated easier method routes.',
      'Carry aliases into returning-player exposure history and both development/reserved selector evaluation; do not clear history.'],
     'globalFilesChanged':False,'admitted':False,'selectorHorizonRerun':False,'humanReviewed':False}
    (out/'cross-topic-grouping-audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report['summary']))
if __name__=='__main__':main()
