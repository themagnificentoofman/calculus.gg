'use client';
import type {FormEvent} from 'react';
import {FlaskConical} from 'lucide-react';

export function ExperimentalSettings({enabled,onChange,onSave,saving,dirty}:{enabled:boolean;onChange:(enabled:boolean)=>void;onSave:(event:FormEvent)=>void;saving:boolean;dirty:boolean}) {
  return (
            <section aria-labelledby="experimental-heading" className="dark:bg-zinc-900/40 bg-white border dark:border-zinc-800/50 border-zinc-200 rounded-3xl p-5 sm:p-6 shadow-sm">
              <h2 id="experimental-heading" className="text-xl font-bold mb-5 flex items-center gap-2"><FlaskConical className="w-5 h-5 text-amber-500" />Experimental</h2>
              <label className="flex min-h-11 items-center justify-between gap-3 cursor-pointer">
                <span className="font-bold text-sm">Include legacy problems</span>
                <span className="relative shrink-0">
                  <input type="checkbox" role="switch" aria-describedby="legacy-description" className="peer sr-only" checked={enabled} onChange={event => onChange(event.target.checked)} />
                  <span className={`block w-10 h-6 rounded-full transition-colors peer-focus-visible:outline-2 peer-focus-visible:outline-offset-4 peer-focus-visible:outline-emerald-400 ${enabled ? 'bg-emerald-500' : 'dark:bg-zinc-700 bg-zinc-300'}`} />
                  <span className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${enabled ? 'translate-x-4' : ''}`} />
                </span>
              </label>
              <p id="legacy-description" className="mt-3 text-sm leading-6 dark:text-zinc-400 text-zinc-600">Adds reviewed problems from the original bank to new Test and Rapid rounds, when available. They carry a Legacy label and must meet the same quality standards. Off by default. PvP and Multiplayer use a shared pool without legacy problems.</p>
              <p className="mt-3 text-xs dark:text-zinc-400 text-zinc-600">Current rounds and saved history stay as they are.</p>
              <button type="button" disabled={saving || !dirty} onClick={onSave} className="mt-4 min-h-11 rounded-xl bg-emerald-500 px-4 py-2 font-bold text-white hover:bg-emerald-600 disabled:opacity-50">{saving ? 'Saving…' : 'Save Changes'}</button>
            </section>
  );
}
