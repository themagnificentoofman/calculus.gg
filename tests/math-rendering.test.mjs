import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'vite';
import { renderMath } from '../lib/render-math.ts';

const samples = [
  String.raw`\int_0^{1/2} \frac{x^2}{\sqrt{1-x^2}}\,dx`,
  String.raw`\frac{\pi}{12}-\frac{\sqrt{3}}{8}`,
  String.raw`\textnormal{Let }u=x^3+1\textnormal{, then }du=3x^2\,dx`,
  String.raw`\begin{pmatrix}1&2\\3&4\end{pmatrix}`,
];

test('production-minified math renders the same as unbundled KaTeX', async () => {
  const result = await build({
    configFile: false, logLevel: 'silent',
    build: { write: false, minify: true, lib: { entry: 'lib/render-math.ts', formats: ['es'] } },
  });
  const chunk = result[0].output.find(item => item.type === 'chunk' && item.isEntry);
  const bundled = await import('data:text/javascript;base64,' + Buffer.from(chunk.code).toString('base64'));
  for (const math of samples) {
    assert.equal(bundled.renderMath(math, true), renderMath(math, true));
  }
  assert.throws(() => bundled.renderMath(String.raw`\notARealCommand{x}`), /Undefined control sequence/);
  assert.ok(bundled.renderMath(String.raw`\href{javascript:alert(1)}{click}`).includes('href=') === false);
});
