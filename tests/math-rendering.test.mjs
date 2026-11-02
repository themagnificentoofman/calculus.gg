import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'vite';
import { renderMath } from '../lib/render-math.mjs';

const samples = [
  String.raw`\int_0^{1/2} \frac{x^2}{\sqrt{1-x^2}}\,dx`,
  String.raw`\frac{\pi}{12}-\frac{\sqrt{3}}{8}`,
  String.raw`\textnormal{Let }u=x^3+1\textnormal{, then }du=3x^2\,dx`,
  String.raw`\begin{pmatrix}1&2\\3&4\end{pmatrix}`,
];

test('production-minified math renders the same as unbundled KaTeX', async () => {
  const result = await build({
    configFile: false, logLevel: 'silent',
    build: { write: false, minify: true, lib: { entry: 'lib/render-math.mjs', formats: ['es'] } },
  });
  const chunk = result[0].output.find(item => item.type === 'chunk' && item.isEntry);
  const bundled = await import('data:text/javascript;base64,' + Buffer.from(chunk.code).toString('base64'));
  for (const math of samples) {
    assert.equal(bundled.renderMath(math, true), renderMath(math, true));
  }
  assert.throws(() => bundled.renderMath(String.raw`\notARealCommand{x}`), /Undefined control sequence/);
  assert.ok(bundled.renderMath(String.raw`\href{javascript:alert(1)}{click}`).includes('href=') === false);
});

import { renderingSamples } from './math-fixtures.mjs';
import { normalizeMath, questionMathIsRenderable } from '../lib/render-math.mjs';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { mkdir, writeFile, unlink } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

test('the actual minified MathDisplay preserves complete nested expressions in inline and block layouts', async () => {
  const result = await build({
    configFile: false, logLevel: 'silent',
    resolve: { alias: { '@': process.cwd() } },
    build: { write: false, minify: true, lib: { entry: 'components/MathDisplay.tsx', formats: ['es'] }, rolldownOptions: { external: ['react', 'react/jsx-runtime'] } },
  });
  const chunk = result[0].output.find(item => item.type === 'chunk' && item.isEntry);
  await mkdir('.sites-runtime/tests', { recursive: true });
  const filename = path.resolve('.sites-runtime/tests/math-display.mjs');
  await writeFile(filename, chunk.code);
  try {
    const { MathDisplay } = await import(pathToFileURL(filename).href + '?test=' + Date.now());
    // The four modes share this component for inline options and block problems/explanations.
    for (const { name, math } of renderingSamples) for (const block of [false, true]) {
      const html = renderToStaticMarkup(createElement(MathDisplay, { math, block }));
      assert.ok(html.includes(renderMath(math, block)), name);
      assert.ok(!html.includes('math-source'), name);
      assert.ok(!html.includes('Math Render Error'), name);
    }
    const invalid = renderToStaticMarkup(createElement(MathDisplay, { math: '<script>alert(1)</script>\\unsupported{x}' }));
    assert.ok(invalid.includes('math-source'));
    assert.ok(invalid.includes('&lt;script&gt;'));
    assert.ok(!invalid.includes('<script>'));
    const next = renderToStaticMarkup(createElement(MathDisplay, { math: String.raw`\frac{x^3}{3}+C` }));
    assert.ok(!next.includes('math-source'));
  } finally { await unlink(filename); }
});

test('question render validation checks the problem, every option and every explanation step', () => {
  const q = { latexProblem: 'x', options: ['1','2','3','4'], explanation: [String.raw`\textnormal{Set }n=2.`] };
  assert.ok(questionMathIsRenderable(q));
  assert.equal(questionMathIsRenderable({ ...q, latexProblem: String.raw`\frac{1}{` }), false);
  assert.equal(questionMathIsRenderable({ ...q, options: ['1',String.raw`\unknown{x}`,'3','4'] }), false);
  assert.equal(questionMathIsRenderable({ ...q, explanation: ['x=1',String.raw`\frac{1}{`] }), false);
});


test('legacy JSON control escapes recover the intended commands before trimming', () => {
  assert.equal(normalizeMath(JSON.parse(String.raw`"\frac{d}{dx}\bigl(\tan x\bigr)"`)), String.raw`\frac{d}{dx}\bigl(\tan x\bigr)`);
  assert.equal(normalizeMath(JSON.parse(String.raw`"\textnormal{Use }\frac{x^3}{3}+C"`)), String.raw`\textnormal{Use }\frac{x^3}{3}+C`);
  assert.equal(normalizeMath('x +\ny'), 'x +\ny');
  assert.equal(questionMathIsRenderable({latexProblem:'$$',options:['1','2','3','4'],explanation:['x=1']}),false);
});

test('post-match review preserves the submitted answer and renders legacy and structured explanations', async () => {
  const result = await build({
    configFile: false, logLevel: 'silent',
    resolve: { alias: { '@': process.cwd() } },
    build: { write: false, minify: true, lib: { entry: 'components/LastAnswerReview.tsx', formats: ['es'] }, rolldownOptions: { external: ['react', 'react/jsx-runtime'] } },
  });
  const chunk = result[0].output.find(item => item.type === 'chunk' && item.isEntry);
  await mkdir('.sites-runtime/tests', { recursive: true });
  const filename = path.resolve('.sites-runtime/tests/last-answer-review.mjs');
  await writeFile(filename, chunk.code);
  try {
    const { LastAnswerReview } = await import(pathToFileURL(filename).href + '?test=' + Date.now());
    assert.equal(renderToStaticMarkup(createElement(LastAnswerReview, { answer: null })), '');
    const question = {
      latexProblem: String.raw`\int x^2\,dx`,
      options: [String.raw`\frac{x^3}{3}+C`, String.raw`\frac{x^2}{2}+C`],
      correctIndex: 0,
    };
    for (const explanation of [
      JSON.parse(String.raw`"\textnormal{Use }\frac{x^3}{3}+C"`),
      [String.raw`\textnormal{Power rule: }\frac{x^{2+1}}{2+1}+C`, String.raw`\underbrace{\frac{x^3}{3}}_{\text{antiderivative}}+C`],
    ]) for (const selectedOption of [0, 1]) {
      const html = renderToStaticMarkup(createElement(LastAnswerReview, { answer: { question: { ...question, explanation }, selectedOption } }));
      assert.ok(html.includes('Review last answer'));
      assert.ok(html.includes(selectedOption === 0 ? 'Your answer · Correct' : 'Your answer · Incorrect'));
      assert.equal(html.includes('Correct answer'), selectedOption === 1);
      for (const math of [question.latexProblem, question.options[selectedOption], ...(Array.isArray(explanation) ? explanation : [explanation])]) {
        assert.ok(html.includes(renderMath(normalizeMath(math), true)));
      }
      assert.ok(!html.includes('math-source'));
    }
  } finally { await unlink(filename); }
});
