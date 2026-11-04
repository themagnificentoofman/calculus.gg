"""Read-only synthesis of existing evidence for the 72 original v2 families.

No constructors, canonical records, history, eligibility or screen thresholds are
changed. Existing finite measurements are joined, not rerun or extrapolated.
"""
import argparse, hashlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/bank'))
from families import FAMILIES
import sympy as sp

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def digest(x):
    return hashlib.sha256(x.encode()).hexdigest()

def load(path):
    return json.loads(path.read_text())

def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024*1024), b''):
            h.update(data)
    return h.hexdigest()

def artifact(path):
    import os
    return {'path': os.path.relpath(path, ROOT), 'sha256': file_hash(path)}

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    out = args.output.resolve()
    if out.exists():
        raise RuntimeError('Use a new evidence directory; preserve prior outputs.')
    out.mkdir(parents=True)
    paths = {
        'dispositions': ROOT/'docs/bank/problem-quality/legacy-dispositions.json',
        'withdrawals': ROOT/'docs/bank/problem-quality/legacy-withdrawals.json',
        'baselineScreen': ROOT/'.bank-data/quality/baseline-option-screen.json',
        'baselineSummary': ROOT/'docs/bank/problem-quality/baseline-option-summary.json',
        'baselineInput': ROOT/'.bank-data/quality/baseline-options.jsonl',
        'odeInventory': ROOT.parent/'quality-research/ode-multivariable/inventory.json',
        'diffInventory': ROOT.parent/'quality-research/differentiation-limits/legacy-disposition.json',
        'seriesInventory': ROOT.parent/'quality-research/series-sources/initial-disposition.json',
        'completeSolutionReview': ROOT/'scripts/bank/solution-review/integration-legacy/complete-family-audit.json',
        'mathematicalCertificates': ROOT/'scripts/bank/solution-review/integration-legacy/legacy-certificates.json',
        'presentationContract': ROOT/'scripts/bank/solution-review/integration-legacy/contract-audit.json',
        'presentationRender': ROOT/'scripts/bank/solution-review/integration-legacy/render-audit.json',
        'historicalHashGuard': ROOT/'lib/server/solution-reviews/legacy-hashes.json',
        'constructor': ROOT/'scripts/bank/pipeline.py',
        'familyDefinitions': ROOT/'scripts/bank/families.py',
        'advancedDefinitions': ROOT/'scripts/bank/olympiad.py',
        'specialOdeDefinitions': ROOT/'scripts/bank/special_ode.py',
        'reviewCode': Path(__file__).resolve(),
    }
    D, W, A, S = (load(paths[k]) for k in ['dispositions','withdrawals','baselineScreen','baselineSummary'])
    family_ids = {r['familyId'] for r in D['families']}
    assert len(family_ids) == 72
    definitions = {r['id']: r for r in FAMILIES}
    assert family_ids == set(definitions) == {r['familyId'] for r in W['withdrawals']}
    assert A['artifactSha256'] == S['artifactSha256'] == file_hash(paths['baselineInput'])
    assert A['records'] == S['records'] == 103304
    inventory = {}
    for key, field in [('odeInventory','legacyFamilies'),('diffInventory','legacyFamilies'),('seriesInventory','legacyDispositions')]:
        for row in load(paths[key])[field]:
            assert row['familyId'] not in inventory
            inventory[row['familyId']] = (key, row)
    assert family_ids == set(inventory)
    prior_solutions = {r['familyId']: r for r in load(paths['completeSolutionReview'])['families']}
    certs = {r['familyId']: r for r in load(paths['mathematicalCertificates'])}
    assert family_ids == set(certs)
    packed = load(paths['historicalHashGuard'])
    assert isinstance(packed,str) and len(packed) == 100800*64
    guard = {packed[n:n+64] for n in range(0,len(packed),64)}
    records = defaultdict(list)
    with paths['baselineInput'].open() as f:
        for line in f:
            row = json.loads(line)
            if row['familyId'] in family_ids:
                assert row['contentHash'] in guard
                assert len(row['choices']) == 4
                records[row['familyId']].append(row)
    assert sum(map(len,records.values())) == 100800
    assert {r['contentHash'] for rows in records.values() for r in rows} == guard
    assert len({r['problemId'] for rows in records.values() for r in rows}) == 100800

    special = {
        'hidden-riccati': 'Dedicated parameter-dependent nonlinear Riccati constructor. Subtract p(x)=a x+b/x to obtain z′=z², with a parameter-dependent evaluation point inside the stated pole-free interval. This is not a linear combination of three fixed kernels.',
        'clairaut-envelope': 'Dedicated nonlinear singular-branch constructor, selecting the non-affine positive-derivative envelope of a Clairaut equation. Its parameters change the envelope and evaluation point; the proof is a symbolic branch/residual check, not linear superposition.',
        'euler-double-resonance': 'Dedicated parameter-dependent Euler equation. The parameter a changes the characteristic root and b changes the logarithmic forcing power; t=ln x and u=x^a v(t) reduce it to v″=t^b. This is not three fixed linear kernels.',
    }
    rows = []
    for d in sorted(D['families'],key=lambda r:(r['topic'],r['familyId'])):
        fid = d['familyId']; f = definitions[fid]; audit = A['families'][fid]
        assert audit['items'] == len(records[fid]) == 1400
        assert len(audit['trainingIds']) == len(audit['heldoutIds']) == 700
        assert set(audit['trainingIds']).isdisjoint(audit['heldoutIds'])
        assert set(audit['trainingIds']+audit['heldoutIds']) == {r['problemId'] for r in records[fid]}
        assert audit['flags'] == S['families'][fid]['flags']
        assert audit['selectedUsingTrainingOnly'] == S['families'][fid]['selectedUsingTrainingOnly']
        k, prior = inventory[fid]
        assert certs[fid]['instances'] == 1400 and certs[fid]['exactBasisRecalculated']
        assert certs[fid]['immutableBasisResultsAgree'] and prior_solutions[fid]['mathematicalResultAgreement']
        all_results = {r['rule']:r for r in audit['results']}
        flags = [{**flag, 'training':all_results[flag['rule']]['training'], 'heldout':all_results[flag['rule']]['heldout']} for flag in audit['flags']]
        nonposition_flags = [flag for flag in flags if not flag['rule'].startswith('shuffled-position-')]
        replicated = [r for r in audit['results'] if not r['rule'].startswith('shuffled-position-') and r['training']['expectedTieBrokenAccuracy']>=.625 and r['heldout']['expectedTieBrokenAccuracy']>=.625]
        nonposition = [r for r in audit['results'] if not r['rule'].startswith('shuffled-position-')]
        best_nonposition = sorted(nonposition,key=lambda r:(-r['training']['expectedTieBrokenAccuracy'],r['rule']))[0]
        lattice = prior.get('optionOnlyHeldOutLatticeCue')
        lattice_signal = bool(lattice and lattice.get('status')=='executed' and lattice.get('heldOutExpectedAccuracyWithUniformTieBreak',0)>=.625)
        if nonposition_flags:
            measured_status = 'existing-general-screen-measured-nonposition-signal'
            recommendation = 'Do not allow these original menus in Experimental yet. Resolve the measured choice clue for exact proposed revisions, with independent mathematical and options-visible review.'
        elif lattice_signal:
            measured_status = 'no-general-screen-flag-but-existing-specialized-rational-lattice-signal'
            recommendation = 'Do not allow these original menus in Experimental yet. The separate rational-lattice audit supplies an actual measured clue even though the general screen does not flag this family.'
        else:
            measured_status = 'no-threshold-flag-in-existing-screens-not-cleared'
            recommendation = 'Do not claim a measured exploitable signal from the reviewed screens. Keep exact originals outside the Experimental allowlist until current finite content, misconception-option and easiest-route standards are demonstrated. Underlying practice value can justify future bounded review.'
        if k == 'odeInventory':
            usefulness = {'status':'prior-editorial-practice-usefulness-at-concept-level','recommendedConceptDifficulty':prior['recommendedDifficulty'],'reason':prior['reason']}
        elif k == 'diffInventory':
            usefulness = {'status':'prior-editorial-practice-disposition-at-concept-level','priorDisposition':prior['conceptualPracticeDisposition'],'reason':prior['rationale']}
        else:
            usefulness = {'status':'prior-editorial-practice-usefulness-at-concept-level','recommendedConceptDifficulty':prior['easiestRouteEditorialRating'],'centralDecision':prior['centralDecision'],'priorDisposition':prior['conceptDisposition']}
        usefulness.update({'establishesCurrentMenuEligibility':False,'measuredPlayerUsefulness':False,'coefficientVariantsAreNotNewIdeas':True})
        family_records = sorted(records[fid],key=lambda r:r['problemId'])
        record_bindings = [{key:r[key] for key in ['problemId','problemRevision','contentHash','answerChoiceId']} for r in family_records]
        previously_bound_sha = d.get('auditSourceSha256')
        actual_prior_sha = file_hash(paths[k])
        known_basis = certs[fid]['basisValues']
        rows.append({
            'familyId':fid,'topic':d['topic'],'baselineDifficulty':d['baselineDifficulty'],'originalRecords':1400,
            'exactHistoricalSource':{'originalSourceReleaseId':'cn-2026-11-02-full-v2','templateVersion':'original-linear-families-v2',
                'sourceRecordBindingSHA256':digest(canonical(record_bindings)), 'baselineOptionRowsSHA256':digest(canonical(family_records)),
                'allContentHashesInCurrentHistoricalPresentationGuard':True,'sample':record_bindings[0],
                'trainingIdsSHA256':digest(canonical(audit['trainingIds'])),'heldoutIdsSHA256':digest(canonical(audit['heldoutIds']))},
            'constructor':{'operationKind':f['kind'],'actualConstruction':special.get(fid,'One fixed calculus operation applied to a linear combination a·K₁+b·K₂+c·K₃ of three fixed kernels; bounded integer coefficient triples create the 1,400 records.'),
                'fixedKernelLatex':[] if fid in special else [sp.latex(x)for x in f['kernels']],
                'fixedOperationArguments':{key:sp.latex(v) if isinstance(v,sp.Basic)else v for key,v in f.items()if key in ['lo','hi','point','order','start','dx','dy','px','py','xhi','yhi','initial']},
                'verifiedBasisValues':known_basis,
                'zeroBasisContributionCount':sum(v=='0'for v in known_basis),
                'repeatedBasisValues':sorted(v for v,n in Counter(known_basis).items()if n>1),
                'weakness':'Every menu uses answer plus three nonzero hash-selected multiples of one positive answer-derived unit. The source does not author each wrong choice by recomputing a mathematical misconception. This is a demonstrated construction/review gap, not proof of an exploitable clue for every family or every item.',
                'coefficientCoverageLimitation':'Large bounded parameter coverage proves neither a new mathematical decision for each tuple nor useful exposure depth. Three special ODE constructors require their own parameter-dependent description.',
                'legacyDispositionDescriptionNeedsCorrection':fid in special},
            'measuredHeuristics':{'status':measured_status,'source':'baselineScreen','rawBaselineOptionsOnly':True,
                'trainingItems':700,'heldoutItems':700,'selectedUsingTrainingOnly':audit['selectedUsingTrainingOnly'],
                'bestNonPositionRuleChosenUsingTrainingOnly':best_nonposition,'flags':flags,
                'replicatedNonPositionRulesAt625':replicated,'allExistingRuleMeasurements':audit['results'],
                'specializedPriorRationalLatticeAudit':lattice,
                'uncertainty':'A missing threshold flag is not a zero-cue result or a quality certificate. Scores below the threshold are retained. This older raw-options screen does not cover later rational-square/cube or opposite-expression diagnostics, and has not been rerun through the current presenter in this evidence synthesis.'},
            'existingMathematicalAndPresentationEvidence':{'certificate':certs[fid],
                'solutionReview':prior_solutions[fid],
                'scope':'Prior exact operation/linearity or special-ODE certificates cover the bounded source family. Current content-hash guards cover every original source record. The prior strict presentation render checked four edge records per family, not all 100,800 served presentations; this synthesis performs no fresh solution derivations or renders.'},
            'validPracticeUsefulness':usefulness,
            'priorEditorialEvidence':{'sourceArtifact':k,'recordSHA256':digest(canonical(prior)),'record':prior,
                'dispositionPreviouslyRecordedSourceSHA256':previously_bound_sha,'actualSourceSHA256':actual_prior_sha,'sourceHashMatchesEarlierDisposition':previously_bound_sha==actual_prior_sha},
            'recommendation':{'action':'not-currently-demonstrated-for-experimental-allowlist','reason':recommendation,
                'requiredBeforeEligibility':['Choose a bounded exact revision set and demonstrate purposeful practice value at the easiest reasonable level.','Review actual current statements, solutions, all literal alternatives and their misconception routes, with exact source bindings.','Resolve measured clues and disclose untested or uncertain diagnostics; run the current bounded screens and full proposed presentation checks.','Use an explicit Legacy label and Experimental opt-in only after the owner admits the exact reviewed revisions.'],
                'currentFullyQualifiedExactOriginalSubset':[],'fullyQualifiedExactOriginalCount':0,
                'historicalTreatment':'Keep canonical hashes, recorded choices, grades, saved playbacks and exposure lineage immutable. A future eligibility disposition does not rewrite history.',
                'ageSuppliesEligibilityOrWithdrawalReason':False,'newAdvancedIdeaCredit':0},
            'originalWithdrawal':next(r for r in W['withdrawals']if r['familyId']==fid),
        })
    count_status = Counter(r['measuredHeuristics']['status']for r in rows)
    assert count_status['existing-general-screen-measured-nonposition-signal']==15
    assert count_status['no-general-screen-flag-but-existing-specialized-rational-lattice-signal']==1
    assert count_status['no-threshold-flag-in-existing-screens-not-cleared']==56
    summary = {'legacyFamilies':72,'legacyOriginalRecords':100800,'generalScreenAllBaselineRecords':103304,
        'generalScreenFlaggedLegacyFamilies':15,'generalScreenNoFlagLegacyFamilies':57,
        'additionalFamilyWithPriorSpecializedLatticeSignal':1,'familiesWithSomeDocumentedThresholdSignal':16,
        'familiesWithoutThresholdSignalInReviewedExistingScreens':56,
        'familiesWithPriorExactMathematicalCertificates':72,'historicalContentHashesMatched':100800,
        'linearFixedKernelFamilies':69,'dedicatedParameterDependentOdeFamilies':3,
        'fullyDemonstratedExactOriginalsForExperimental':0,'sourceHashMismatchesAgainstPriorDisposition':sum(not r['priorEditorialEvidence']['sourceHashMatchesEarlierDisposition']for r in rows)}
    report = {'status':'read-only-existing-evidence-synthesis-not-admission','reviewer':'series_final_review',
        'scope':'All 72 original v2 families only. M3 content is not classified Legacy merely because it predates this release. No new content, classifier sweep, independent 100,800-item mathematical re-solve, eligibility change or deployment occurs.',
        'summary':summary,'sourceArtifacts':{k:artifact(p)for k,p in paths.items()},
        'screenProtocol':{'existingSplit':A['split'],'randomChance':.25,'existingFlagThreshold':.625,
            'existingFlagMinimumApplicableHeldout':3,'sameInputsAndSplitsPreserved':True,
            'noThresholdRelaxation':True,'noNewClassifiersOrReruns':True,'rawVersusServedLimitation':'Source options are the original baseline export. Do not advertise these results as a current full served-display clearance.'},
        'crossFamilyFindings':['Only 15 of 72 original families have a non-position flag in the general baseline screen; it is false to describe all 72 as having measured exploitable choice signals.',
            'The prior specialized rational-lattice audit measures a further signal for removable-exponential-derivative. Its 89.642857% held-out expected accuracy and 555/555 unique predictions are distinct from the no-flag generic-screen result.',
            'The baseline generic screen omits later rational-square, rational-cube and opposite-expression predictors. Unsupported arithmetic parsing and a no-flag result remain limitations, not evidence of absence.',
            'All 72 have prior exact mathematical and improved-solution evidence. This positive evidence is retained even where eligibility remains unearned.',
            'All original menus still originate from generic answer-derived additive offsets, without exact reviewed misconception routes. The reviewed evidence does not demonstrate any old revision satisfying every current content, distractor, presentation and difficulty requirement.',
            'Three special ODE constructors are not three-fixed-kernel linear combinations; blanket source descriptions should be corrected for those families.',
            'No fully qualified subset is demonstrated by these sources. This is an evidence limit, not a theorem that no historical item could ever earn eligibility under a bounded review.'],
        'priorPresentationReview':{'contract':load(paths['presentationContract']),'render':load(paths['presentationRender'])},
        'families':rows,'recommendedExactExperimentalAllowlist':[],
        'historicalMutationCount':0,'admitted':False,'imported':0,'active':0,'humanReviewed':False}
    (out/'legacy-evidence-audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(summary))

if __name__=='__main__':
    main()
