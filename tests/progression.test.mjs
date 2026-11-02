import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateProblemXp, getLevelFromXp, getXpForLevel, getXpProgress, getStandings, calculateRatings, hasRating, RATING_K } from '../lib/progression.ts';
const player = (uid, score, rating = 0, answers = {0:{correct:true}}) => ({uid, score, rating, answers, attempted:Object.keys(answers).length, correct:Object.values(answers).filter(a=>a.correct).length});
const close = (a,b) => assert.ok(Math.abs(a-b)<1e-9, `${a} != ${b}`);
test('XP rewards difficulty consistently across modes, without finish bonuses', () => {
  for (const mode of ['test','rapid','pvp','multiplayer']) {
    assert.deepEqual(['easy','medium','hard','olympiad'].map(d=>calculateProblemXp(mode,d)),[10,20,30,50]);
    for (const bad of ['unknown','constructor','__proto__']) assert.equal(calculateProblemXp(mode,bad),0);
  }
});
test('existing quadratic level thresholds and progress remain stable', () => {
  for (let level=0;level<=100;level++) {
    const threshold=getXpForLevel(level);
    assert.equal(getLevelFromXp(threshold),level);
    if(level) assert.equal(getLevelFromXp(threshold-1),level-1);
    assert.deepEqual(getXpProgress(threshold),{current:0,max:100*(2*level+1),percentage:0});
  }
  for (const bad of [NaN,Infinity,-1]) assert.deepEqual(getXpProgress(bad),{current:0,max:100,percentage:0});
});
test('equal ratings give a symmetric 16-point decisive result, zero for a draw', () => {
  const result=calculateRatings([player('a',5),player('b',3)],[]);
  assert.equal(result.a.ratingChange,16); assert.equal(result.b.ratingChange,-16);
  const draw=calculateRatings([player('a',5),player('b',5)],[]);
  assert.equal(draw.a.ratingChange,0); assert.equal(draw.a.outcome,'draw'); assert.equal(draw.b.outcome,'draw');
});
test('an upset earns more; a stronger player gains less for an expected win', () => {
  const upset=calculateRatings([player('a',5,0),player('b',3,400)],[]);
  const expected=calculateRatings([player('a',5,400),player('b',3,0)],[]);
  assert.ok(upset.a.ratingChange>16); assert.ok(expected.a.ratingChange<16);
  close(upset.a.ratingChange+upset.b.ratingChange,0);
});
test('multiplayer ties have the same placement regardless of join order', () => {
  const ps=[player('a',4),player('b',4),player('c',1)];
  const original=calculateRatings(ps,[]);
  for (const order of [[ps[2],ps[1],ps[0]],[ps[1],ps[0],ps[2]]]) assert.deepEqual(calculateRatings(order,[]),original);
  assert.equal(original.a.rank,1); assert.equal(original.b.rank,1); assert.equal(original.c.rank,3);
  assert.equal(original.a.outcome,'draw'); assert.equal(original.b.outcome,'draw');
  close(original.a.ratingChange,original.b.ratingChange);
});
test('rating updates conserve the pool and stay bounded for 2–10 players', () => {
  for(let n=2;n<=10;n++) for(let run=0;run<30;run++) {
    const ps=Array.from({length:n},(_,i)=>player(`p${i}`,(i*13+run)%7,(i*73+run*31)%1500-300,i%3===0?{}:{0:{correct:true}}));
    const values=Object.values(calculateRatings(ps,[{topic:'integration'}]));
    close(values.reduce((sum,r)=>sum+r.ratingChange,0),0);
    assert.ok(values.every(r=>Math.abs(r.ratingChange)<=RATING_K));
    close(values.reduce((sum,r)=>sum+(r.topicChanges.integration||0),0),0);
  }
});
test('no rating transfer for empty or all-wrong games; no inactive victory over a penalty', () => {
  for(const ps of [[player('a',0,500,{}),player('b',0,0,{})],[player('a',0,500,{0:{correct:false}}),player('b',0,0,{0:{correct:false}})]]) {
    const result=calculateRatings(ps,[{topic:'integration'}]);
    assert.equal(result.a.ratingChange,0); assert.equal(result.b.ratingChange,0);
    assert.equal(result.a.rated,false);
  }
  const standings=getStandings([player('a',0,0,{}),player('b',-1,0,{0:{correct:false}})]);
  assert.equal(standings.find(p=>p.uid==='b').outcome,'win');
});
test('unseen questions and unplayed topics do not dilute overall or topic rating', () => {
  const a=player('a',1,100,{0:{correct:true}}),b=player('b',0,100,{0:{correct:false}});
  const base=calculateRatings([a,b],[{topic:'integration'}]);
  const expanded=calculateRatings([{...a,topicRatings:{limits:0,series:0}},{...b,topicRatings:{limits:0}}],[{topic:'integration'},{topic:'limits'}]);
  assert.deepEqual(base,expanded);
  assert.equal(base.a.topicChanges.integration,16);
  assert.deepEqual(calculateRatings([a,{...b,answers:{1:{correct:false}}}],[{topic:'integration'},{topic:'integration'}]).a.topicChanges,{});
});
test('topic expectation uses topic ratings independently of overall rating', () => {
  const a={...player('a',1,500),topicRatings:{integration:-400}};
  const b={...player('b',0,0,{0:{correct:false}}),topicRatings:{integration:0}};
  const result=calculateRatings([a,b],[{topic:'integration'}]);
  assert.ok(result.a.ratingChange<16); assert.ok(result.a.topicChanges.integration>16);
});
test('rated zero and negative values remain rated; untouched new accounts do not', () => {
  assert.equal(hasRating({rating:0,ratedGames:1}),true);
  assert.equal(hasRating({rating:-16}),true);
  assert.equal(hasRating({rating:0,wins:1}),true);
  assert.equal(hasRating({rating:0,ratedGames:0,draws:1}),false);
  assert.equal(hasRating({rating:0}),false);
});
