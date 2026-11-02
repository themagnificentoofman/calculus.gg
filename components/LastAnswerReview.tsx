import { MathDisplay } from './MathDisplay';

export interface AnsweredQuestion {
  question: {
    latexProblem: string;
    options: string[];
    correctIndex: number;
    explanation: string | string[];
  };
  selectedOption: number;
}

export function LastAnswerReview({ answer }: { answer: AnsweredQuestion | null }) {
  if (!answer) return null;

  const { question, selectedOption } = answer;
  const correct = selectedOption === question.correctIndex;
  const steps = Array.isArray(question.explanation) ? question.explanation : [question.explanation];

  return (
    <details className="min-w-0 mb-8 rounded-xl border border-zinc-800 bg-zinc-950 p-4 text-left">
      <summary className="cursor-pointer font-bold text-white">Review last answer</summary>
      <div className="min-w-0 mt-4 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-zinc-400">Question</h3>
          <MathDisplay math={question.latexProblem} block />
        </div>
        <div>
          <h3 className={correct ? 'text-emerald-400' : 'text-red-400'}>
            Your answer · {correct ? 'Correct' : 'Incorrect'}
          </h3>
          <MathDisplay math={question.options[selectedOption]} block />
        </div>
        {!correct && (
          <div>
            <h3 className="text-sm font-semibold text-emerald-400">Correct answer</h3>
            <MathDisplay math={question.options[question.correctIndex]} block />
          </div>
        )}
        <div className="min-w-0 space-y-4 text-zinc-400">
          <h3 className="text-sm font-semibold">Explanation</h3>
          {steps.map((step, index) => <MathDisplay key={index} math={step} block />)}
        </div>
      </div>
    </details>
  );
}
