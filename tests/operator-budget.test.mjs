import test from 'node:test';
import assert from 'node:assert/strict';
import {OPERATOR_LIMITS,PROVIDER_UNKNOWN,assertOperatorBudget} from '../lib/server/operator-budget.mjs';
test('operator limits are independent of unavailable provider telemetry and enforce lower reported limits',()=>{
  const l={measured_reads:7431,measured_writes:3860,overhead_reads:10000,overhead_writes:1000,database_bytes:1077248};
  assert.doesNotThrow(()=>assertOperatorBudget(l,{reads:2000,writes:1020},{provider:PROVIDER_UNKNOWN,readReserve:2500000,writeReserve:40000}));
  assert.throws(()=>assertOperatorBudget({...l,measured_writes:1299990},{reads:1,writes:1}),/write budget/);
  assert.throws(()=>assertOperatorBudget({...l,measured_reads:4999990},{reads:1,writes:1}),/read budget/);
  assert.throws(()=>assertOperatorBudget({...l,database_bytes:150000001},{reads:1,writes:1}),/storage budget/);
  assert.throws(()=>assertOperatorBudget(l,{reads:100,writes:100},{provider:{remainingWrites:99}}),/Provider write limit/);
  assert.throws(()=>assertOperatorBudget(l,{reads:100,writes:100},{provider:{remainingReads:99}}),/Provider read limit/);
  assert.throws(()=>assertOperatorBudget(l,{reads:1,writes:1},{provider:{storageCeilingBytes:1000000}}),/storage budget/);
  assert.deepEqual(OPERATOR_LIMITS,{reads:5000000,writes:1300000,bytes:150000000,maxBatches:25});
  assert.equal(PROVIDER_UNKNOWN.sharedUsageReservation,null);
});
