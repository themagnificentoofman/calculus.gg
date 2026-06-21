'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { InlineMath, BlockMath } from 'react-katex';

interface MathDisplayProps {
  math: string;
  block?: boolean;
}

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("KaTeX Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <span className="text-red-500 font-mono text-sm">[Math Render Error]</span>;
    }
    return this.props.children;
  }
}

function parseMathText(input: string) {
  // Match \text{...} or \textnormal{...} or \textbf{...}
  // We use a simple regex that assumes no nested braces inside the text block.
  const regex = /\\text(?:normal|bf)?\{([^}]*)\}/g;
  const parts: { type: 'math' | 'text'; content: string }[] = [];
  let lastIndex = 0;
  let match;
  
  while ((match = regex.exec(input)) !== null) {
    if (match.index > lastIndex) {
      const mathPart = input.substring(lastIndex, match.index);
      if (mathPart.trim()) {
        parts.push({ type: 'math', content: mathPart });
      }
    }
    if (match[1]) {
      parts.push({ type: 'text', content: match[1] });
    }
    lastIndex = regex.lastIndex;
  }
  
  if (lastIndex < input.length) {
    const mathPart = input.substring(lastIndex);
    if (mathPart.trim()) {
      parts.push({ type: 'math', content: mathPart });
    }
  }
  
  // If no text blocks were found, just return the whole thing as math
  if (parts.length === 0) {
    return [{ type: 'math', content: input }];
  }
  
  return parts;
}

export function MathDisplay({ math, block = false }: MathDisplayProps) {
  const cleanMath = math ? math.trim() : '';
  
  // Parse the math string to separate text and math blocks
  const parts = parseMathText(cleanMath);

  // If it's just one math block, render it normally
  if (parts.length === 1 && parts[0].type === 'math') {
    return (
      <ErrorBoundary>
        {block ? <BlockMath math={parts[0].content} /> : <InlineMath math={parts[0].content} />}
      </ErrorBoundary>
    );
  }

  // Otherwise, render a mix of HTML text and inline math to allow natural wrapping
  return (
    <ErrorBoundary>
      <div className={`${block ? 'flex justify-center w-full my-4' : 'inline-flex'} flex-wrap items-baseline leading-relaxed`}>
        {parts.map((part, i) => (
          part.type === 'text' ? (
            <span key={i} className="whitespace-pre-wrap">{part.content}</span>
          ) : (
            <span key={i} className="inline-block">
              <InlineMath math={part.content} />
            </span>
          )
        ))}
      </div>
    </ErrorBoundary>
  );
}
