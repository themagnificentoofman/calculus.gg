import { auth } from '@/firebase';

export interface GeneratedQuestion {
  latexProblem: string;
  options: string[];
  correctIndex: number;
  explanation: string[];
  topic: string;
  difficulty: string;
}

export async function generateQuestions(category: string, difficulty: string, count: number): Promise<GeneratedQuestion[]> {
  const user = auth.currentUser;
  if (!user) throw new Error('Please sign in before starting a game.');
  const token = await user.getIdToken();
  const response = await fetch('/api/questions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ category, difficulty, count }),
    signal: AbortSignal.timeout(85000),
  });
  const payload = await response.json().catch(() => null) as { error?: string; questions?: GeneratedQuestion[] } | null;
  if (!response.ok) {
    throw new Error(payload?.error || 'Question generation is unavailable. Please try again.');
  }
  if (!payload || !Array.isArray(payload.questions)) throw new Error('The server returned an invalid question set. Please try again.');
  return payload.questions;
}
