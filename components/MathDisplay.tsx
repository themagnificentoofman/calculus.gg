'use client';

import { useMemo } from 'react';
import { normalizeMath, renderMath } from '@/lib/render-math.mjs';

interface MathDisplayProps {
  math: string;
  block?: boolean;
}

export function MathDisplay({ math, block = false }: MathDisplayProps) {
  const source = normalizeMath(math);
  const html = useMemo(() => {
    try {
      // Render the complete expression. Splitting around \\text{...} can sever
      // fractions, nested groups, environments, or paired \\left / \\right.
      return renderMath(source, block);
    } catch {
      return null;
    }
  }, [source, block]);

  // Old saved games can contain unsupported LaTeX. Keep their content visible
  // as escaped React text, and recover automatically when the formula changes.
  if (html === null) {
    return <span className="math-source whitespace-pre-wrap break-words font-mono text-sm" role="note" aria-label="Formula shown as source">{source}</span>;
  }
  return <span className={`math-display max-w-full min-w-0 overflow-x-auto overflow-y-hidden ${block ? 'block' : 'inline-block align-middle'}`} dangerouslySetInnerHTML={{ __html: html }} />;
}
