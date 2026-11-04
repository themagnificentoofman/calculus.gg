import type { ContentCredit,ContentNotice } from '@/lib/bank/contracts';
export function ContentAttribution({credit}:{credit?:ContentCredit|ContentNotice}){
 if(!credit)return null;
 return <details className="mt-5 min-w-0 border-t border-zinc-700/60 pt-3 text-left text-xs leading-relaxed text-zinc-400">
  <summary className="min-h-11 cursor-pointer py-2">Source, adaptation & license</summary>
  <div className="space-y-3 break-words">
   <p>{credit.credit}</p>
   <p><a className="underline" href={credit.sourceUrl} target="_blank" rel="noreferrer">{credit.sourceItem}</a> · <a className="underline" href={credit.licenseUrl} target="_blank" rel="noreferrer">{credit.license}</a></p>
   <p>{'modifications' in credit?`Changes: ${credit.modifications}`:'Adapted to multiple choice with an original worked explanation. Detailed changes are included with the answered review.'}</p>
  </div>
 </details>;
}
