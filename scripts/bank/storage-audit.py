#!/usr/bin/env python3
"""Read-only dbstat audit; optionally build a fresh full-membership-only comparison."""
import argparse, hashlib, json, pathlib, sqlite3
p=argparse.ArgumentParser(); p.add_argument('source'); p.add_argument('report'); p.add_argument('--full-only'); p.add_argument('--release',default='cn-2026-11-02-full-v2'); a=p.parse_args()
source=pathlib.Path(a.source); db=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True); db.row_factory=sqlite3.Row
if a.full_only:
    target=pathlib.Path(a.full_only)
    if target.exists(): raise SystemExit('Refusing to overwrite comparison')
    out=sqlite3.connect(target); out.executescript((pathlib.Path(__file__).resolve().parents[2]/'drizzle/0001_problem_bank.sql').read_text())
    for table in ['bank_problems','bank_publication','bank_releases','bank_pools','bank_slots','bank_config','bank_legacy_ids','bank_reports','bank_statistics']:
        query='SELECT * FROM '+table
        params=()
        if table in ['bank_releases','bank_pools','bank_slots']: query+=' WHERE release_id=?'; params=(a.release,)
        for row in db.execute(query,params): out.execute('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in row)+')',tuple(row))
    out.commit(); out.close()
objects=[dict(r) for r in db.execute('SELECT name,count(*) pages,sum(pgsize) allocatedBytes,sum(payload) payloadBytes,sum(unused) unusedBytes FROM dbstat GROUP BY name ORDER BY allocatedBytes DESC')]
tables=[]
for r in db.execute("SELECT name,sql FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
    name=r['name']; count=db.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0]
    # WITHOUT ROWID's primary key IS the table, not an additional write/index.
    indexes=[dict(i) for i in db.execute('PRAGMA index_list("'+name+'")')]
    extra=sum(1 for i in indexes if not ('WITHOUT ROWID' in r['sql'].upper() and i['origin']=='pk'))
    tables.append(dict(table=name,rows=count,additionalIndexes=extra,estimatedRowIndexWrites=count*(1+extra)))
report=dict(path=str(source),bytes=source.stat().st_size,sha256=hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),sqliteVersion=sqlite3.sqlite_version,pageSize=db.execute('PRAGMA page_size').fetchone()[0],pageCount=db.execute('PRAGMA page_count').fetchone()[0],freelistCount=db.execute('PRAGMA freelist_count').fetchone()[0],objects=objects,tables=tables,estimatedRowIndexWrites=sum(t['estimatedRowIndexWrites'] for t in tables),writeEstimateCaveat='Logical inserted rows plus secondary indexes, not measured D1 billing. Excludes schema, receipts, activation, verification scans, retries and application usage.')
if db.execute("SELECT 1 FROM sqlite_schema WHERE name='bank_slots'").fetchone(): report['originalMemberships']=[dict(r) for r in db.execute('SELECT release_id,count(*) slots FROM bank_slots GROUP BY release_id')]
pathlib.Path(a.report).write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({k:report[k] for k in ['bytes','pageCount','freelistCount','estimatedRowIndexWrites']}))
