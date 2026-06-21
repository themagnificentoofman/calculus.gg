'use client';

import React from 'react';
import { InlineMath, BlockMath } from 'react-katex';

interface LatexTextProps {
  text: string;
}

export function LatexText({ text }: LatexTextProps) {
  // Simple parser to split text by $$ and $
  // This is a basic implementation. For production, a more robust parser is recommended.
  const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g);

  return (
    <span>
      {parts.map((part, index) => {
        if (part.startsWith('$$') && part.endsWith('$$')) {
          return <BlockMath key={index} math={part.slice(2, -2)} />;
        } else if (part.startsWith('$') && part.endsWith('$')) {
          return <InlineMath key={index} math={part.slice(1, -1)} />;
        } else {
          return <span key={index}>{part}</span>;
        }
      })}
    </span>
  );
}
