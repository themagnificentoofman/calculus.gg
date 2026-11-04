"""Apply the separately frozen 58-menu repair to the complete private pool."""
from pathlib import Path
import copy,hashlib,json,sys
from .contract import ROOT,canonical,normalize
from .integration import algebraic_release_runtime

P=ROOT/'scripts/bank/quality/integration/algebraic-options'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readlines(p):return list(map(json.loads,p.read_text().splitlines()))

def main(previous_stage,output):
    stage,out=Path(previous_stage),Path(output);out.mkdir(parents=True,exist_ok=True)
    if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve earlier stage')
    base=readlines(stage/'canonical-previews.jsonl')
    retained=readlines(stage/'retained-originals.jsonl')
    effective={r['problemId']:r for r in retained+base}
    entries=json.loads((stage/'admission-previews.json').read_text())
    entry_by_id={r['problemId']:entries[r['provenance']['authoring']['reviewId']] for r in base}
    joins=json.loads((P/'source-joins.json').read_text())
    raws={hashlib.sha256(canonical(r).encode()).hexdigest():r for r in readlines(P/'sources/combined-candidates.jsonl')}
    domains={(r['route'],r['familyId']):r['indices'] for r in json.loads((P/'catalog.json').read_text())}
    results,failures,replacements=[],[],[]
    for j in joins:
        raw=algebraic_release_runtime.supplement(raws[j['rawHash']],j['route'],j['familyId'],j['index'])
        rawhash=hashlib.sha256(canonical(raw).encode()).hexdigest()
        old=effective[j['sourcePreview']['problemId']]
        assert old['contentHash']==j['sourcePreview']['sourceContentHash']
        assert old['semanticHash']==j['sourcePreview']['semanticHash']
        prior_entry=entry_by_id.get(old['problemId'])
        route='integration-algebraic-'+j['route'];rid='quality-review:'+route+':'+j['familyId']+':'+str(j['index'])
        evidence=P/j['independentReview']['report']
        assert sha(evidence)==j['independentReview']['reportSha256']
        review=copy.deepcopy(prior_entry['review']) if prior_entry else {
            'status':'independently-reviewed','author':'integration_research','reviewer':'root',
            'nearestNeighbor':'Same previously reviewed construction and exposure lineage; repaired options add no new mathematical idea.',
            'qualifiedOlympiad':old['difficulty']=='olympiad','relatedIdeaGroupId':old['pedagogy']['relatedIdeaGroupId'],
            'normalizedLineageKey':old['semanticHash'],
            'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64,
        }
        review.update({'report':str(evidence.relative_to(ROOT)),'reportSha256':sha(evidence),
                       'centralDecision':j['easiestOptionsVisibleRoute'],
                       'easiestOptionsVisibleRoute':j['easiestOptionsVisibleRoute'],
                       'difficultyRationale':j['easiestOptionsVisibleRoute'],
                       'difficulty':j['recommendedDifficulty'],
                       'qualifiedOlympiad':j['recommendedDifficulty']=='olympiad'})
        e={'reviewId':rid,'module':route,'familyId':j['familyId'],'index':j['index'],
           'rawSha256':rawhash,'verifier':'independent-literal-integral-and-six-outward-rational-choice-inequalities-v1',
           'finiteDomain':{'indices':domains[(j['route'],j['familyId'])]},'review':review,
           'supplementalReports':[{'path':str((P/'source-joins.json').relative_to(ROOT)),
                                   'sha256':sha(P/'source-joins.json'),
                                   'purpose':'Exact previous identity, source presentation and independent review joins for the 58-menu repair.'}]}
        if rawhash!=j['rawHash']:
            ap=P.parent/'algebraic-conclusion-amendments.json'
            e['supplementalReports'].append({'path':str(ap.relative_to(ROOT)),'sha256':sha(ap),'purpose':'Exact positive-real algebraic identity for the explicit final conclusion.'})
        if j.get('previous'):
            e['previous']=copy.deepcopy(j['previous'])
            if prior_entry:
                assert all(v==prior_entry['previous'].get(k) for k,v in e['previous'].items())
                e['previous']=copy.deepcopy(prior_entry['previous'])
            if e['previous']['meaningChanged']:
                e['review']['semanticChangeReason']=prior_entry['review']['semanticChangeReason']
        try:
            record=normalize(raw,e);results.append(record);entries[rid]=e
            if prior_entry:entries.pop(prior_entry['reviewId'])
            replacements.append({'oldPreviewProblemId':old['problemId'],'problemId':record['problemId'],
                                 'problemRevision':record['problemRevision'],'rawSha256':rawhash,
                                 'canonicalConstruction':old['pedagogy']['constructionId'],
                                 'sameMathematicalTask':True,'previous':e.get('previous')})
        except Exception as error:failures.append({'reviewId':rid,'error':str(error)})
    replaced={r['oldPreviewProblemId'] for r in replacements}
    records=[r for r in base if r['problemId']not in replaced]+results
    retained=[r for r in retained if r['problemId']not in replaced]
    effective=retained+records
    assert len({r['problemId'] for r in effective})==len(effective)
    for name,rows in [('canonical-previews',records),('retained-originals',retained)]:
        (out/(name+'.jsonl')).write_text(''.join(canonical(r)+'\n' for r in rows))
    (out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n')
    (out/'replacement-joins.json').write_text(json.dumps(replacements,indent=2)+'\n')
    (out/'effective-option-input.jsonl').write_text(''.join(canonical({k:r[k] for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']})+'\n'for r in effective))
    report={'status':'private-not-admitted','records':len(records),'retained':len(retained),
            'effectiveRecords':len(effective),'optionOverlays':len(results),'failures':failures,
            'pending':'Final actual-ID family/form option dispositions and central admission.','imported':0,'active':0}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({**report,'failures':len(failures)}))
    assert not failures and len(effective)==766 and len(results)==58
if __name__=='__main__':main(*sys.argv[1:])
