/** Playback position comes from a monotonic origin, never frame count. */
export class PlaybackClock {
 private base=0;private anchor=0;private running=false;private rate=1;
 readonly duration:number;readonly mono:()=>number;constructor(duration:number,mono:()=>number){this.duration=duration;this.mono=mono;}
 position(){return Math.min(this.duration,Math.max(0,this.base+(this.running?(this.mono()-this.anchor)*this.rate:0)));}
 play(){this.base=this.position();this.anchor=this.mono();this.running=true;}
 pause(){this.base=this.position();this.running=false;}
 seek(ms:number){this.base=Math.max(0,Math.min(this.duration,ms));this.anchor=this.mono();}
 speed(rate:number){this.base=this.position();this.anchor=this.mono();this.rate=rate;}
 get playing(){return this.running&&this.position()<this.duration;}
}
export async function loadReplay(roundId:string,request:(body:any)=>Promise<any>){
 const first=await request({op:'read',roundId});if(!first.manifest||!first.content)return first;
 const events=[],gaps=[...first.gaps];let start=0;
 do{const page=await request({op:'server',roundId,start});if(page.locked||!page.chunks)throw Error('Replay access changed.');for(const c of page.chunks)events.push(...c.events);if(page.missing.length)gaps.push(`Missing server chunks: ${page.missing.join(', ')}`);if(page.done)break;if(page.next<=start)throw Error('Replay cursor did not advance.');start=page.next;}while(start<first.manifest.chunkCount);
 for(const segment of first.segments){start=0;do{const page=await request({op:'client',roundId,segmentId:segment.id,start});events.push(...page.events);if(page.missing.length)gaps.push(`Missing client chunks in ${segment.id}: ${page.missing.join(', ')}`);if(page.done)break;if(page.next<=start)throw Error('Capture cursor did not advance.');start=page.next;}while(start<segment.nextChunk);if(segment.clockUncertain)gaps.push('A recovered clock segment cannot be aligned with server time. Its raw events remain in the event list.');}
 const seen=new Set();const unique=events.filter(e=>{const key=`${e.source}:${e.segmentId||''}:${e.eventId}`;if(seen.has(key))return false;seen.add(key);return true;});
 const accepted=new Map(unique.filter(e=>e.type==='answer_accepted').map(e=>[e.eventId,e]));if(unique.some(e=>e.type==='feedback_displayed'&&(!accepted.has(e.serverEventId)||e.at!==null&&e.at<accepted.get(e.serverEventId)!.at!)))gaps.push('Some feedback observations cannot be ordered exactly against server acceptance; clock uncertainty or missing evidence is shown.');
 return {manifest:first.manifest,content:first.content,solutionReviews:first.solutionReviews,events:unique,playerId:first.playerId,status:gaps.length?'Partial':first.replayStatus,gaps};
}
