export const OPERATOR_LIMITS=Object.freeze({reads:5000000,writes:1300000,bytes:150000000,maxBatches:25});
export const PROVIDER_UNKNOWN=Object.freeze({remainingReads:null,remainingWrites:null,resetTiming:null,sharedUsageReservation:null});
export const ACCOUNTING_BOUND=Object.freeze({reads:32,writes:8});
// Separate conservative cover for earlier unmetered schema/viewer operations.
// These are charged reserves, never represented as measured/provider usage.
export const HISTORICAL_BOUND=Object.freeze({reads:10000,writes:1000});
export function assertOperatorBudget(ledger,estimate,{readReserve=0,writeReserve=0,byteReserve=0,provider=null}={}) {
  const limits={...OPERATOR_LIMITS};
  if(provider?.remainingReads!==undefined && provider.remainingReads!==null && estimate.reads>provider.remainingReads)throw Error('Provider read limit');
  if(provider?.remainingWrites!==undefined && provider.remainingWrites!==null && estimate.writes>provider.remainingWrites)throw Error('Provider write limit');
  if(Number.isFinite(provider?.storageCeilingBytes))limits.bytes=Math.min(limits.bytes,provider.storageCeilingBytes);
  for(const n of [ledger.measured_reads,ledger.measured_writes,ledger.overhead_reads,ledger.overhead_writes,ledger.database_bytes,estimate.reads,estimate.writes,readReserve,writeReserve,byteReserve])if(!Number.isSafeInteger(n)||n<0)throw Error('Invalid operator accounting');
  if(ledger.measured_reads+ledger.overhead_reads+estimate.reads+ACCOUNTING_BOUND.reads+readReserve>limits.reads)throw Error('Operator read budget');
  if(ledger.measured_writes+ledger.overhead_writes+estimate.writes+ACCOUNTING_BOUND.writes+writeReserve>limits.writes)throw Error('Operator write budget');
  if(ledger.database_bytes+byteReserve>limits.bytes)throw Error('Operator storage budget');
}
