'use client';
import { useState } from 'react';
import { apiRequest } from '@/lib/game-session';
export function ProblemReference({ problemId, problemRevision }: { problemId?: string; problemRevision?: number }) {
  const [copied, setCopied] = useState(false), [reporting, setReporting] = useState(false), [reason, setReason] = useState(''), [status, setStatus] = useState(''), [busy, setBusy] = useState(false);
  if (!problemId || !problemRevision) return null;
  const reference = `${problemId}@${problemRevision}`;
  return <div className="space-y-2 text-xs text-zinc-400">
    <div className="flex flex-wrap items-center gap-3">
      <button type="button" className="min-h-11 break-all font-mono underline" onClick={() => { void navigator.clipboard.writeText(reference).then(() => setCopied(true)).catch(() => setStatus('Select and copy the ID manually.')); }}>{copied ? 'Copied: ' : 'Copy problem ID: '}{reference}</button>
      <button type="button" className="min-h-11 underline" onClick={() => setReporting(v => !v)}>Report a problem</button>
    </div>
    {reporting && <form className="space-y-2" onSubmit={event => { event.preventDefault(); setBusy(true); setStatus(''); void apiRequest('problems/report', { problemId, problemRevision, reason }).then(() => { setStatus('Report saved. Thank you.'); setReporting(false); }).catch(error => setStatus(error.message)).finally(() => setBusy(false)); }}>
      <label className="block">What seems wrong?<textarea value={reason} onChange={e => setReason(e.target.value)} required minLength={5} maxLength={2000} className="mt-2 block min-h-24 w-full rounded-lg border border-zinc-700 bg-zinc-900 p-3 text-sm text-white" /></label>
      <button disabled={busy} className="min-h-11 rounded-lg border border-zinc-700 px-4">{busy ? 'Saving…' : 'Send report'}</button>
    </form>}
    {status && <p role="status">{status}</p>}
  </div>;
}
