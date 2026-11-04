import { normalizeMath } from './render-math.mjs';
import { normalizeNotation, braced } from './math-notation.mjs';

const proseCommand=/^\\(?:textnormal|text|textrm)\{/;
function prose(value) {
  return value.replace(/\\textasciicircum\{\}/g,'^').replace(/\\textbackslash\{\}/g,'\\')
    .replace(/\\([_%&#{}$])/g,'$1').replace(/~/g,' ');
}
function rows(source) {
  const begin='\\begin{gathered}',end='\\end{gathered}';
  if(!source.startsWith(begin)||!source.endsWith(end))return [source];
  // Several adjacent gathered environments are not one outer wrapper.
  let outer=0;
  for(const token of source.matchAll(/\\(begin|end)\{gathered\}/g)){
    outer+=token[1]==='begin'?1:-1;
    if(outer===0){if(token.index+token[0].length!==source.length)return [source];break;}
  }
  source=source.slice(begin.length,-end.length);let depth=0,env=0,start=0,parts=[];
  for(let i=0;i<source.length;i++) {
    if(source[i]==='\\') {
      const token=/^\\(begin|end)\{[^{}]+\}/.exec(source.slice(i));
      if(token){env+=token[1]==='begin'?1:-1;i+=token[0].length-1;continue;}
      if(source[i+1]==='\\'&&depth===0&&env===0){parts.push(source.slice(start,i));i++;start=i+1;continue;}
      if(/[{}\\]/.test(source[i+1]||'')){i++;continue;}
    }
    if(source[i]==='{')depth++;else if(source[i]==='}')depth--;
  }
  return [...parts,source.slice(start)];
}
function rowBlock(source) {
  let depth=0,environment=0,delimiters=0,start=0,parts=[];
  const addMath=value=>{if(!value.trim()||/^(?:\s|\\(?:quad|qquad)|\\[,;! ])+$/.test(value))return;parts.push(/^[\s.,:;!?]+$/.test(value)?{kind:'text',value}:{kind:'math',value:value.replace(/\\ /g,'\\;').trim()});};
  for(let i=0;i<source.length;i++) {
    if(source[i]==='\\') {
      const delimiter=/^\\(left|right)\b/.exec(source.slice(i));
      if(delimiter){delimiters+=delimiter[1]==='left'?1:-1;i+=delimiter[0].length-1;continue;}
      const env=/^\\(begin|end)\{[^{}]+\}/.exec(source.slice(i));
      if(env){environment+=env[1]==='begin'?1:-1;i+=env[0].length-1;continue;}
      const command=depth===0&&environment===0&&delimiters===0&&proseCommand.exec(source.slice(i));
      if(command){const group=braced(source,i+command[0].length-1);if(group){addMath(source.slice(start,i));parts.push({kind:'text',value:prose(group.body)});i=group.end-1;start=group.end;continue;}}
      if(/[{}\\]/.test(source[i+1]||'')){i++;continue;}
    }
    if(source[i]==='{')depth++;else if(source[i]==='}')depth--;
  }
  addMath(source.slice(start));
  return parts.some(p=>p.kind==='text')?{kind:'paragraph',parts}:{kind:'math',value:source};
}
// Parse only top-level prose. Never split a fraction, cases definition, paired
// delimiter, or nested TeX group merely because it contains a text command.
export function formatSolutionStep(step) {
  const source=normalizeNotation(normalizeMath(step));let blocks=[];
  for(const row of rows(source)) {
    const block=rowBlock(row.trim()),last=blocks.at(-1);
    if(block.kind==='paragraph'&&block.parts.every(p=>p.kind==='text')&&last?.kind==='paragraph'&&last.parts.every(p=>p.kind==='text'))last.parts.push({kind:'text',value:' '},...block.parts);
    else blocks.push(block);
  }
  return blocks;
}

// Older prompts wrapped individual sentences in nested gathered environments.
// Unwrap only environments made entirely of prose. Mathematical alignments,
// fractions, cases and paired delimiters remain complete TeX expressions.
function collapseProseGathered(source) {
  const begin='\\begin{gathered}',end='\\end{gathered}';
  const stack=[];let result='',cursor=0;
  for(const token of source.matchAll(/\\(begin|end)\{gathered\}/g)) {
    if(token[1]==='begin'){stack.push(token.index);continue;}
    const start=stack.pop();if(start===undefined||stack.length)continue;
    const body=collapseProseGathered(source.slice(start+begin.length,token.index));
    const lines=rows(begin+body+end),blocks=lines.map(row=>rowBlock(row.trim()));
    const onlyProse=blocks.every(block=>block.kind==='paragraph'&&block.parts.every(part=>part.kind==='text'));
    result+=source.slice(cursor,start)+(onlyProse?lines.join(' '):begin+body+end);
    cursor=token.index+end.length;
  }
  return result+source.slice(cursor);
}
export function formatProblemStatement(statement) {
  const result=[];
  for(const block of formatSolutionStep(collapseProseGathered(normalizeMath(statement)))) {
    if(block.kind==='math'){result.push(block);continue;}
    let parts=[];
    const flush=()=>{if(parts.length)result.push({kind:'paragraph',parts});parts=[];};
    for(const part of block.parts) {
      // A long defining equation belongs in display math, even when a legacy
      // prompt concatenated it directly with the following prose sentence.
      if(part.kind==='math'&&(part.value.length>100||(/\\(?:int|sum|prod|begin)(?![A-Za-z])/.test(part.value)&&part.value.length>65))){flush();result.push({kind:'math',value:part.value});}
      else parts.push(part);
    }
    flush();
  }
  return result;
}
