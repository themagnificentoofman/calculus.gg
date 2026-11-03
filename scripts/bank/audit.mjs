#!/usr/bin/env node
import { DatabaseSync } from 'node:sqlite';
import { writeFileSync, statSync } from 'node:fs';
import { selectBankQuestions } from '../../lib/server/bank-selection.ts';
import { sqliteD1 } from './sqlite-d1.mjs';

const [path = '.bank-data/bank.sqlite', output = '.bank-data/validation-report.json'] = process.argv.slice(2);
const db = new DatabaseSync(path, { readOnly: true });
const release = db.prepare("SELECT r.* FROM bank_releases r JOIN bank_config c ON c.value=r.release_id WHERE c.key='active_release' AND r.state='published'").get();
if (!release) throw Error('No active published release');
const manifest = JSON.parse(release.manifest_json);
const rows = db.prepare(`SELECT b.*,p.state FROM bank_slots s JOIN bank_problems b USING(problem_id,revision)
  JOIN bank_publication p USING(problem_id,revision) WHERE s.release_id=? AND s.tag='*'`);
const coverage = {}, families = {}, techniques = {}, ids = new Set(), semantics = new Set(), hashes = new Set();
let count = 0, humanReviewed = 0;
for (const row of rows.iterate(release.release_id)) {
  const p = JSON.parse(row.payload_json);
  if (row.state !== 'approved' || p.validation.status !== 'passed') throw Error('Unapproved active member');
  count++; humanReviewed += Number(p.validation.humanReviewed);
  ids.add(p.problemId); semantics.add(p.semanticHash); hashes.add(p.contentHash);
  const cell = p.topic + '/' + p.difficulty;
  coverage[cell] = (coverage[cell] || 0) + 1;
  families[p.familyId] = (families[p.familyId] || 0) + 1;
  for (const tag of p.techniqueTags) techniques[tag] = (techniques[tag] || 0) + 1;
}
const same = (a, b) => JSON.stringify(Object.entries(a).sort()) === JSON.stringify(Object.entries(b).sort());
if (count !== manifest.approvedCount || ids.size !== count || semantics.size !== count || hashes.size !== count || !same(coverage, manifest.coverage) || !same(families, manifest.families) || !same(techniques, manifest.techniques)) throw Error('Persisted corpus differs from manifest');
const integrity = db.prepare('PRAGMA integrity_check').all();
if (integrity.length !== 1 || integrity[0].integrity_check !== 'ok' || db.prepare('PRAGMA foreign_key_check').all().length) throw Error('Database integrity failed');
let selectionCases = 0;
for (const cell of Object.keys(coverage)) {
  const [category, difficulty] = cell.split('/');
  const selected = await selectBankQuestions(sqliteD1(db), { category, difficulty, count: 20 });
  if (selected.questions.length !== 20 || new Set(selected.questions.map(q => q.problemId)).size !== 20) throw Error('Selection failed for ' + cell);
  selectionCases++;
}
const report = {
  releaseId: release.release_id, scope: 'Private local SQLite artifact; not a production D1 deployment',
  approvedMaterialized: count, selectable: count, distinctProblemIds: ids.size, distinctSemanticHashes: semantics.size,
  distinctContentHashes: hashes.size, distinctFamilies: Object.keys(families).length,
  maxFamilyShare: Math.max(...Object.values(families)) / count, coverage, families, techniques,
  humanReviewedCount: humanReviewed, databaseBytes: statSync(path).size, integrity: 'ok',
  selectionChecks: { cells: selectionCases, questionsPerRound: 20, distinctWithinEveryRound: true },
  allReleaseStates: db.prepare('SELECT release_id,state,expected_count FROM bank_releases ORDER BY release_id').all(),
  physicalRevisionCount: db.prepare('SELECT count(*) AS n FROM bank_problems').get().n,
  retiredRevisionCount: db.prepare("SELECT count(*) AS n FROM bank_publication WHERE state='retired'").get().n,
  verification: 'The supported importer reconstructs every mathematical record before rendering and publication. This audit checks persisted counts, hashes, coverage, integrity and selection; it does not repeat the mathematical reconstruction.',
  semanticLimits: manifest.deduplication,
  importedExistingCount: manifest.importedExistingCount, openaiCalls: manifest.openaiCalls, openaiCostUSD: manifest.openaiCostUSD,
  productionPublishedCount: null, productionStatus: 'Not measured by this local audit.'
};
writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ approvedMaterialized: count, distinctFamilies: report.distinctFamilies, selectionCases, integrity: 'ok' }));
db.close();
