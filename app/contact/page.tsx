'use client';

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { CheckCircle2, Clock3, Loader2, Mail, Send } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';
import { CONTACT_COOLDOWN_SECONDS, CONTACT_DAILY_LIMIT, CONTACT_TOPICS, type ContactTopic } from '@/lib/contact';
type ContactResponse = { error?: string; retryAfter?: number; ok?: boolean };

function waitLabel(seconds: number) {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.ceil(seconds / 60);
  return minutes < 60 ? `${minutes} min` : `${Math.ceil(minutes / 60)} hr`;
}

export default function ContactPage() {
  const { user, loading } = useAuth();
  const [topic, setTopic] = useState<ContactTopic>('bug');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  const [statusAttempt, setStatusAttempt] = useState(0);
  const [remaining, setRemaining] = useState(0);
  const readyAt = useRef(0);
  const sending = useRef(false);
  const requestId = useRef('');
  const setCooldown = (seconds: unknown) => {
    const value = Number(seconds);
    if (!Number.isFinite(value) || value < 0) return;
    readyAt.current = Date.now() + Math.min(value, 86400) * 1000;
    setRemaining(Math.ceil(value));
  };

  useEffect(() => {
    const timer = setInterval(() => setRemaining(Math.max(0, Math.ceil((readyAt.current - Date.now()) / 1000))), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    setReady(false); setError(''); setSent(false); setCooldown(0);
    if (!user) return;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    void (async () => {
      try {
        const result = await fetch('/api/contact', { headers: { Authorization: `Bearer ${await user.getIdToken()}` }, signal: controller.signal });
        const data = await result.json() as ContactResponse;
        if (!result.ok) throw new Error(data.error || 'Contact is temporarily unavailable. Please retry.');
        if (!controller.signal.aborted) { setCooldown(data.retryAfter); setReady(true); }
      } catch (reason) {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'Contact is temporarily unavailable. Please retry.');
        else if (controller.signal.reason?.name === 'AbortError') setError('The connection timed out. Please retry.');
      } finally { clearTimeout(timeout); }
    })();
    return () => { clearTimeout(timeout); controller.abort('unmounted'); };
  }, [user, statusAttempt]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user || !ready || sending.current || remaining > 0) return;
    sending.current = true; setBusy(true); setError(''); setSent(false);
    if (!requestId.current) requestId.current = crypto.randomUUID();
    try {
      const result = await fetch('/api/contact', {
        method: 'POST', headers: { Authorization: `Bearer ${await user.getIdToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, message, requestId: requestId.current }), signal: AbortSignal.timeout(20000),
      });
      const data = await result.json() as ContactResponse;
      if (data.retryAfter !== undefined) setCooldown(data.retryAfter);
      if (!result.ok || data.ok !== true) throw new Error(data.error || 'Your message could not be sent. Please retry.');
      setMessage(''); requestId.current = ''; setSent(true);
    } catch (reason) {
      setError(reason instanceof Error && reason.name !== 'TimeoutError' ? reason.message : 'Delivery could not be confirmed. Your message is still here; please retry.');
    } finally { sending.current = false; setBusy(false); }
  }

  return <main className="min-h-screen bg-zinc-950 px-4 py-10 text-zinc-50 selection:bg-emerald-500/30 sm:px-6 sm:py-14">
    <div className="mx-auto max-w-2xl">
      <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-emerald-400"><Mail className="h-6 w-6" aria-hidden="true" /></div>
      <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Contact Us</h1>
      <p className="mt-3 text-base leading-relaxed text-zinc-400 sm:text-lg">Help make Calculus Ninja better. Send Zach a bug report, balance feedback, or a question.</p>
      <div className="mt-6 flex items-start gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-3 text-sm leading-relaxed text-zinc-400">
        <Clock3 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" aria-hidden="true" />
        <p>To prevent spam, please wait {CONTACT_COOLDOWN_SECONDS} seconds between submissions. Each account can send up to {CONTACT_DAILY_LIMIT} messages per day.</p>
      </div>
      {loading ? <p role="status" className="mt-8 text-sm text-zinc-400">Loading your account…</p> : !user ? <div className="mt-6 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6">
        <h2 className="text-lg font-semibold">Sign in to send a message</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-400">Signing in helps keep reports useful and lets Zach reply to your account email.</p>
        <a href="/auth?next=/contact" className="mt-5 inline-flex min-h-11 items-center justify-center rounded-xl bg-emerald-400 px-5 py-3 text-sm font-semibold text-zinc-950 hover:bg-emerald-300">Sign in to contact us</a>
      </div> : <form onSubmit={submit} className="mt-6 space-y-5 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 sm:p-7">
        <div><label htmlFor="contact-topic" className="mb-2 block text-sm font-medium text-zinc-200">What’s on your mind?</label>
          <select id="contact-topic" value={topic} disabled={busy} onChange={event => { setTopic(event.target.value as ContactTopic); requestId.current = ''; }} className="min-h-12 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 text-base text-zinc-100">
            {Object.entries(CONTACT_TOPICS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <div><label htmlFor="contact-message" className="mb-2 block text-sm font-medium text-zinc-200">Your message</label>
          <textarea id="contact-message" value={message} onChange={event => { setMessage(event.target.value); requestId.current = ''; }} disabled={busy} required minLength={10} maxLength={4000} rows={7} aria-describedby="contact-hint" className="min-h-44 w-full resize-y rounded-xl border border-zinc-700 bg-zinc-950 p-3 text-base leading-relaxed text-zinc-100 placeholder:text-zinc-500" placeholder={topic === 'bug' ? 'What happened, and what did you expect? Include the game mode, device, browser, and game ID if available.' : topic === 'balance' ? 'What feels unbalanced? Share an example and what you would change.' : 'What would you like to ask or suggest?'} />
          <div id="contact-hint" className="mt-2 flex justify-between gap-4 text-xs text-zinc-400"><span>10–4,000 characters</span><span>{message.length.toLocaleString()} / 4,000</span></div>
        </div>
        <p className="break-words text-sm leading-relaxed text-zinc-400">Your message and account email ({user.email}) will be sent to Zach so he can reply.</p>
        {error && <div role="alert" className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm leading-relaxed text-red-300">{error}{!ready && <button type="button" onClick={() => setStatusAttempt(value => value + 1)} className="ml-2 min-h-11 rounded-lg px-3 font-semibold underline">Retry</button>}</div>}
        {sent && <div role="status" className="flex items-start gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-300"><CheckCircle2 className="h-5 w-5 shrink-0" aria-hidden="true" />Message sent. Thanks for helping improve Calculus Ninja!</div>}
        {remaining > 0 && <p className="text-sm text-zinc-300">You can send another message in <span role="timer" aria-live="off" className="font-semibold text-emerald-400">{waitLabel(remaining)}</span>.</p>}
        <button type="submit" disabled={!ready || busy || remaining > 0 || message.trim().length < 10} className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 py-3 text-sm font-semibold text-zinc-950 transition-colors hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Send className="h-4 w-4" aria-hidden="true" />}{busy ? 'Sending…' : remaining > 0 ? 'Please wait' : !ready && !error ? 'Checking availability…' : 'Send message'}
        </button>
      </form>}
    </div>
  </main>;
}
