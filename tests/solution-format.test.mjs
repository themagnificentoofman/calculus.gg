import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeNotation } from '../lib/math-notation.mjs';
import { formatSolutionStep,formatProblemStatement } from '../lib/solution-format.mjs';
import { renderMath } from '../lib/render-math.mjs';

test('natural logarithms and inverse functions use consistent notation without changing bases',()=>{
  assert.equal(normalizeNotation(String.raw`\log x+\log_{10}x+\log _2 x+\operatorname{log}_{b}x+\operatorname{atan}(x)`),String.raw`\ln x+\log_{10}x+\log _2 x+\operatorname{log}_{b}x+\arctan(x)`);
  assert.equal(normalizeNotation(String.raw`\operatorname{asinh}(x)+\operatorname{acos}(x)`),String.raw`\operatorname{arcsinh}(x)+\arccos(x)`);
  for(const name of ['asinh','acosh','atanh','asin','acos','atan'])assert.doesNotThrow(()=>renderMath('\\operatorname{'+name+'}(x)'));
  assert.equal(normalizeNotation(String.raw`\textnormal{The word log and \log are quoted.}`),String.raw`\textnormal{The word log and \log are quoted.}`);
});
test('upright differential normalization is restricted to differential forms',()=>{
  assert.equal(normalizeNotation(String.raw`\frac{dy}{dx}`),String.raw`\frac{\mathrm{d}y}{\mathrm{d}x}`);
  const source=String.raw`\frac{d^{2}}{dx^{2}}f(x)\,dx+\frac{1}{dx}+d x`;
  assert.equal(normalizeNotation(source),String.raw`\frac{\mathrm{d}^{2}}{\mathrm{d}x^{2}}f(x)\,\mathrm{d}x+\frac{1}{dx}+d x`);
  assert.equal(normalizeNotation(normalizeNotation(source)),normalizeNotation(source));
});
test('wrapped prose becomes a normal paragraph, retaining inline mathematics',()=>{
  const blocks=formatSolutionStep(String.raw`\begin{gathered}\textnormal{The cubic integrates to zero}\\\textnormal{on symmetric bounds; cosine is}\\\textnormal{even.}\end{gathered}`);
  assert.equal(blocks.length,1);assert.equal(blocks[0].kind,'paragraph');
  assert.equal(blocks[0].parts.map(p=>p.value).join(''),'The cubic integrates to zero on symmetric bounds; cosine is even.');
  const mixed=formatSolutionStep(String.raw`\textnormal{Define }F(x)=\log x\textnormal{ for }x>0.`)[0];
  assert.equal(mixed.kind,'paragraph');assert.equal(mixed.parts[1].value,String.raw`F(x)=\ln x`);
});
test('text inside mathematical groups never splits an equation',()=>{
  for(const source of [String.raw`\left(\textnormal{distance}\right)`,String.raw`\frac{\textnormal{distance}}{\textnormal{time}}`,String.raw`f(x)=\begin{cases}0,&\textnormal{otherwise},\\x,&x>0.\end{cases}`,String.raw`\left(\frac{\textnormal{a}}x\right)`]){
    const blocks=formatSolutionStep(source);assert.equal(blocks.length,1);assert.equal(blocks[0].kind,'math');assert.equal(blocks[0].value,source);assert.doesNotThrow(()=>renderMath(blocks[0].value,true));
  }
});
test('nested gathered mathematical content remains whole and escaped prose remains text',()=>{
  const source=String.raw`\begin{gathered}\textnormal{Use the following identity.}\\\begin{gathered}a=b\\b=c\end{gathered}\end{gathered}`;
  const blocks=formatSolutionStep(source);assert.equal(blocks.length,2);assert.equal(blocks[1].kind,'math');assert.doesNotThrow(()=>renderMath(blocks[1].value,true));
  assert.equal(formatSolutionStep(String.raw`\textnormal{A \{finite\} set, 50\%, and x\_0.}`)[0].parts[0].value,'A {finite} set, 50%, and x_0.');
});
test('prose boundaries preserve TeX spaces and adjacent gathered environments remain complete',()=>{
 for(const source of [String.raw`x=0\ \textnormal{or}\ x=4`,String.raw`\begin{gathered}\textnormal{First line}\end{gathered}x+1\begin{gathered}\textnormal{Last line}\end{gathered}`])for(const block of formatSolutionStep(source)){
  if(block.kind==='math')assert.doesNotThrow(()=>renderMath(block.value,true));else for(const part of block.parts)if(part.kind==='math')assert.doesNotThrow(()=>renderMath(part.value,false));
 }
 assert.equal(normalizeNotation(String.raw`\frac{d}{dx}\,dx+dt`,{differentialVariables:['x','t']}),String.raw`\frac{\mathrm{d}}{\mathrm{d}x}\,\mathrm{d}x+\mathrm{d}t`);
});
test('statements unwrap nested prose while preserving complete mathematical environments',()=>{
 const source=String.raw`\begin{gathered}\textnormal{Find the tangent}\end{gathered}y=x^2\textnormal{ at }x=1.`;
 const result=formatProblemStatement(source);assert.equal(result.length,1);assert.equal(result[0].kind,'paragraph');
 assert.equal(result[0].parts[0].value,'Find the tangent');assert.equal(result[0].parts[1].value,'y=x^2');
 const nested=formatProblemStatement(String.raw`\begin{gathered}\begin{gathered}\textnormal{First part}\end{gathered}\\\textnormal{second part.}\\f(x)=\begin{cases}0,&x<0,\\x,&x\ge0.\end{cases}\end{gathered}`);
 assert.equal(nested.length,2);assert.equal(nested[0].kind,'paragraph');assert.equal(nested[0].parts.map(p=>p.value).join(''),'First part second part.');
 assert.equal(nested[1].kind,'math');assert.match(nested[1].value,/begin\{cases\}/);assert.doesNotThrow(()=>renderMath(nested[1].value,true));
 const fraction=String.raw`\frac{\textnormal{distance}}{\textnormal{time}}`;
 assert.deepEqual(formatProblemStatement(fraction),[{kind:'math',value:fraction}]);
 const defining=String.raw`\operatorname{erf}(x)=\frac2{\sqrt\pi}\int_0^x e^{-t^2}\,\mathrm{d}t=\sum_{k=0}^{\infty}a_kx^k.\textnormal{Find the coefficient.}`;
 assert.equal(formatProblemStatement(defining)[0].kind,'math');
});
