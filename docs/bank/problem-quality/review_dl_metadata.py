"""Independent source-join and bounded refined-label review; no raw mutations."""
from pathlib import Path
import json,hashlib,re,collections
import sympy as s
from literal_numeric_extended import parse
P=Path(__file__).resolve().parent;BASE=P.parent/'differentiation-limits';META=BASE/'metadata-addendum';SRC=BASE/'portable/diff-limits'
H=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();fh=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def expected_refinement(raw,ref):
 f=raw['familyId'];st=raw['statement'];old=ref['originalEvidenceLabel'];x=s.symbols('x',real=True);note=None
 if f.endswith('moving-integral-endpoints'):
  m=s.Integer(re.search(r'\\int_x\^\{(\d+)x',st)[1]);assert 'e^t'in st;correct=m-1;result={'omit a derivative contribution':m,'misapply the chain or product rule':m+1}[old];argument='Leibniz gives m*exp(mx)−exp(x); omitting the second term gives m at0, while adding it gives m+1.'
 elif f.endswith('noncommuting-operator'):
  m=s.Integer(re.search(r'L\^\{(\d+)\}',st)[1]);fx=s.exp(-x*x+x);assert s.simplify(s.diff(fx,x)+2*x*fx-fx)==0;correct=s.Integer(1);result={'use an inappropriate rule':m,'reverse a relation':s.factorial(m),'omit a contribution':2**m}[old];argument='The displayed function is an eigenfunction of D+2x with eigenvalue1 and f(0)=1. Replacing iteration by m times one application, a degree-m monomial derivative, or the false eigenvalue2 gives the three literal wrong values.'
  if old=='reverse a relation':note='The label introduces an undefined generic m. It is acceptable as an audit shorthand only; do not expose it as a public explanation. This exact index is withdrawn. A future source-bound label can say: Confuse the operator iterate with the factorial normalization of a monomial derivative.'
 elif f.endswith('exponential-variable-power'):
  m=s.Integer(re.search(r'\\left\((\d+) x \+ 1',st)[1]);loglimit=s.limit(s.log(1+m*x)/x,x,0,dir='+');assert loglimit==m;correct=s.exp(m);result={'drop a leading contribution':s.exp(1/m),'discard the first surviving limit term':s.Integer(0)}[old];argument='The logarithm of the power has limit m. Inverting that scale before exponentiation gives exp(1/m); taking only the logarithm numerator limit and omitting the remaining operations gives0.'
 else:
  assert f.endswith('recurrence-limit');C=s.Integer(re.search(r'\\sqrt\{(\d+)\+a_n',st)[1]);L=(1+s.sqrt(1+4*C))/2;assert L.is_Integer and L>2;correct=L;result={'omit the endpoint correction':s.sqrt(C),'retain a lower-order term':C,'use the wrong asymptotic scale':L-1}[old];argument='The positive fixed point solves L²−L−C=0. Dropping the recurrence term gives the first iterate sqrt(C); returning C drops both operations; taking the absolute value of the negative root gives L−1.'
 literal=parse(ref['math']);assert s.simplify(literal-result)==0 and s.simplify(literal-correct)!=0
 return {'independentWrongValue':s.srepr(result),'independentCorrectValue':s.srepr(correct),'literalExactMatch':True,'notCorrectChoice':True,'argument':argument,'publicLabelNote':note}
def main():
 report=json.loads((META/'report.json').read_text());assert fh(META/'report.json')=='e86ba642b2409527cf27ef2d1baf344a3ef2519c403f2c059dc34d8b2f326afd';joins=json.loads((SRC/'source-joins.json').read_text());assert fh(SRC/'source-joins.json')==report['sourceClosure']['source-joins.json'];cache={}
 for f,h in joins['sourceArtifacts'].items():assert fh(SRC/f)==h;cache[f]=json.loads((SRC/f).read_text())
 expected={}
 for j in joins['records']:
  if not j['route'].startswith('diff-limits'):continue
  raw=cache[j['sourceFile']][j['sourceRecordIndex']];assert H(raw)==j['rawSha256'];missing=any('misconception'not in c for c in raw['choices']);kind=raw['provenance']['kind']in['original-constructor-extension','original-finite-pool-replacement']
  if missing or kind:expected[j['rawSha256']]=(j,raw,missing,kind)
 assert len(expected)==508 and set(expected)=={e['rawSha256']for e in report['entries']}
 priorpath=SRC/report['priorIndependentMathEvidence']['path'];assert fh(priorpath)==report['priorIndependentMathEvidence']['sha256'];prior=json.loads(priorpath.read_text());priorby={r['rawHash']:r for r in prior['records']}
 refs={(r['rawSha256'],r['choiceId']):r for r in report['refinements']};assert len(refs)==35;checkedrefs=[];results=[];counts=collections.Counter()
 for e in report['entries']:
  j,r,missing,kind=expected[e['rawSha256']];assert e['sourceFile']==j['sourceFile']and e['sourceRecordIndex']==j['sourceRecordIndex']and e['sourceFileSha256']==fh(SRC/e['sourceFile']);assert e['familyId']==r['familyId']and e['expectedChoices']==[{k:c[k]for k in['choiceId','math']}for c in r['choices']];assert len({c['choiceId']for c in r['choices']})==4
  assert e['rawSha256']in priorby;mathevidence=priorby[e['rawSha256']];assert mathevidence['answerIndependentlyDerived']and mathevidence['sixLiteralChoicePairsPassed']
  if missing:
   assert all('misconception'not in c for c in r['choices']);mapping=e['choiceMisconceptions'];assert set(mapping)=={c['choiceId']for c in r['choices']};source=r['validation']['evidence']['choiceMisconceptions'];assert set(source)=={c['math']for c in r['choices']}
   for c in r['choices']:
    label=mapping[c['choiceId']];assert (label=='correct')==(c['choiceId']==r['answerChoiceId']);ref=refs.get((e['rawSha256'],c['choiceId']))
    if ref:
     assert ref['math']==c['math']and ref['originalEvidenceLabel']==source[c['math']]and ref['reviewedLabel']==label
     check=expected_refinement(r,ref);checkedrefs.append({'rawSha256':e['rawSha256'],'familyId':r['familyId'],'index':r['parameters']['instance'],'choiceId':c['choiceId'],'literalMath':c['math'],'originalLabel':ref['originalEvidenceLabel'],'reviewedLabel':label,**check})
    else:assert label==source[c['math']]
   counts['completeMaps']+=1;counts['labels']+=4
  else:assert 'choiceMisconceptions'not in e
  if kind:
   assert e['originalProvenanceKind']==r['provenance']['kind']and e['proposedCanonicalKind']=='original'and e['preservedProvenance']==r['provenance'];lineage=r['provenance']['lineage'];assert lineage['newIdeaCredit']==0 and lineage['originalFamilyId']==lineage['construction']
   if r['provenance']['kind']=='original-constructor-extension':assert lineage['sameRelatedIdea']is True
   else:assert r['provenance']['withdrawOriginalFinitePool']is True
   assert r['provenance'].get('sourceContentHash')or r['provenance']['kind']=='original-finite-pool-replacement';counts['originalKindMappings']+=1;counts[r['provenance']['kind']]+=1
  else:assert 'proposedCanonicalKind'not in e
  withdrawn=r['familyId']=='m3-differentiation-olympiad-noncommuting-operator'and r['parameters']['instance']in range(1,8)
  results.append({'reviewId':e['reviewId'],'rawSha256':e['rawSha256'],'sourceFile':e['sourceFile'],'sourceRecordIndex':e['sourceRecordIndex'],'familyId':r['familyId'],'index':r['parameters']['instance'],'completeLabelMapLifted':missing,'originalKindMapped':kind,'mathematicalEvidenceEntryHash':H(mathevidence),'metadataOnlyNoTaskOrLineageChange':True,'existingWithdrawalMustRemain':withdrawn,'passed':True})
 assert len(checkedrefs)==35 and counts['completeMaps']==324 and counts['originalKindMappings']==184
 notes=[r for r in checkedrefs if r['publicLabelNote']];assert len(notes)==4 and all(r['index']in[1,3,5,7]for r in notes)
 # The184 specialized kinds are workflow descriptors over independently authored
 # original fluency tasks, not externally adapted source/license classifications.
 out={'status':'metadata-joins-and-refined-math-reviewed-with-four-withdrawn-label-notes','reviewer':'integration_research','inputPath':str(META/'report.json'),'inputSHA256':fh(META/'report.json'),'sourceJoinsSHA256':fh(SRC/'source-joins.json'),'priorIndependentMathSHA256':fh(priorpath),'reviewCodeSHA256':fh(Path(__file__)),'literalParserSHA256':fh(P/'literal_numeric_extended.py'),'counts':{'entries':508,**dict(counts),'refinedLabelsMathematicallyChecked':35,'undefinedGenericSymbolNotesOnWithdrawnRows':4},'records':results,'refinementChecks':checkedrefs,'publicLabelNotes':notes,'provenanceDisposition':'All184 are within the previously independently reviewed original lower batch:134 finite extensions plus50 purposeful replacement tasks. The specialized source kind names construction workflow. Canonical kind original is justified only while complete originalProvenanceKind, lineage, source hash and zero-new-idea metadata remain preserved; no external adaptation or license provenance is relabeled.','replacementPoolDisposition':'The50 purposeful new tasks are replacements for40 withdrawn original IDs across five documented pools. Their withdrawal flags and original construction lineage must survive metadata normalization; the50 are not revisions of those older mathematical tasks.',
'withdrawalDisposition':'The four public-label notation notes occur only on withdrawn noncommuting indices1/3/5/7. All existing indices1..7 withdrawal dispositions must remain; this review neither admits those rows nor turns their metadata presence into capacity. If exposed in a future revision, replace the undefined generic-m wording through a separately source-bound label override.','scope':'Independent completeness/source checks over all508 entries and independent literal-value checks for35 refined labels. Author refinement code and labels were read first, so this is not blinded. The remaining1261 label strings are exact inherited evidence labels and were not reinterpreted as new mathematical hypotheses. Numeric equality validates the described wrong computation, not empirical prevalence of that student mistake. All508 raw hashes rejoin the previously completed independent577 answer/choice review. No source, statement, options, difficulty, lineage or admission flags were modified. Separate AI review, not human/formal certification.'}
 dest=P/'diff-limits-metadata-independent-peer.json';dest.write_text(json.dumps(out,indent=2)+'\n');print(out['counts']);print('reportSHA',fh(dest))
if __name__=='__main__':main()
