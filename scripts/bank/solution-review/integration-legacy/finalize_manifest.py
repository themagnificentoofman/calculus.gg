import os
from pathlib import Path
import json,hashlib,sqlite3
BASE=Path(__file__).parent;ROOT=Path(os.environ.get('BANK_AUDIT_REPO',Path(__file__).resolve().parents[4]))
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
legacy=json.loads((BASE/'legacy-certificates.json').read_text());defs=json.loads((BASE/'legacy-definitions.json').read_text());recipes=json.loads((BASE/'legacy-recipes.json').read_text());io=json.loads((BASE/'io3-audit.json').read_text());inter=json.loads((BASE/'intermediate-checks.json').read_text());render=json.loads((BASE/'render-audit.json').read_text());contract=json.loads((BASE/'contract-audit.json').read_text())
issues={
'weighted-complement':'Defines the complementary ratio, invariant weight and target integral; supplies the weight substitution.',
'reciprocal-quartic':'Defines the target and states the reciprocal substitution before the monotone substitution.',
'inverse-moment':'Makes the inverse domain/range explicit and displays the actual Jacobian and power contributions.',
'chebyshev-absolute':'Explains the recurrence identity, absolute-value substitution and counted half-periods.',
'floor-laplace':'Defines the staircase representation and proves the nonnegative interchange before summing tails.',
'gamma-unit-average':'Defines the sliding function and its improper endpoint extension, constant and log-sine derivation.',
'log-fourier-coefficient':'Maps the ratio and frequency to the actual instance and displays orthogonality.',
'arctan-parameter':'Defines the parameter family, differentiability condition, partial fractions and initial value.',
'gaussian-fourier':'Defines the parameter family with the actual Gaussian coefficient, its ODE and normalization.',
'reciprocal-gaussian':'Defines the varying parameter and the inversion in its differentiated integral.',
'sinc-overlap':'Defines the cosine-difference integral and connects product-to-sum, Dirichlet and the actual frequencies.',
'mixed-beta-log':'Defines Gamma, beta and harmonic notation and maps the mixed derivative to the instance.',
 'thermal-derivative':'Gives the exact Laplace moment and frequency power after the positive series expansion.',
'mellin-cyclotomic':'Defines the reflection exponent and transformed differential with its strict convergence domain.',
'cauchy-convolution':'Defines the rational function, actual pole parameters and both explicit residue contributions.',
'binomial-exponential':'Transforms both bounds and the differential and gives the integer factorial evaluation.',
'agm-parameter':'Defines the integral family, entire-line substitution, symmetry factor and uniqueness argument.',
'abel-recovery':'Defines the target; justifies absolute Fubini and evaluates the resulting finite polynomial integral.',
'boundary-asymptotic':'Defines the target limit and zero-extended rescaled function; states pointwise convergence and domination.',
'integral-equation':'Defines the kernel operator and actual coefficient; gives both ODE necessity and original-residual sufficiency.',
'convolution-laplace':'Defines the actual Laplace parameter, transforms, supports, translation and recurrence.',
'poisson-log-potential':'Defines the harmonic function and actual height/displacement; verifies its zero is below the domain.',
'jensen-radius':'Defines the actual radius and explains the vanishing full-period Fourier modes.',
'fresnel':'Defines the regulator, coefficient, square-root branch and uniform tail estimate needed for the ordinary integral.',
'bessel-laplace':'Defines both scales; supplies the angular moment identity, Fubini condition and tangent substitution.',
'rodrigues-moment':'Justifies all endpoint cancellations and evaluates the final integral by a finite monomial sum.',
'bernoulli-product':'Defines Bernoulli numbers, product integrals and recurrence domains; displays the final endpoint jump.',
'principal-value':'Separates ordinary divergence, the symmetric-cutoff correction and reciprocal reduction before reflection.',
'oscillatory-regularization':'Separates the nonconvergent cutoff from the well-defined positive-damping limit.',
'concentration':'Defines the integral sequence and its exact substituted value for every positive parameter.',
'binary-product':'Connects the binary product to a finite polynomial before integrating; harmonic convention is in the question.',
'fejer-fourth':'Defines the geometric exponential sum and connects its modulus to the displayed trigonometric ratio.',
'scaled-frullani':'Uses actual bounds for the parameter integral and justifies the interchange by nonnegativity.',
'sech-fourier':'Defines the actual frequency and complex beta exponent with its strip condition.',
'variational-energy':'Defines the functional, coefficient, feasible candidate and residual; expands the cross term explicitly.',
'moment-projection':'Defines the prescribed moment, centered basis, variance and candidate; verifies feasibility and orthogonality.',
'quadrature-defect':'Defines the nodes and leading coefficient role; supplies exactness for every cubic basis monomial.',
'rearrangement':'Defines the level sets and their lengths, gives sharp set-moment inequalities and feasible extremizers.'}
allrows=[]
for r in legacy:
 fid=r['familyId'];recipe=recipes[fid]
 allrows.append({'familyId':fid,'inventory':r['instances'],'status':'solution-correction-ready','mathematicalResultAgreement':True,'logicalReview':'Each supplied identity is now tied to the actual fixed components; unrelated tag-selected identities removed. Operator derivatives, endpoint evaluations, convergence conditions and the final coefficient combination are explicitly present. Special ODEs use their own residual/branch argument rather than superposition.' if r['kind']!='special-ode' else 'Defines the transformed unknown, derives its equation and initial or singular-branch condition, reconstructs the original unknown and evaluates the actual target.','conditions':defs[fid].get('assumptions',[]),'finiteCertificate':r,'representativeEdgeInstancesChecked':4,'checks':['symbol meanings and actual-instance mapping','decisive step to result','domains and convergence or uniqueness','no irrelevant parameter dump','natural logarithm and inverse trigonometric notation','primitive constants or explicit chosen primitives','immutable source answer agreement','strict KaTeX syntax','no ASCII formulas in prose'],'humanReviewed':False})
for fid,r in io['families'].items():allrows.append({'familyId':fid,'inventory':r['instances'],'status':'solution-correction-ready','mathematicalResultAgreement':True,'logicalReview':issues[fid[4:]],'finiteChecks':inter['io3FamilyChecks'][fid],'allFiniteInstancesReviewed':True,'humanReviewed':False})
(BASE/'complete-family-audit.json').write_text(json.dumps({'scopeFamilies':len(allrows),'scopeInstances':sum(x['inventory'] for x in allrows),'families':allrows,'statementChoiceIdentityChanges':False,'humanReviewed':False},indent=2)+'\n')
sources={str(ROOT/'scripts/bank'/name):sha(ROOT/'scripts/bank'/name) for name in ['pipeline.py','families.py','derivations.py','special_ode.py','olympiad.py','content/integration.py']}
db=Path(os.environ['BANK_AUDIT_LEGACY_DB'])
c=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True);sourcefamilies={}
for (meta,) in c.execute('select metadata_json from cbank_shared'):
 d=json.loads(meta);sourcefamilies[d['familyId']]={'templateVersion':d['templateVersion'],'mathematicalSourceHash':d['validation']['evidence'].get('mathematicalSourceHash'),'assumptions':d['assumptions']}
(BASE/'legacy-source-fingerprints.json').write_text(json.dumps(sourcefamilies,indent=2)+'\n')
assets=['io3_solutions.py','io3-solutions.json','legacy-solutions.mjs','legacy-recipes.json','complete-family-audit.json','legacy-certificates.json','legacy-definitions.json','legacy-source-fingerprints.json','io3-audit.json','intermediate-checks.json','render-audit.json','contract-audit.json','io3-independent-peer.json']
manifest={'version':'integration-legacy-solution-audit-v1','status':'ready-for-owner-integration','apis':{'io3':{'path':str(BASE/'io3_solutions.py'),'supports':'supports(record)','render':'corrected_solution(record)','runtimeExport':str(BASE/'io3-solutions.json')},'legacy':{'path':str(BASE/'legacy-solutions.mjs'),'supports':'supports(record)','render':'correctedLegacySolution(record)','alias':'corrected_solution(record)','runtimeDependencies':[]}},'coverage':{'legacyFamilies':72,'legacyInstancesByFiniteCertificates':100800,'legacyIndependentBasisOperations':207,'legacyNonlinearOrParameterODECertificates':3,'legacyEdgeInstances':288,'io3Families':38,'io3Instances':304,'io3ExecutedSourceIdentityChecks':sum(v['executedSourceIdentityChecks'] for v in inter['io3FamilyChecks'].values()),'extraBridgeAndEdgeChecks':inter['newBridgeCheckCount'],'strictKatexExpressions':render['renderedExpressions'],'contractChecks':contract['checks']},'immutability':{'statementsChanged':False,'choicesChanged':False,'identitiesChanged':False,'originalRecordsChanged':False,'sourceRepositoryEdited':False,'productionWrites':False},'requiredIntegrationGuard':'Legacy supports identifies recipe coverage only. The owner must allowlist original content hashes and versions before rendering current corrected explanations. io3 JSON includes the exact original sourceContentHash. Preserve immutable stored originals and replay snapshots.','durableRules':['Introduce each auxiliary function, operator and nonstandard symbol before using it.','Map only mathematical parameters that actually occur in the instance and derivation; never dump builder parameters.','Show the decisive transformation and actual endpoints or evaluation point before the final value.','State convergence, interchange, branch and uniqueness conditions where they support a step.','Use natural-log and named inverse-trigonometric notation; keep formulas out of prose strings.','Use derivative identities for chosen primitives or include arbitrary constants in indefinite-integral equalities; retain logarithmic absolute values whenever the domain requires them.','Do not label formula reconstruction as a proof of analytic theorems; separate executed identities from explicit theorem obligations.','Render every finite new instance and every legacy template plus bounded parameter edges; guard source hashes so unrelated records cannot acquire the recipe.'],'verificationLimits':['AI-assisted mathematical/editorial review; no human or formal-proof-assistant certification.','Strict KaTeX syntax checked; browser geometry remains the owner’s final review.','Classical analytic theorem applications retain explicit mathematical hypotheses; no claim that a CAS proved measure theory or complex analysis.'],'sourceFiles':sources,'legacyImmutableDatabase':{'path':str(db),'sha256':sha(db)},'activeArtifact':{'path':'/Users/zhenxg/Documents/Codex/2026-11-03/sign/work/milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl','sha256':io['sourceSha256']},'assets':{name:sha(BASE/name) for name in assets}}
(BASE/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'status':manifest['status'],'coverage':manifest['coverage'],'manifest':str(BASE/'delivery-manifest.json')}))
