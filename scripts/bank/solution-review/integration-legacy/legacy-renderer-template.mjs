// RECIPES is prepended by the offline generator. No filesystem or CAS at runtime.
const text = (s) => `\\text{${s}}`;
const natural = (s) => s.replaceAll('\\log', '\\ln').replaceAll('\\operatorname{atan}', '\\arctan');
const group = (s) => `\\left(${s}\\right)`;
const combination = (coefficients, values) => coefficients.map((v,i)=>`${v}\\cdot ${group(natural(values[i]))}`).join('+');
const finalAnswer = (record) => {
  const choices = record.choices.filter(c=>c.choiceId===record.answerChoiceId);
  if (choices.length!==1) throw new Error('Missing or ambiguous answer choice');
  return natural(choices[0].math);
};
function coefficients(record) {
  const p=record.parameters;
  if (!p || Object.keys(p).sort().join(',')!=='a,b,c' || ['a','b','c'].some(k=>!Number.isInteger(p[k]) || p[k]<1 || p[k]>16)) throw new Error('Parameters outside certified legacy domain');
  return [p.a,p.b,p.c];
}
export function supports(record) {
  return record?.templateVersion==='original-linear-families-v2' && Object.hasOwn(RECIPES,record.familyId);
}
function specialSolution(record) {
  const [a,b,c]=coefficients(record);const A=finalAnswer(record);
  if (record.familyId==='hidden-riccati') return [
    `p(x):=${a}x+\\frac{${b}}x,\\quad z(x):=u(x)-p(x)`,
    `z^{\\prime}=u^{\\prime}-p^{\\prime}=(u-p)^2=z^2,\\quad z(1)=${c}`,
    `-\\frac1z=x-1-\\frac1{${c}},\\quad z(x)=\\frac{${c}}{1-${c}(x-1)}`,
    `u(x)=${a}x+\\frac{${b}}x+\\frac{${c}}{1-${c}(x-1)}`,
    text('The denominator is nonzero on the stated interval; uniqueness selects this initial-value solution.'),
    `x_0=1+\\frac1{${2*c}},\\quad z(x_0)=${2*c}`,
    `u(x_0)=${a}\\left(1+\\frac1{${2*c}}\\right)+\\frac{${b}}{1+1/${2*c}}+${2*c}=${A}`
  ];
  if (record.familyId==='clairaut-envelope') return [
    `v(x):=u(x)+${b}x,\\quad p(x):=v^{\\prime}(x)=u^{\\prime}(x)+${b}>0`,
    `v=(x+${c})p+\\frac{${a}}p`,
    `p^{\\prime}\\left(x+${c}-\\frac{${a}}{p^2}\\right)=0`,
    text('The specified singular branch uses the second factor, rather than a constant derivative.'),
    `p=\\sqrt{\\frac{${a}}{x+${c}}},\\quad v=2\\sqrt{${a}(x+${c})}`,
    `u(x)=2\\sqrt{${a}(x+${c})}-${b}x\\quad(x>-${c})`,
    `u(${a-c})=${2*a}-${b}(${a-c})=${A}`
  ];
  if (record.familyId==='euler-double-resonance') return [
    `t=\\ln x,\\quad u(x)=x^{${a}}v(t)\\quad(x>0)`,
    `x^2u^{\\prime\\prime}+(1-${2*a})xu^{\\prime}+${a*a}u=x^{${a}}v^{\\prime\\prime}(t)`,
    `v^{\\prime\\prime}(t)=t^{${b}},\\quad v(0)=${c},\\quad v^{\\prime}(0)=0`,
    `v^{\\prime}(t)=\\frac{t^{${b+1}}}{${b+1}},\\quad v(t)=${c}+\\frac{t^{${b+2}}}{${(b+1)*(b+2)}}`,
    `u(x)=x^{${a}}\\left(${c}+\\frac{(\\ln x)^{${b+2}}}{${(b+1)*(b+2)}}\\right)`,
    text('The normalized linear equation has continuous coefficients on the positive axis, so the initial conditions determine this solution uniquely.'),
    `u(2)=${A}`
  ];
  throw new Error('Unsupported special ODE');
}
export function corrected_solution(record) {
  if(!supports(record)) throw new Error('Unsupported legacy family or version');
  const d=RECIPES[record.familyId],co=coefficients(record),A=finalAnswer(record);
  if(d.kind==='special-ode')return specialSolution(record);
  const steps=[...d.prefix,...d.extra].map(natural);
  if(d.kind==='ode') {
    steps.push(`u(x):=${co[0]}v_1(x)+${co[1]}v_2(x)+${co[2]}v_3(x)`);
    steps.push(text('Linearity of the displayed operator gives exactly the forcing term in the question.'));
    d.initialValues.forEach((vals,j)=>{
      const evaluated=vals.every(v=>/^-?\d+$/.test(v))?String(vals.reduce((sum,v,i)=>sum+Number(v)*co[i],0)):combination(co,vals);
      const label=j===0?'u':j===1?'u^{\\prime}':`u^{(${j})}`;
      steps.push(`${label}(${d.initial})=${combination(co,vals)}=${evaluated}`);
    });
    steps.push(text('The leading coefficient is nonzero and the normalized coefficients are continuous on the interval containing these data and the target point; the linear initial-value solution is unique.'));
    steps.push(`u(${natural(d.point)})=${combination(co,d.values)}=${A}`);
    return steps;
  }
  steps.push(text('The component values are:'));
  steps.push(...d.componentOperations.map(natural));
  steps.push(text('Linearity combines the three contributions with the coefficients in the question.'));
  steps.push(`${combination(co,d.values)}=${A}`);
  return steps;
}
export const familyIds=Object.keys(RECIPES);
export const recipeVersion='legacy-worked-solutions-2026-11-03-v1';
export const correctedLegacySolution=corrected_solution;
