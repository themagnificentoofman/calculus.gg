"""Build actual-ID private previews from the frozen 1,069 D/L review records.

This stage does not register, import, or activate content. It joins each record
to its exact independent review and the conservative construction disposition.
"""
from pathlib import Path
import copy, hashlib, json, sys
from .contract import ROOT, canonical, normalize

P = ROOT / 'scripts/bank/quality/diff-limits'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def identity(row): return row['route'], row['familyId'], row['index']

def main(output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'canonical-previews.jsonl').exists():
        raise ValueError('Preserve earlier preview stages')
    joins = [r for r in json.loads((P/'source-joins.json').read_text())['records']
             if r['route'].startswith('diff-limits-')]
    manifest = json.loads((P/'review-manifest.json').read_text())
    reviews = {identity(r): r for r in manifest['records']}
    lineage = json.loads((P/'lineage-dispositions.json').read_text())
    originals = {r['problemId']: r for r in lineage['instances'] if r['kind']=='original-record'}
    new = {r['rawHash']: r for r in lineage['instances'] if r['kind']!='original-record'}
    lower = json.loads((P/'evidence/peer-lower577.json').read_text())
    lower_rows = {r['rawHash']: r for r in lower['records']}
    lower_families = {r['familyId']: r for r in lower['familyReviews']}
    metadata_path=ROOT/'scripts/bank/quality/editorial/diff-limits/adapter-supplements.json'
    metadata=json.loads(metadata_path.read_text())
    technique_path=ROOT/'scripts/bank/quality/editorial-technique-labels.json'
    technique_aliases=json.loads(technique_path.read_text())['aliases']
    sources, domains = {}, {}
    for j in joins:
        sources.setdefault(j['sourceFile'], None)
        domains.setdefault((j['route'], j['familyId']), []).append(j['index'])
    sources = {f: json.loads((P/f).read_text()) for f in sources}
    records, entries, failures, dispositions, excluded = [], {}, [], [], []
    for j in joins:
        raw = sources[j['sourceFile']][j['sourceRecordIndex']]
        h = hashlib.sha256(canonical(raw).encode()).hexdigest()
        assert h == j['rawSha256']
        peer = reviews[identity(j)]
        assert peer['rawSha256']==h and peer['status']=='independently-reviewed'
        evidence = P / peer['evidence']['file']
        assert evidence.is_file()
        lin = originals[j['previous']['problemId']] if j.get('previous') else new[h]
        if lin['disposition'].startswith('withdraw-'):
            excluded.append({'route':j['route'],'familyId':j['familyId'],'index':j['index'],
                             'rawSha256':h,'problemId':j['previous']['problemId'],
                             'reason':lin['disposition']})
            continue
        meta = raw.get('reviewMetadata', {})
        low = lower_rows.get(h)
        family = lower_families.get(j['familyId'], {})
        route = low['easiestOptionsVisibleRoute'] if low else lin['centralDecision']
        nearest = family.get('nearestNeighbor') or meta.get('nearestNeighborDistinction') or raw['pedagogy'].get('nearestNeighborDistinction')
        assert nearest, j['familyId']
        level = low['recommendedDifficulty'] if low else lin['recommendedDifficulty']
        assert level == lin['recommendedDifficulty'], (j['familyId'],j['index'])
        rid = 'quality-review:'+':'.join(map(str,identity(j)))
        entry = {
            'reviewId':rid,'module':j['route'],'familyId':j['familyId'],'index':j['index'],
            'rawSha256':h,'verifier':'isolated-finite-reconstruction-and-independent-differentiation-limits-review-v1',
            'finiteDomain':{'indices':sorted(domains[(j['route'],j['familyId'])])},
            'review':{
                'status':'independently-reviewed','author':'coverage_research',
                'reviewer':'root-source-and-integration-independent-reviews',
                'report':str(evidence.relative_to(ROOT)),'reportSha256':sha(evidence),
                'centralDecision':lin['centralDecision'],'nearestNeighbor':nearest,
                'easiestOptionsVisibleRoute':route,
                'difficultyRationale':family.get('difficultyRationale',route),
                'difficulty':level,'qualifiedOlympiad':lin['qualifiedOlympiad'],
                'relatedIdeaGroupId':lin['relatedIdeaGroupId'],
                'structuralSignature':lin['structuralSignature'],
                'primaryTechnique':lin['primaryTechnique'],
                'normalizedLineageKey':lin['normalizedTaskKey'],
                'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN',
                'optionAuditSha256':'0'*64,
            },
            'supplementalReports':[
                {'path':str((P/f).relative_to(ROOT)),'sha256':sha(P/f),'purpose':purpose}
                for f,purpose in [
                    ('source-joins.json','Exact frozen constructor, raw item and previous-identity joins.'),
                    ('review-manifest.json','Complete finite independent-review coverage.'),
                    ('lineage-dispositions.json','Conservative construction, related idea, normalized task and options-visible classification.'),
                ]
            ]
        }
        if rid in metadata:
            entry.update(copy.deepcopy(metadata[rid]))
            assert entry['editorialSupplement']['rawSha256']==h
            mp=ROOT/entry['editorialSupplement']['report']
            assert sha(mp)==entry['editorialSupplement']['reportSha256']
        if lin['primaryTechnique']in technique_aliases:
            entry['review']['primaryTechnique']=technique_aliases[lin['primaryTechnique']]
            entry['supplementalReports'].append({'path':str(technique_path.relative_to(ROOT)),'sha256':sha(technique_path),'purpose':'Bounded spelling alias for the same reviewed primary mathematical method.'})
        if j.get('previous'):
            entry['previous']=copy.deepcopy(j['previous'])
            assert entry['previous']['sourceContentHash']==lin['sourceContentHash']
            if entry['previous']['meaningChanged']:
                entry['review']['semanticChangeReason']=raw.get('review',{}).get('semanticChangeReason') or raw.get('semanticChangeReason')
        try:
            record=normalize(raw,entry)
            records.append(record);entries[rid]=entry
            dispositions.append({'problemId':record['problemId'],'problemRevision':record['problemRevision'],
                                 'sourceRawSha256':h,**{k:lin[k] for k in ['constructionFamilyId','relatedIdeaGroupId','normalizedTaskKey','qualifiedOlympiad','recommendedDifficulty']}})
        except Exception as error:
            failures.append({'reviewId':rid,'error':str(error)})
    oldpath=ROOT.parent/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl'
    assert sha(oldpath)=='1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677'
    replaced={e['previous']['problemId'] for e in entries.values() if e.get('previous')}
    retired={p for p,r in originals.items() if r['disposition'].startswith('withdraw-')}
    assert not replaced & retired
    retained=[r for r in map(json.loads,oldpath.read_text().splitlines())
              if r['topic'] in ['differentiation','limits'] and r['problemId'] not in replaced|retired]
    effective=retained+records
    assert len({r['problemId'] for r in effective})==len(effective)
    for name,rows in [('canonical-previews',records),('retained-originals',retained)]:
        (out/(name+'.jsonl')).write_text(''.join(canonical(r)+'\n' for r in rows))
    (out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n')
    (out/'item-dispositions.json').write_text(json.dumps({'records':dispositions,'retiredProblemIds':sorted(retired),'excludedReviewedRecords':excluded},indent=2)+'\n')
    (out/'effective-option-input.jsonl').write_text(''.join(canonical({k:r[k] for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']})+'\n' for r in effective))
    report={'status':'private-not-admitted','records':len(records),'retained':len(retained),
            'effectiveRecords':len(effective),'retired':len(retired),'reviewedInventory':len(joins),
            'excludedReviewedRecords':len(excluded),'failures':failures,
            'pending':'Actual-ID full-family option dispositions, global normalized coverage and final admission.',
            'imported':0,'active':0}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({**report,'failures':len(failures)}))
    assert not failures and len(records)==1062 and len(excluded)==7 and len(effective)==1405

if __name__=='__main__':main(sys.argv[1])
