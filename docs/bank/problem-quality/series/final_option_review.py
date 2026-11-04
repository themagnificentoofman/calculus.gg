"""Read-only review/binding of the final 705 effective series option pools."""
from pathlib import Path
import json,hashlib,math,re
from series_option_disposition import DISPOSITIONS,pool
P=Path(__file__).resolve().parent;W=P.parents[1]
F=W/'problem-quality/.bank-data/quality/series-previews-v4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(r):return hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def read(p):return list(map(json.loads,p.read_text().splitlines()))
screen=json.loads((F/'effective-option-screen.json').read_text())
canonical={r['problemId']:r for r in read(W/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl')+read(F/'canonical-previews.jsonl')+read(F.parent/'adapted-pilot-admitted.jsonl')}
effective=read(F/'effective-option-input.jsonl');rows=[];families={};negative=[];binomial=[]
patches=json.loads((P/'series-negative-binomial-option-patches.json').read_text())
def clean(t):return t.replace('\\\\','\\').replace(' ','')
for e in effective:
 r=canonical[e['problemId']]
 normalized=[dict(c,math=c['math'].replace('\\log','\\ln').replace('\\operatorname{atan}','\\arctan')) for c in r['choices']]
 assert (r['choices']==e['choices'] or normalized==e['choices']) and r['answerChoiceId']==e['answerChoiceId'],r['problemId']
 fid=r['familyId'];f=screen['families'][fid];slug=fid.split('-',3)[-1]
 if fid not in families:
  if fid=='m3-series-easy-binomial-total':
   verdict='retain-Easy-with-parity-disposition'
   reason='The exact identity is the binomial theorem at one: the sum is 2^n. Its being a square depends on the displayed exponent parity: five of the ten answers are squares and five are not. A square-only rule is therefore not a family-wide selector. Several odd-exponent cases contain the wrong adjacent power of two as their sole square, so the same rule points to a wrong option. The held-out 65% (three unique correct predictions among five cases) does not replicate a training-selected rule: training selected divisibility by32, whose held-out tie-aware score is51.7%. Using the parity of n and the power-of-two structure is mathematical reasoning appropriate to Easy, rather than evidence of an advanced task. The finite small sample does not prove absence of other cues.'
  elif fid=='m3-series-medium-negative-binomial':
   verdict='repaired-final-IDs-cleared-for-screened-cues'
   reason='All ten final effective records match the independently peer-reviewed v2 authored option pools, with exact answers and two distinct rational-cube alternatives. Cube status leaves two options in every case, with the correct cube above or below its competitor. The former unique-cube and repeated longest-TeX clues are absent. The final screen has no flags; its selected cube rule ties at50% in each half. This is bounded clearance of the screened clues, not proof against all possible option heuristics.'
  elif slug in DISPOSITIONS:
   verdict,reason=DISPOSITIONS[slug]
   if slug=='weighted-binomial-total':reason=reason.replace('the training-selected position rule does not replicate','the new training-selected square-minority rule drops from65% to15% held out')
  elif f['flags']:
   assert all(q['rule'].startswith('shuffled-position-') for q in f['flags']), (fid,f['flags'])
   verdict='retain-random-position-only-diagnostic'
   reason='All flags for this family concern the deterministic audit shuffle position. Actual play freshly shuffles options; these positions are not a mathematical property of the option content. Small held-out halves can produce75–80% by chance. The training-selected rule and held-out results are retained as evidence, with no manual answer-position balancing.'
  elif f['items']<=2:
   verdict='tiny-finite-domain-no-statistical-clearance'
   reason='One or two effective items cannot support a meaningful training/held-out inference. The individual exact mathematics and options-visible fit are covered by their separate source-bound review; the absence of a screen flag is not statistical evidence of robust option quality. No additional idea or repeated practice capacity is inferred.'
  else:
   verdict='no-flag-in-bounded-screen'
   reason='No configured option-only heuristic exceeded the report threshold on this actual effective pool. This preserves the independent mathematics and fit verdict; it does not establish absence of untested cues. Unsupported numeric expressions remain inapplicable, rather than silently counted as passes.'
  families[fid]={'items':f['items'],'flags':f['flags'],'selectedUsingTrainingOnly':f['selectedUsingTrainingOnly'],'disposition':verdict,'reason':reason}
 q={'problemId':r['problemId'],'familyId':fid,'problemRevision':r.get('problemRevision'),'contentHash':r['contentHash'],'semanticHash':r['semanticHash'],'rawHash':raw(r),'effectiveInputRawHash':raw(e),'optionPoolHash':raw({'choices':e['choices'],'answerChoiceId':e['answerChoiceId']}),'sourceToEffectiveNotationOnly':r['choices']!=e['choices'],'familyDisposition':families[fid]['disposition']}
 rows.append(q)
 if fid=='m3-series-easy-binomial-total':
  n=r['parameters']['instance']+4;a=next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']);assert int(a)==sum(math.comb(n,k) for k in range(n+1))==2**n
  vals=[int(c['math']) for c in r['choices']];assert len(set(vals))==4
  squares=[c['choiceId'] for c in r['choices'] if math.isqrt(int(c['math']))**2==int(c['math'])]
  binomial.append(q|{'n':n,'independentAnswer':2**n,'squareChoiceIds':squares,'correctIsSquare':n%2==0,'allSixPairInequalities':True})
 if fid=='m3-series-medium-negative-binomial':
  m=r['parameters']['instance']+4;A,_=pool(m)
  matches=[p for p in patches if p['independentExactAnswer']==__import__('sympy').srepr(A)];assert len(matches)==1
  patch=matches[0];assert sorted(clean(c['math']) for c in r['choices'])==sorted(clean(c['math']) for c in patch['choices'])
  correct=next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']);assert clean(correct)==clean(next(c['math'] for c in patch['choices'] if c['choiceId']==patch['answerChoiceId']))
  assert not f['flags'];negative.append(q|{'m':m,'peerReviewedPatchRawHash':raw(patch),'previousProblemId':patch['problemId'],'exactPoolAndAnswerMatch':True})
assert len(rows)==705 and len(negative)==10 and len(binomial)==10
byid={r['problemId']:r for r in rows};answerForms={}
for form,f in screen['answerForms'].items():
 ids=f['trainingIds']+f['heldoutIds'];bindings=[byid[k] for k in ids];assert len(ids)==f['items']
 if f['flags']:
  assert form=='extended-real' and f['items']==8
  assert {canonical[k]['familyId'] for k in ids}=={'m3-series-easy-ratio-test-data'}
  categories={phase:[next(c['math'] for c in canonical[k]['choices'] if c['choiceId']==canonical[k]['answerChoiceId']) for k in f[phase+'Ids']] for phase in ['training','heldout']}
  infinityCounts={phase:sum('infty' in a for a in answers) for phase,answers in categories.items()}
  assert infinityCounts=={'training':1,'heldout':3}
  verdict='retain-with-balanced-factorial-category-disposition'
  reason='This answer-form stratum contains the eight retained ratio-test-data cases, with four zero and four infinity answers. Numerator factorial produces infinity; denominator factorial produces zero. Infinity is the unique long/noninteger command in each option set, but is wrong in half the actual stratum. The fixed split contains one infinity in training and three in held-out, exactly explaining the length-max and integer-min rule moving from25% to75%; these are opposite category mixtures, not replication. The training-selected shuffled-position rule falls from100% to50%. Length-minority62.5% is another post-hoc small-half diagnostic. Retain Easy and preserve the category-based proof, without balancing random positions or claiming a statistical guarantee.'
 else:
  verdict='no-flag-in-bounded-answer-form-screen';reason='No configured heuristic is flagged within this actual answer-form stratum. Mathematical and difficulty review remain per-source; pooled nonflags cannot override any family flag, and unsupported numerical expressions remain inapplicable.'
  infinityCounts=None
 answerForms[form]={'items':f['items'],'flags':f['flags'],'selectedUsingTrainingOnly':f['selectedUsingTrainingOnly'],'disposition':verdict,'reason':reason,'infinityCountsBySplit':infinityCounts,'records':bindings}
report={'scope':'Independent source-bound disposition for all705 final effective series records and all four answer-form strata, including every flagged family, random-position-only diagnostics, tiny finite domains, and ten actual final-ID option repairs. No app or immutable source changed.','inputs':{n:sha(F/n) for n in ['effective-option-input.jsonl','effective-option-screen.json','canonical-previews.jsonl']},'records':rows,'families':families,'answerForms':answerForms,'binomialTotalIndependentChecks':binomial,'negativeBinomialFinalIDChecks':negative,'limitations':screen['limitations']+['This separate AI review is not a human review or formal proof. Post-hoc held-out maxima are not the same as a rule selected on training and replicated. Numerical-form screens do not understand arbitrary symbolic expressions.'],'sourceRecipeSha256':sha(Path(__file__))}
(P/'series-final-option-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('705 effective source bindings;',len(families),'families; ten final negative-binomial pools cleared; ten binomial answers checked')
