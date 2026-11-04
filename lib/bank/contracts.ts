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
  schemaVersion: 1 | 2;
  selectionPolicy: 'family-uniform-v1' | 'exposure-weighted-v2';
  relaxation: 'none' | 'recent-families' | 'recent-problems' | 'family-cap';
  diagnostics?: SelectionDiagnostics;
  questions: (ProblemReference & { ordinal: number })[];
}
export interface BankProblem {
  schemaVersion: 1 | 2;
  pedagogy?: ProblemPedagogy;
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

/** Private mathematical metadata. Never included in a pre-answer projection. */
export interface ProblemPedagogy {
  constructionId: string;
  relatedIdeaGroupId: string;
  structuralSignature: string;
  primaryTechnique: string;
  alternativeTechniques: string[];
  prerequisites: string[];
  reasoningDemand: ('execution' | 'recognition' | 'method-selection' | 'reframing' | 'convergence' | 'synthesis')[];
  answerForm: string;
  difficultyRationale: string;
  sourceRecordIds: string[];
  responseFormat: 'multiple-choice';
}

export interface SelectionDiagnostics {
  policy: 'exposure-weighted-v2';
  candidateCount: number;
  probes: number;
  statements: number;
  catalogFamilies: number;
  exhaustedInventory: boolean;
  reasons: ('family-cap-impossible' | 'recent-items-exhausted' | 'candidate-sampling-limit' | 'adjacency-unavoidable')[];
}
