import { MathDisplay } from './MathDisplay';
import { formatProblemStatement } from '@/lib/solution-format.mjs';

export function ProblemStatement({ math, legacy = false }: { math: string; legacy?: boolean }) {
  return <div className="problem-statement min-w-0 space-y-4">
    {legacy && <span className="inline-flex rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs font-medium text-amber-700 dark:text-amber-300" title="A problem from an original bank construction.">Legacy</span>}
    {formatProblemStatement(math).map((block: any, row: number) => block.kind === 'paragraph'
      ? <p key={row} className="text-left text-base leading-7 text-zinc-200 [overflow-wrap:anywhere]">{block.parts.map((part: any, i: number) => part.kind === 'text' ? <span key={i}>{part.value}</span> : <MathDisplay key={i} math={part.value} />)}</p>
      : <MathDisplay key={row} math={block.value} block />)}
  </div>;
}
