import type {ClientEvent,ClientEventType} from './contracts.ts';
type Observer=(type:ClientEventType,data?:Partial<ClientEvent>)=>void;
const observers=new Map<string,Observer>();
export function registerCapture(round:string,observer:Observer){observers.set(round,observer);return()=>{if(observers.get(round)===observer)observers.delete(round);};}
export function observeReplay(round:string,type:ClientEventType,data:Partial<ClientEvent>={}){observers.get(round)?.(type,data);}
