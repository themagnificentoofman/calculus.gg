export interface ProblemReference {
  problemId: string;
  problemRevision: number;
  contentHash: string;
  bankRelease: string;
  familyId: string;
  /** Stable IDs in the actual displayed order; never identifies the answer. */
  choiceOrder: string[];
}
export interface RoundSnapshot {
  schemaVersion: 1;
  selectionPolicy: 'family-uniform-v1';
  relaxation: 'none' | 'recent-families' | 'recent-problems' | 'family-cap';
  questions: (ProblemReference & { ordinal: number })[];
}
export interface BankProblem {
  schemaVersion: 1;
  problemId: string;
  problemRevision: number;
  contentHash: string;
  semanticHash: string;
  statement: string;
  choices: { choiceId: string; math: string }[];
  answerChoiceId: string;
  solutionSteps: string[];
  assumptions: string[];
  topic: string;
  difficulty: string;
  subtopic: string;
  techniqueTags: string[];
  familyId: string;
  templateVersion: string;
  parameters: Record<string, number>;
  provenance: { kind: string; sourceUrl: string | null; sourceItem: string | null; license: string; attribution: string; authoring: Record<string, unknown> };
  validation: { status: 'passed'; methods: string[]; evidence: Record<string, unknown>; humanReviewed: boolean };
  estimates: { difficulty: string; solveSeconds: number; basis: string };
}
