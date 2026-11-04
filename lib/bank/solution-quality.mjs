import { normalizeNotation, braced } from '../math-notation.mjs';
import { normalizeMath, renderMath } from '../render-math.mjs';
import { formatSolutionStep } from '../solution-format.mjs';

export const SOLUTION_QUALITY_VERSION='worked-solutions-v1';
const norm=s=>normalizeNotation(normalizeMath(s)).replace(/\s+/g,'');
export function solutionQualityIssues(problem,{render=true}={}) {
  const issues=[],steps=problem.solutionSteps,answer=problem.choices?.find(c=>c.choiceId===problem.answerChoiceId)?.math;
  if(!Array.isArray(steps)||steps.length<2||steps.length>40)return ['A solution needs a bounded derivation and a final answer.'];
  if(!answer||norm(steps.at(-1))!==norm(answer))issues.push('The explicit conclusion must match the verified correct choice.');
  const joined=[problem.statement,...steps].join('\n');
  if(steps.some(s=>/^\\text(?:normal)?\{(?:Here\s*|In this derivation,\s*)\}m\s*=/.test(s)))issues.push('Remove the generator-parameter preface; define a mathematical role where needed.');
  if(steps.some(s=>/F\(b\)\s*-\s*F\(a\)/.test(s))&&(!/\ba\s*=/.test(joined)||!/\bb\s*=/.test(joined)))issues.push('Connect both endpoint symbols to the displayed bounds.');
  for(const [i,step] of steps.entries()) {
    if(typeof step!=='string'||!step.trim()||step.length>8000){issues.push(`Step ${i+1} is empty or exceeds its bound.`);continue;}
    if(normalizeNotation(step)!==step)issues.push(`Step ${i+1} does not use canonical notation.`);
    if(/\\begin\{gathered\}\s*\\text(?:normal)?\{/.test(step))issues.push(`Step ${i+1} hard-wraps prose inside an equation.`);
    for(let at=0;at<step.length;at++) {
      const command=/^\\(?:textnormal|text|textrm)\{/.exec(step.slice(at));if(!command)continue;
      const group=braced(step,at+command[0].length-1);if(!group)continue;
      if(/\b[A-Za-z]\s*(?:\^|_|=|<=|>=|->|\*|\/)\s*[\w({+\-]/.test(group.body)||/\\textasciicircum/.test(group.body))issues.push(`Step ${i+1} hides a formula in plain prose.`);
      at=group.end-1;
    }
    try {
      if(!render)continue;
      renderMath(step,true);
      for(const block of formatSolutionStep(step))if(block.kind==='math')renderMath(block.value,true);else for(const p of block.parts)if(p.kind==='math')renderMath(p.value,false);
    }catch {issues.push(`Step ${i+1} cannot be rendered as complete prose and mathematics.`);}
  }
  return [...new Set(issues)];
}
export function assertSolutionQuality(problem,options) {
  if(problem.solutionQuality?.version!==SOLUTION_QUALITY_VERSION||!problem.solutionQuality?.auditId||!problem.solutionQuality?.sourceContentHash)throw Error('A source-bound mathematical and editorial solution review is required.');
  const issues=solutionQualityIssues(problem,options);if(issues.length)throw Error('Solution admission failed: '+issues.join(' '));
  return problem;
}
