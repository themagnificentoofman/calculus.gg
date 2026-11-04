import { MathDisplay } from './MathDisplay';
import { formatSolutionStep } from '@/lib/solution-format.mjs';

export function SolutionSteps({ steps }: { steps: string | string[] }) {
  const lines=Array.isArray(steps)?steps:[steps];
  return <div className="solution-steps min-w-0 space-y-4">
    {lines.flatMap((line,index)=>formatSolutionStep(line).map((block:any,row:number)=>block.kind==='paragraph'
      ? <p key={`${index}-${row}`} className="text-left text-base leading-7 text-zinc-300 [overflow-wrap:anywhere]">{block.parts.map((part:any,i:number)=>part.kind==='text'?<span key={i}>{part.value}</span>:<MathDisplay key={i} math={part.value}/>)}</p>
      : <MathDisplay key={`${index}-${row}`} math={block.value} block/>))}
  </div>;
}
