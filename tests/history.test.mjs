import test from 'node:test';
import assert from 'node:assert/strict';
import {initializeApp,deleteApp} from 'firebase/app';
import {getAuth,connectAuthEmulator,signInAnonymously} from 'firebase/auth';
import {getFirestore,connectFirestoreEmulator,terminate} from 'firebase/firestore';
import {firestoreStore} from '../lib/server/firestore-admin.ts';
import {loadHistoryPage,historyDate} from '../lib/history.ts';
test('Historical date compatibility preserves unknowns',()=>{assert.equal(historyDate('2020-01-01T00:00:00Z'),1577836800000);assert.equal(historyDate({seconds:1577836800,nanoseconds:0}),1577836800000);assert.equal(historyDate(1577836800),1577836800000);assert.equal(historyDate(null),null);assert.equal(historyDate('bad'),null);});
test('Full history filters precede pagination; all encodings, >50 records, stable ties and ranges', {skip:process.env.FIRESTORE_EMULATOR_HOST!=='127.0.0.1:8080',timeout:120000},async()=>{
 const app=initializeApp({projectId:'demo-calculus-rendering',apiKey:'emulator-only'},`history-${Date.now()}`),auth=getAuth(app);connectAuthEmulator(auth,'http://127.0.0.1:9099',{disableWarnings:true});const db=getFirestore(app);connectFirestoreEmulator(db,'127.0.0.1',8080);
 try{
 const {user}=await signInAnonymously(auth),uid=user.uid,store=firestoreStore('demo-calculus-rendering','(default)',async()=> 'owner','http://127.0.0.1:8080');
 const fixtures=Array.from({length:83},(_,i)=>{const date=new Date(Date.UTC(2024,0,1+Math.floor(i/3)));return {id:`history_${uid}_${String(i).padStart(3,'0')}`,value:{players:[uid],mode:i<70?'test':'ffa',status:'finished',createdAt:i%3===0?date:i%3===1?date.toISOString():date.getTime(),category:i<70?'integration':'differentiation',difficulty:'hard',scores:{[uid]:1},...(i<70?{}:{replayVersion:1,receipts:{[uid]:{outcome:'win'}}})}};});
 fixtures.push({id:`history_${uid}_unknown`,value:{players:[uid],mode:'test',status:'finished'}});fixtures.push({id:`history_${uid}_object`,value:{players:[uid],mode:'test',status:'finished',createdAt:{seconds:Date.UTC(2023,0,1)/1000}}});
 await store.transaction(async tx=>{await tx.get(`games/${fixtures[0].id}`);for(const x of fixtures)tx.set(`games/${x.id}`,x.value);});
 let cursor={},all=[],more=true;while(more){const page=await loadHistoryPage(db,uid,{},cursor);assert.ok(page.rows.length<=25);all.push(...page.rows);cursor=page.cursor;more=page.hasMore;assert.ok(all.length<=fixtures.length);}
 assert.equal(all.length,fixtures.length);assert.equal(new Set(all.map(r=>r.id)).size,fixtures.length);assert.ok(all.some(r=>historyDate(r.createdAt)===null));
 const filtered=await loadHistoryPage(db,uid,{mode:'multiplayer',topic:'differentiation',replay:'recorded',result:'win'});assert.equal(filtered.rows.length,13);assert.ok(filtered.rows.every(r=>r.mode==='ffa'));
 const range=await loadHistoryPage(db,uid,{from:'2024-01-01',to:'2024-01-03'});assert.equal(range.rows.length,9);
 const legacy=await loadHistoryPage(db,uid,{replay:'legacy'});assert.ok(legacy.rows.every(r=>r.replayVersion!==1));
 }finally{await terminate(db);await deleteApp(app);}
});
