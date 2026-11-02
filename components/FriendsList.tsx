'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { db } from '@/firebase';
import { apiRequest } from '@/lib/game-session';
import { searchPublicProfiles } from '@/lib/stat-queries';
import { usePanel } from '@/lib/use-panel';
import { collection, query, where, orderBy, limit, doc, onSnapshot, getDoc } from 'firebase/firestore';
import { Users, Search, X, Check, Swords, UserMinus } from 'lucide-react';

type Person = { uid: string; displayName: string; photoURL?: string; lastActive?: number };
type RequestRow = { id: string; from: string; to: string; gameId?: string; mode?: string; person?: Person };
const avatar = (p?: Person) => p?.photoURL || '/ninja-logo.png';
const actionClass = 'min-h-11 min-w-11 shrink-0 rounded-lg px-3 text-xs font-semibold text-indigo-300 hover:bg-indigo-500/20 disabled:opacity-40';
const rowClass = 'flex flex-wrap items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-950/60 p-3';
function PersonLabel({ person, detail }: { person?: Person; detail?: string }) {
  return <div className="flex min-w-0 flex-1 basis-36 items-center gap-3"><img src={avatar(person)} alt="" className="h-10 w-10 shrink-0 rounded-full bg-zinc-800 object-cover" /><div className="min-w-0"><span className="block break-words text-sm font-medium">{person?.displayName || 'Player'}</span>{detail && <span className="text-xs text-zinc-400">{detail}</span>}</div></div>;
}
export function FriendsList() {
  const { user, profile } = useAuth();
  const [isOpen, setIsOpen] = usePanel('friends');
  const [friends, setFriends] = useState<Person[]>([]);
  const [incoming, setIncoming] = useState<RequestRow[]>([]);
  const [sent, setSent] = useState<RequestRow[]>([]);
  const [invites, setInvites] = useState<RequestRow[]>([]);
  const [toast, setToast] = useState<RequestRow | null>(null);
  const [search, setSearch] = useState('');
  const [results, setResults] = useState<Person[]>([]);
  const [searched, setSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const [removeId, setRemoveId] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());
  const scope = useRef(user?.uid); scope.current = user?.uid;
  const busy = useRef(false), searchVersion = useRef(0);
  const notify = useRef(true); notify.current = profile?.settings?.notifications !== false;
  const open = useRef(isOpen); open.current = isOpen;
  const friendIds = (profile?.friends || []).join(',');

  useEffect(() => {
    setFriends([]); setIncoming([]); setSent([]); setInvites([]); setToast(null);
    setResults([]); setSearch(''); setSearched(false); setError(''); setStatus(''); setRemoveId(null); setPending(false); busy.current = false;
    searchVersion.current++;
    if (!user) return;
    let active = true;
    const revisions = { incoming: 0, sent: 0, invites: 0 };
    let initialInvites = true;
    const seen = new Set<string>();
    const failure = () => { if (active) setError('Friends could not be refreshed. Check your connection and reload to retry.'); };
    const listen = (kind: keyof typeof revisions, name: string, field: 'from' | 'to', setter: (rows: RequestRow[]) => void) => onSnapshot(query(collection(db, name), where(field, '==', user.uid), where('status', '==', 'pending'), orderBy('createdAt', 'desc'), limit(100)), async snapshot => {
      const revision = ++revisions[kind];
      const rows = await Promise.all(snapshot.docs.map(async record => {
        const data = record.data();
        const other = field === 'to' ? data.from : data.to;
        const person = await getDoc(doc(db, 'users_public', other)).catch(() => null);
        return { ...data, id: record.id, person: person?.exists() ? { ...person.data(), uid: other } as Person : { uid: other, displayName: 'Player' } } as RequestRow;
      }));
      if (!active || revision !== revisions[kind]) return;
      setter(rows);
      if (kind === 'invites') {
        const newest = rows.find(row => !seen.has(row.id));
        if (!initialInvites && newest && notify.current && !open.current) setToast(newest);
        initialInvites = false; rows.forEach(row => seen.add(row.id));
        setToast(previous => previous && rows.some(row => row.id === previous.id) ? previous : null);
      }
    }, failure);
    const stops = [listen('incoming', 'friendRequests', 'to', setIncoming), listen('sent', 'friendRequests', 'from', setSent), listen('invites', 'gameInvites', 'to', setInvites)];
    return () => { active = false; stops.forEach(stop => stop()); };
  }, [user?.uid]);

  useEffect(() => {
    setFriends([]); if (!user) return;
    let active = true;
    const stops = (profile?.friends || []).map(uid => onSnapshot(doc(db, 'users_public', uid), snapshot => {
      if (!active) return;
      setFriends(previous => [...previous.filter(p => p.uid !== uid), ...(snapshot.exists() ? [{ ...snapshot.data(), uid } as Person] : [])].sort((a,b) => a.displayName.localeCompare(b.displayName)));
    }, () => { if (active) setError('A friend profile could not be loaded. Please reload to retry.'); }));
    return () => { active = false; stops.forEach(stop => stop()); };
  }, [user?.uid, friendIds]);
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 30000); return () => clearInterval(timer); }, []);
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(null), 8000); return () => clearTimeout(timer); }, [toast]);
  useEffect(() => { if (!notify.current) setToast(null); }, [profile?.settings?.notifications]);

  async function run(action: string, body: Record<string, unknown>, message: string, after?: (result: any) => void) {
    if (!user || busy.current) return;
    const uid = user.uid; busy.current = true; setPending(true); setError(''); setStatus('');
    try {
      const result = await apiRequest('social', { action, ...body });
      if (scope.current !== uid) return;
      setStatus(message); after?.(result);
    } catch (e) { if (scope.current === uid) { setError(e instanceof Error ? e.message : 'Could not complete this action. Please retry.'); setIsOpen(true); } }
    finally { if (scope.current === uid) { busy.current = false; setPending(false); } }
  }
  async function findPlayers() {
    if (!user || !search.trim()) return;
    const uid = user.uid, version = ++searchVersion.current;
    setSearching(true); setError(''); setStatus('');
    try {
      const rows = await searchPublicProfiles(db, uid, search);
      if (scope.current === uid && version === searchVersion.current) { setResults(rows.map(p => ({ ...p, displayName: p.displayName || 'Player' }) as Person)); setSearched(true); }
    } catch { if (scope.current === uid && version === searchVersion.current) setError('Search failed. Please retry.'); }
    finally { if (scope.current === uid && version === searchVersion.current) setSearching(false); }
  }
  const acceptInvite = (invite: RequestRow) => run('invite_accept', { id: invite.id }, 'Invitation accepted.', result => {
    setToast(null); window.location.assign(`/play/${result.mode === 'multiplayer' ? 'multiplayer' : 'pvp'}?join=${result.gameId}`);
  });
  const controls = (row: RequestRow, invitation = false) => <div className="ml-auto flex shrink-0"><button disabled={pending} aria-label={invitation ? 'Accept game invitation' : 'Accept friend request'} className={actionClass} onClick={() => invitation ? acceptInvite(row) : run('accept', { id: row.id }, 'Friend request accepted.')}><Check className="h-4 w-4" /></button><button disabled={pending} aria-label={invitation ? 'Decline game invitation' : 'Decline friend request'} className={actionClass} onClick={() => run(invitation ? 'invite_reject' : 'reject', { id: row.id }, invitation ? 'Invitation declined.' : 'Friend request declined.')}><X className="h-4 w-4" /></button></div>;
  const section = (title: string, children: React.ReactNode) => <section className="space-y-2"><h4 className="px-1 text-xs font-bold uppercase tracking-wide text-zinc-400">{title}</h4>{children}</section>;
  if (!user) return null;
  return <div className="fixed bottom-4 right-4 z-40 flex max-w-[calc(100vw-2rem)] flex-col items-end gap-3">
    {toast && !isOpen && <div role="status" className="flex w-80 max-w-full flex-wrap items-center gap-2 rounded-2xl border border-indigo-400/30 bg-indigo-950 p-3 text-white shadow-xl"><PersonLabel person={toast.person} detail="Invited you to play" />{controls(toast, true)}</div>}
    {isOpen ? <section role="region" aria-label="Friends panel" className="flex h-[32rem] max-h-[calc(100dvh-6rem)] w-80 max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border border-zinc-700 bg-zinc-900 text-zinc-100 shadow-2xl sm:w-96">
      <header className="flex shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-950 px-4 py-2"><h3 className="flex items-center gap-2 font-bold"><Users className="h-5 w-5 text-indigo-400" />Friends</h3><button aria-label="Close friends" onClick={() => setIsOpen(false)} className={actionClass}><X className="h-5 w-5" /></button></header>
      <form onSubmit={e => { e.preventDefault(); void findPlayers(); }} className="flex shrink-0 gap-1 border-b border-zinc-800 p-3"><input aria-label="Search users by name or handle" placeholder="Name or handle…" maxLength={99} value={search} onChange={e => { searchVersion.current++; setSearch(e.target.value); setSearched(false); setSearching(false); setResults([]); }} className="min-w-0 flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 text-base" />{search && <button type="button" aria-label="Clear search" className={actionClass} onClick={() => { searchVersion.current++; setSearch(''); setResults([]); setSearched(false); setSearching(false); }}><X className="h-4 w-4" /></button>}<button aria-label="Search users" disabled={searching || !search.trim()} className={actionClass}><Search className="h-4 w-4" /></button></form>
      {error && <p role="alert" className="shrink-0 border-b border-zinc-800 px-3 py-2 text-sm text-red-300">{error}</p>}
      {status && <p role="status" className="shrink-0 px-3 py-2 text-sm text-emerald-300">{status}</p>}
      <div className="min-h-0 min-w-0 flex-1 space-y-5 overflow-x-hidden overflow-y-auto overscroll-contain p-3">
        {search ? section('Search results', <>{searching ? <p role="status" className="p-3 text-sm text-zinc-400">Searching…</p> : !searched ? <p className="p-3 text-sm text-zinc-400">Search by a player's name or handle.</p> : !results.length ? <p className="p-3 text-sm text-zinc-400">No matching players.</p> : results.map(person => { const request = incoming.find(r => r.from === person.uid), outgoing = sent.find(r => r.to === person.uid); return <div key={person.uid} className={rowClass}><PersonLabel person={person} />{profile?.friends?.includes(person.uid) ? <span className="ml-auto text-xs text-zinc-400">Friend</span> : request ? controls(request) : outgoing ? <button disabled={pending} className={actionClass} onClick={() => run('cancel', { id: outgoing.id }, 'Request cancelled.')}>Cancel Request</button> : <button disabled={pending} className={actionClass} onClick={() => run('request', { to: person.uid }, 'Friend request sent.')}>Add</button>}</div>; })}</>) : <>
          {incoming.length > 0 && section('Pending requests', incoming.map(row => <div key={row.id} className={rowClass}><PersonLabel person={row.person} />{controls(row)}</div>))}
          {invites.length > 0 && section('Game invites', invites.map(row => <div key={row.id} className={rowClass}><PersonLabel person={row.person} detail={row.mode === 'multiplayer' ? 'Multiplayer invitation' : 'PvP invitation'} />{controls(row, true)}</div>))}
          {sent.length > 0 && section('Sent requests', sent.map(row => <div key={row.id} className={rowClass}><PersonLabel person={row.person} detail="Request pending" /><button disabled={pending} className={actionClass} onClick={() => run('cancel', { id: row.id }, 'Request cancelled.')}>Cancel Request</button></div>))}
          {section('Your friends', !friends.length ? <p className="p-4 text-sm text-zinc-400">No friends yet. Search for a player to add them.</p> : friends.map(person => <div key={person.uid} className={rowClass}><PersonLabel person={person} detail={person.lastActive && now - person.lastActive < 5 * 60000 ? 'Online' : 'Offline'} />{removeId === person.uid ? <div className="flex w-full flex-wrap items-center justify-end gap-1"><span className="mr-auto text-xs text-zinc-400">Remove this friend?</span><button disabled={pending} className={actionClass} onClick={() => run('remove', { friendId: person.uid }, 'Friend removed.', () => setRemoveId(null))}>Remove</button><button className={actionClass} onClick={() => setRemoveId(null)}>Keep</button></div> : <div className="ml-auto flex shrink-0 items-center"><button className={actionClass} onClick={() => window.location.assign(`/play/pvp?invite=${person.uid}`)}><Swords className="mr-1 inline h-4 w-4" />Challenge</button><button aria-label={`Remove ${person.displayName}`} className={actionClass} onClick={() => setRemoveId(person.uid)}><UserMinus className="h-4 w-4" /></button></div>}</div>))}
        </>}
      </div>
    </section> : <button aria-label="Open friends" aria-expanded={false} onClick={() => setIsOpen(true)} className="relative flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg hover:bg-indigo-500"><Users className="h-6 w-6" />{incoming.length + invites.length > 0 && <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full border-2 border-zinc-950 bg-red-400" />}</button>}
  </div>;
}
