"""Conservative, explicit AI-assisted editorial decisions, separate from CAS results."""
QUARANTINE={
'm3-series-easy-alternating-geometric':'Same geometric-series recognition as geometric-tail; signed ratio is a related variant, not a new independent family.',
'm3-series-easy-finite-geometric':'Same geometric-sum recognition; finite endpoint variant retained only in quarantine for honest independent counts.',
'm3-series-easy-geometric-remainder':'A geometric tail is the same recognition as geometric-tail.',
'm3-series-easy-squared-telescope':'Same adjacent first-difference telescoping as rational-telescope; changing the exponent does not create a new idea.',
'm3-series-easy-odd-integer-square':'Same finite-difference/telescoping and elementary arithmetic-sum recognition; not counted separately.',

'm3-series-olympiad-alternating-lattice-resolvent':'Valid mathematics but shares the same whole-lattice partial-fraction recognition and normalization with lattice-resolvent; held out to avoid counting one idea twice.',
'm3-integration-hard-absolute-sinusoid-periods':'A period-split absolute sine integral is routine medium work; the exponent/number of periods does not justify hard.',
'm3-integration-hard-parts-boundary-cancellation':'Recognizing one product derivative is not sufficient hard reasoning as rendered.',
'm3-integration-hard-area-inverse-pair':'The inverse-area identity is a single geometric complement step; pending a harder version.',
'm3-integration-hard-trig-rational':'One logarithmic substitution is medium, not hard.',
'm3-integration-hard-log-ratio-integral':'One integration by parts is medium, not hard.',
'm3-differentiation-hard-differential-error':'A second binomial coefficient is medium fluency, not hard.',
'm3-differentiation-olympiad-dilation-functional-equation':'One nth chain-rule differentiation is hard fluency, not a distinct Olympiad decision.',
'm3-differentiation-olympiad-Hermite-log-product':'Same log-derivative product construction as hard/log-product with one extra order; not an independent Olympiad idea.',
'm3-differentiation-olympiad-inverse-jet':'Cubic inverse coefficient matching is a routine hard instance of inverse differentiation.',
'm3-differentiation-olympiad-Rodrigues-multiplicity':'Same vanishing-Leibniz mechanism as hard/multiplicity-shortcut.',
'm3-limits-medium-continuity-hole-filling':'Same removable power-factor decision as easy/removable-power; no new medium-level construction.',
'm3-limits-medium-integer-subsequence':'The floor is exactly mn for integer inputs; it adds no genuine difficulty to the standard e-limit.',
'm3-limits-hard-fractional-binomial-second':'Single second-order binomial coefficient is medium fluency.',
'm3-limits-hard-geometric-mean-limit':'A first-order log expansion of two factors is routine medium work.',
'm3-limits-hard-oscillatory-derivative-failure':'As rendered only asks derivative at zero, resolved by one squeeze; harder discontinuity decision not actually asked.',
'm3-limits-hard-arctan-infinity-tail':'A reciprocal arctangent standard limit is medium.',
'm3-limits-olympiad-power-second-correction':'Only raises correction order of the hard normalized-power construction; not a new independent Olympiad idea.',
'm3-limits-olympiad-trig-fourth-correction':'Only raises Taylor cancellation order of the same log-sine ratio mechanism.',
'm3-limits-olympiad-Gamma-two-corrections':'Finite product correction of one higher order than the hard family; shared essential recognition.',
'm3-limits-olympiad-endpoint-second-order':'Same finite-polynomial beta concentration construction as hard/boundary-moment, one correction deeper.',
'm3-limits-olympiad-generalized-mean-correction':'Direct finite exponential log-cumulant expansion; difficult algebra alone is not enough.',
'm3-limits-olympiad-Stirling-log-shift':'Direct leading-order Stirling substitution is hard, not Olympiad.',
'm3-limits-olympiad-oscillatory-nonstationary-bound':'One integration-by-parts bound is hard, not Olympiad.',
'm3-limits-olympiad-dilogarithmic-Riemann-log':'Elementary factorial-log Stirling reduction; the slug falsely suggests a dilogarithm.',
'm3-series-hard-binomial-root':'Direct generalized-binomial identity is medium fluency.',
'm3-series-hard-finite-second-binomial-moment':'Same binomial differentiation construction as medium weighted-binomial total with one additional order.',
'm3-series-hard-factorial-odd-part':'An odd exponential Taylor filter is routine medium work.',
'm3-series-hard-factorial-index-shift':'Subtracting a finite exponential Taylor prefix is not hard.',
'm3-series-hard-radius-central-binomial-square':'A straightforward ratio test with squared coefficients is medium.',
'm3-series-olympiad-zeta-even-tail':'Direct substitution into a named advanced formula; neither huge exponents nor unfamiliar constants establish Olympiad demand.',
'm3-multivariable-olympiad-Gaussian-cross-moment':'As authored this is a single even x moment after completing a square; title overstates a mixed Wick decision.',
'm3-multivariable-olympiad-sharp-log-sum-constraint':'A single weighted Cauchy inequality with its standard equality case is hard, not Olympiad.',
'm3-multivariable-olympiad-radial-Laplacian-iterate':'Radial coefficient multiplication is useful hard work; derivative order alone does not justify Olympiad.',
'm3-multivariable-olympiad-angular-rational-moment':'A single linear scaling plus elementary polar integral is medium/hard and contradicts advertised parameter differentiation.',
'm3-multivariable-olympiad-simplex-ray-Gamma':'A standard sum-ratio transform and two routine special-function moments is hard; currently lacks an additional contest-level decision.',
}
GROUP_MERGES={
 'm3-series-olympiad-lattice-resolvent':'lattice-resolvent-partial-fractions',
 'm3-series-olympiad-alternating-lattice-resolvent':'lattice-resolvent-partial-fractions',
 'm3-differentiation-olympiad-Hermite-log-product':'logarithmic-product-derivatives',
 'm3-differentiation-olympiad-Rodrigues-multiplicity':'zero-multiplicity',
 'm3-limits-olympiad-Gamma-two-corrections':'finite-product-second-order',
 'm3-limits-olympiad-endpoint-second-order':'endpoint-concentration',
 'm3-limits-olympiad-power-second-correction':'second-asymptotic-scale',
 'm3-limits-olympiad-trig-fourth-correction':'power-with-cancelled-trig-ratio',
 'm3-series-hard-finite-second-binomial-moment':'binomial-first-moment',
}
def install(core):
 import json,hashlib
 from pathlib import Path
 base=Path(__file__).resolve().parent
 files=['coverage.py','multivariable.py','extra.py','certificates.py','distractors.py','editorial.py']
 source_hash=hashlib.sha256(b''.join((base/name).read_bytes() for name in files)).hexdigest()
 try:attestation=json.loads((base/'admission.json').read_text())
 except (OSError,ValueError):attestation={}
 admitted=set(attestation.get('admittedFamilies',[])) if attestation.get('sourceHash')==source_hash else set()
 for f in core['FAMILIES']:
  fid=f['familyId']
  if fid in GROUP_MERGES:f['relatedIdeaGroupId']=GROUP_MERGES[fid]
  f['editorialStatus']='quarantined' if fid in QUARANTINE else ('admitted' if fid in admitted else 'reviewed-pending-validation')
  f['editorialReview']={'reviewType':'AI-assisted mathematical/editorial review','humanReviewed':False,'decision':f['editorialStatus'],'reason':QUARANTINE.get(fid,('All eight finite-domain instances passed the attested exact, domain, and rendering checks; AI-assisted editorial review.' if fid in admitted else 'No mathematical or level blocker identified in the recorded review; all finite-domain and presentation checks must still pass.'))}
