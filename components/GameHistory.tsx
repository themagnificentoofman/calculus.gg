'use client';
import {useEffect,useState} from 'react';
import {useAuth} from './AuthProvider';
import {db} from '@/firebase';
import {loadHistoryPage,historyDate,type HistoryCursor,type HistoryFilters,type HistoryRow,HISTORY_PAGE_SIZE} from '@/lib/history';
import {apiRequest} from '@/lib/game-session';
import {legacyMessage} from '@/lib/replay/contracts';
const modeName=(mode:string)=>mode==='ffa'||mode==='multiplayer'?'Multiplayer':mode==='pvp'?'PvP':mode==='rapid'?'Rapid':mode==='test'?'Test':mode||'Unknown mode';
export function GameHistory(){const {user}=useAuth();return user?<HistoryBrowser uid={user.uid}/>:null;}
export function HistoryBrowser({uid,load=loadHistoryPage}:{uid:string;load?:typeof loadHistoryPage}){
const [filters,setFilters]=useState<HistoryFilters>({}),[pages,setPages]=useState<HistoryCursor[]>([{}]),[page,setPage]=useState(0),[rows,setRows]=useState<HistoryRow[]>([]),[next,setNext]=useState<HistoryCursor>({}),[more,setMore]=useState(false),[loading,setLoading]=useState(false),[error,setError]=useState(''),[retry,setRetry]=useState(0),[statuses,setStatuses]=useState<Record<string,string>>({});
 const change=(patch:HistoryFilters)=>{setFilters(f=>({...f,...patch}));setPages([{}]);setPage(0);};
 useEffect(()=>{let active=true;if(!uid)return;setLoading(true);setError('');setStatuses({});
  if(filters.from&&filters.to&&filters.from>filters.to){setError('The end date must be on or after the start date.');setLoading(false);return;}
  void load(db,uid,filters,pages[page]).then(async result=>{if(!active)return;setRows(result.rows);setNext(result.cursor);setMore(result.hasMore);setLoading(false);const ids=result.rows.filter(r=>r.replayVersion===1).map(r=>r.id);if(ids.length){try{const response=await apiRequest('replay',{op:'statuses',roundIds:ids});if(active)setStatuses(response.statuses);}catch{if(active)setStatuses(Object.fromEntries(ids.map(id=>[id,'Status unavailable'])));}}}).catch(()=>{if(active){setError('History could not be loaded. Your stored rounds are unchanged.');setLoading(false);}});
  return()=>{active=false;};
 },[uid,filters,page,pages,retry]);
 const select=(label:string,key:keyof HistoryFilters,options:[string,string][])=> <label className="grid gap-1 text-xs text-zinc-400">{label}<select className="min-h-11 min-w-0 rounded-lg border border-zinc-700 bg-zinc-950 px-2 text-white" value={filters[key]||'all'} onChange={e=>change({[key]:e.target.value})}>{options.map(([v,t])=><option key={v} value={v}>{t}</option>)}</select></label>;
 return <section className="rounded-3xl border border-zinc-800 bg-zinc-900/40 p-4 sm:p-6" aria-label="Round history">
  <h3 className="text-lg font-semibold">Round history</h3><p className="mb-4 text-sm text-zinc-400">All stored rounds remain available. Showing up to {HISTORY_PAGE_SIZE} per page. Filters search your full history.</p>
  <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
   {select('Mode','mode',[['all','All modes'],['test','Test'],['rapid','Rapid'],['pvp','PvP'],['multiplayer','Multiplayer']])}
   {select('Topic','topic',[['all','All topics'],['integration','Integration'],['differentiation','Differentiation'],['limits','Limits'],['series','Series'],['differential equations','Differential equations'],['multivariable','Multivariable'],['mixed','Mixed'],['unknown','Unknown']])}
   {select('Difficulty','difficulty',[['all','All difficulties'],['easy','Easy'],['medium','Medium'],['hard','Hard'],['olympiad','Olympiad'],['unknown','Unknown']])}
   {select('Recorded result','result',[['all','All results'],['win','Win'],['loss','Loss'],['draw','Draw'],['completed','Completed'],['unplayed','Unplayed'],['unknown','No recorded result']])}
   {select('Replay capability','replay',[['all','All rounds'],['recorded','Recording enabled'],['legacy','Legacy']])}
   <div className="flex items-end"><button className="min-h-11 rounded-lg border border-zinc-700 px-3" onClick={()=>{setFilters({});setPages([{}]);setPage(0);}}>Clear filters</button></div>
   <form key={`${filters.from||''}:${filters.to||''}`} className="col-span-2 grid grid-cols-2 gap-3 sm:col-span-3 sm:grid-cols-3" onSubmit={event=>{event.preventDefault();const values=new FormData(event.currentTarget);change({from:String(values.get('from')||''),to:String(values.get('to')||'')});}}>
    <label className="grid gap-1 text-xs text-zinc-400">From (UTC)<input name="from" aria-label="History start date" type="date" className="min-h-11 min-w-0 rounded-lg bg-zinc-950 px-2 text-white" defaultValue={filters.from||''}/></label>
    <label className="grid gap-1 text-xs text-zinc-400">Through (UTC)<input name="to" aria-label="History end date" type="date" className="min-h-11 min-w-0 rounded-lg bg-zinc-950 px-2 text-white" defaultValue={filters.to||''}/></label>
    <div className="flex items-end"><button type="submit" className="min-h-11 rounded-lg border border-emerald-700 px-3 text-sm text-emerald-300">Apply range</button></div>
   </form>
   <div className="col-span-2 flex flex-wrap gap-4 sm:col-span-3"><button className="min-h-11 text-sm underline" onClick={()=>{const now=new Date();change({from:new Date(now.getTime()-7*86400000).toISOString().slice(0,10),to:now.toISOString().slice(0,10)});}}>Last 7 days</button><button className="min-h-11 text-sm underline" onClick={()=>change({from:'',to:''})}>All dates</button></div>
  </div>
  <p className="mb-3 text-xs text-zinc-500">Unknown dates appear under All dates. Legacy results without a saved result receipt are labeled “No recorded result.” Replay capability filters do not imply a complete recording.</p>
  {error?<p role="alert" className="text-red-300">{error} <button className="min-h-11 underline" onClick={()=>setRetry(n=>n+1)}>Retry</button></p>:loading?<p role="status">Loading history…</p>:<div className="space-y-3">{!rows.length&&<p className="py-6 text-zinc-400">No rounds match this range.</p>}{rows.map(g=>{const at=historyDate(g.createdAt),status=g.replayVersion===1?statuses[g.id]||'Checking…':'Legacy',outcome=g.receipts?.[uid]?.outcome;return <article key={g.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-zinc-800 bg-zinc-950/50 p-3"><div className="min-w-0"><p className="font-medium">{modeName(g.mode)} · <span className="capitalize">{g.status||'Unknown status'}</span></p><p className="text-xs text-zinc-400">{at===null?'Unknown date':new Date(at).toLocaleString(undefined,{timeZone:'UTC'})+' UTC'} · {g.category||'Unknown topic'} · {g.difficulty||'Unknown difficulty'}</p><p className="mt-1 text-xs text-zinc-400">{outcome||'No recorded result'} · Score {g.scores?.[uid]??'unknown'}</p><p className="mt-1 text-xs text-zinc-500">{status==='Legacy'?legacyMessage:`Replay: ${status}`}</p></div><div className="flex flex-wrap gap-3">{g.replayVersion===1&&['finished','cancelled'].includes(g.status)&&<a className="min-h-11 py-3 text-sm text-emerald-400 underline" href={`/replay/${g.id}`}>Replay &amp; analyze</a>}{['active','waiting'].includes(g.status)&&<a className="min-h-11 py-3 text-sm text-sky-400 underline" href={`/play/${g.mode==='ffa'?'multiplayer':g.mode}?round=${g.id}`}>Resume round</a>}</div></article>;})}</div>}
  <nav aria-label="History pages" className="mt-5 flex items-center justify-between gap-3"><button className="min-h-11 rounded-lg border border-zinc-700 px-4 disabled:opacity-40" disabled={!page||loading} onClick={()=>setPage(p=>p-1)}>Previous</button><span className="text-sm">Page {page+1}</span><button className="min-h-11 rounded-lg border border-zinc-700 px-4 disabled:opacity-40" disabled={!more||loading||!!error} onClick={()=>{setPages(p=>[...p.slice(0,page+1),next]);setPage(p=>p+1);}}>Next</button></nav>
 </section>;
}
