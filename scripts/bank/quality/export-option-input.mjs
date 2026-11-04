#!/usr/bin/env node
// Private audit input: reconstruct the pinned bank and apply its actual presenter.
import {DatabaseSync} from 'node:sqlite';
import {gunzipSync} from 'node:zlib';
import {openSync,writeSync,closeSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {reconstruct} from '../../../lib/bank/compact-codec.mjs';
import {features} from './option-audit.mjs';
const [database,source,out]=process.argv.slice(2);if(!out||existsSync(out))throw Error('Supply pinned database, pinned source and NEW private output JSONL');
const {presentBankProblem}=await import(pathToFileURL(resolve(source,'lib/server/solution-presentation.mjs'))),db=new DatabaseSync(database,{readOnly:true}),file=openSync(out,'wx');let count=0;
function answerForm(p){
 const math=p.choices.find(c=>c.choiceId===p.answerChoiceId).math,f=features(math);
 if(f.integer!==null)return 'integer';if(f.numeric!==null)return 'rational-or-decimal';if(/\\begin\{(?:cases|matrix|[bpv]matrix)\}/.test(math))return 'piecewise-or-matrix';if(/[xyt]/.test(math.replace(/\\[A-Za-z]+/g,'')))return 'function-expression';return 'exact-constant-expression';
}
try{for(const row of db.prepare('SELECT b.*,s.metadata_json FROM cbank_problems b JOIN cbank_shared s USING(shared_id) JOIN cbank_publication u USING(problem_ref) WHERE u.state=\'approved\' ORDER BY problem_ref').iterate()){
 const p=presentBankProblem(reconstruct(row,JSON.parse(gunzipSync(row.payload_gzip).toString('utf8'))));
 writeSync(file,JSON.stringify({problemId:p.problemId,problemRevision:p.problemRevision,contentHash:p.contentHash,familyId:p.familyId,topic:p.topic,difficulty:p.difficulty,parameters:p.parameters,choices:p.choices,answerChoiceId:p.answerChoiceId,pedagogy:{answerForm:answerForm(p)}})+'\n');count++;
}}finally{closeSync(file);db.close();}console.log(JSON.stringify({records:count,source:resolve(source),output:resolve(out),scope:'Private option-only input; no gameplay/production requests or writes.'}));
