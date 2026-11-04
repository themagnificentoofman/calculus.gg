// Product notation, not an algebraic simplifier. Explicit logarithm bases and
// prose are preserved; source records retain their original immutable hashes.
export const NOTATION_VERSION = 'calculus-ninja-notation-v1';
const functions = {atan:'arctan',asin:'arcsin',acos:'arccos',asinh:'arcsinh',acosh:'arccosh',atanh:'arctanh',arsinh:'arcsinh',arcosh:'arccosh',artanh:'arctanh'};
const functionNotation = name => ['atan','asin','acos'].includes(name)?'\\'+functions[name]:'\\operatorname{'+functions[name]+'}';
const textCommands = new Set(['text','textnormal','textbf','textit','textrm','textsf','texttt']);
export function braced(source, start) {
  if (source[start] !== '{') return null;
  let depth=1;
  for(let i=start+1;i<source.length;i++) {
    if(source[i]==='\\' && /[{}\\]/.test(source[i+1]||'')){i++;continue;}
    if(source[i]==='{')depth++;
    if(source[i]==='}' && --depth===0)return {body:source.slice(start+1,i),end:i+1};
  }
  return null;
}
const hasBase = tail => /^(?:\s|\\[,;! ]|\\limits)*_/.test(tail);
export function normalizeNotation(input,{differentialVariables=[]}={}) {
  const source=String(input);let result='',pieces=[];
  for(let i=0;i<source.length;) {
    if(source[i]!=='\\'){result+=source[i++];continue;}
    const command=/^\\([A-Za-z]+)/.exec(source.slice(i));
    if(!command){result+=source[i++];continue;}
    const name=command[1],end=i+command[0].length;
    const group=braced(source,end);
    if(textCommands.has(name)&&group){pieces.push({math:result},{text:source.slice(i,group.end)});result='';i=group.end;continue;}
    if(name==='log'&&!hasBase(source.slice(end))){result+='\\ln';i=end;continue;}
    if(name==='operatorname'&&group) {
      if(group.body==='log'&&!hasBase(source.slice(group.end))){result+='\\ln';i=group.end;continue;}
      if(functions[group.body]){result+=functionNotation(group.body);i=group.end;continue;}
    }
    if(functions[name]){result+=functionNotation(name);i=end;continue;}
    result+=command[0];i=end;
  }
  // These exact forms denote differential operators/measures, not variables d.
  pieces.push({math:result});
  return pieces.map(p=>{if(p.text!==undefined)return p.text;
    let math=p.math;
    // Only reviewed legacy recipes opt in: d is not an algebraic variable in
    // those source-bound constructors. The generic renderer never guesses.
    math=math.replace(/\\([,; ])d(?=[A-Za-z]|\\(?:theta|phi|rho|tau)\b)/g,'\\$1\\mathrm{d}')
    .replace(/\\(d?frac|tfrac)\{d((?:\^\{[^{}]+\}|\^[A-Za-z0-9])?)\}\{d([A-Za-z])((?:\^\{[^{}]+\}|\^[A-Za-z0-9])?)\}/g,'\\$1{\\mathrm{d}$2}{\\mathrm{d}$3$4}')
    .replace(/\\(d?frac|tfrac)\{d([A-Za-z])\}\{d([A-Za-z])\}/g,'\\$1{\\mathrm{d}$2}{\\mathrm{d}$3}');
    if(differentialVariables.length)math=math.replace(new RegExp('d(['+differentialVariables.join('')+'])(?![A-Za-z])','g'),'\\mathrm{d}$1');
    return math;}).join('');
}
