#!/usr/bin/env node
// Local-only visual QA using the actual React components and app stylesheet.
import {build} from 'esbuild';
import {createServer} from 'node:http';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import postcss from 'postcss';
import tailwind from '@tailwindcss/postcss';
import {presentBankProblem} from '../../lib/server/solution-presentation.mjs';
const [artifact,port='4177']=process.argv.slice(2);
if(!artifact)throw Error('Usage: preview-solutions.mjs ARTIFACT.jsonl [PORT]');
const rows=readFileSync(artifact,'utf8').trim().split('\n').map(JSON.parse);
const legacy=JSON.parse(readFileSync('tests/fixtures/bank/review-samples.json'));
const ids=['cn_c05d5e5ff7186cb58716'];
const picked=[...ids.map(id=>rows.find(p=>p.problemId===id)),rows.find(p=>p.familyId==='io3-principal-value'),rows.find(p=>p.familyId==='io3-bernoulli-product'),rows.find(p=>p.familyId.endsWith('darboux-oscillator')),rows.find(p=>p.familyId.endsWith('path-dependent-directional')),legacy.find(p=>p.familyId==='polynomial-exponential')].filter(Boolean).map(p=>presentBankProblem(p));
const directory=resolve('outputs/solution-preview');mkdirSync(directory,{recursive:true});
await build({stdin:{contents:`import React from 'react';import{renderToStaticMarkup}from'react-dom/server';import{MathDisplay}from'./components/MathDisplay';import{SolutionSteps}from'./components/SolutionSteps';export const render=ps=>renderToStaticMarkup(<main className="mx-auto max-w-4xl space-y-8 px-4 py-8 sm:px-8"><h1 className="text-3xl font-bold">Worked solutions</h1><p className="text-zinc-400">Local review of the actual game components.</p>{ps.map(p=><section key={p.problemId} className="min-w-0 rounded-3xl border border-zinc-700 bg-zinc-900 p-5 sm:p-8"><p className="mb-6 text-sm text-zinc-400">{p.topic} · {p.difficulty}</p><MathDisplay math={p.statement} block/><div className="my-6 grid grid-cols-1 gap-3 sm:grid-cols-2">{p.choices.map((c,i)=><div key={c.choiceId} className={'min-w-0 rounded-xl border p-4 '+(c.choiceId===p.answerChoiceId?'border-emerald-500 bg-emerald-500/10 text-emerald-300':'border-zinc-700')}><span className="mr-3">{String.fromCharCode(65+i)}</span><MathDisplay math={c.math}/></div>)}</div><div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-5"><h2 className="mb-5 text-lg text-emerald-400">Explanation</h2><SolutionSteps steps={p.solutionSteps}/></div></section>)}</main>);`,resolveDir:process.cwd(),loader:'tsx'},outfile:resolve(directory,'components.mjs'),bundle:true,format:'esm',platform:'node',packages:'external',minify:true});
const {render}=await import(pathToFileURL(resolve(directory,'components.mjs')).href);
const css=await postcss([tailwind({base:process.cwd()})]).process(readFileSync('app/globals.css','utf8'),{from:resolve('app/globals.css')});
writeFileSync(resolve(directory,'style.css'),css.css);
const html='<!doctype html><html class="dark"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Calculus Ninja solution review</title><link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="/katex.min.css"><body>'+render(picked)+'</body></html>';
writeFileSync(resolve(directory,'index.html'),html);
createServer((req,res)=>{try{if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end(html);}else if(req.url==='/style.css'){res.setHeader('Content-Type','text/css');res.end(css.css);}else if(req.url==='/katex.min.css'){res.setHeader('Content-Type','text/css');res.end(readFileSync('node_modules/katex/dist/katex.min.css'));}else if(/^\/fonts\/[\w-]+\.(woff2?|ttf)$/.test(req.url)){res.end(readFileSync(resolve('node_modules/katex/dist'+req.url)));}else{res.statusCode=404;res.end();}}catch{res.statusCode=500;res.end();}}).listen(Number(port),'127.0.0.1',()=>console.log('Local: http://127.0.0.1:'+port));
