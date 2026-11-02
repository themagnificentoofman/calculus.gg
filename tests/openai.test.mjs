import test from 'node:test';
import assert from 'node:assert/strict';
import { generateQuestionsOnServer } from '../lib/server/generate-questions.ts';
import { questionOptionsAreDistinct, shuffleQuestionOptions } from '../lib/server/questions-policy.mjs';

const question = { latexProblem: '\\int 2x\\,dx', options: ['x^2+C', '2+C', 'x+C', '2x^2+C'], correctIndex: 0, explanation: ['\\int 2x\\,dx=x^2+C'], topic: 'integration', difficulty: 'easy' };
const complete = { status: 'completed', output: [{ type: 'reasoning' }, { type: 'message', content: [{ type: 'output_text', text: JSON.stringify({ questions: [question] }) }] }] };

function assertSameQuestion(actual, expected) {
  const { options: actualOptions, correctIndex: actualIndex, ...actualRest } = actual;
  const { options: expectedOptions, correctIndex: expectedIndex, ...expectedRest } = expected;
  assert.deepEqual(actualRest, expectedRest);
  assert.deepEqual([...actualOptions].sort(), [...expectedOptions].sort());
  assert.equal(actualOptions[actualIndex], expectedOptions[expectedIndex]);
}

test('all 24 option permutations preserve the answer, explanation and original question', () => {
  for (let correctIndex = 0; correctIndex < 4; correctIndex++) {
    const original = { ...question, correctIndex };
    const before = structuredClone(original), permutations = new Set(), slots = [0, 0, 0, 0];
    for (let a = 0; a < 4; a++) for (let b = 0; b < 3; b++) for (let c = 0; c < 2; c++) {
      const rolls = [(a + 0.5) / 4, (b + 0.5) / 3, (c + 0.5) / 2];
      const result = shuffleQuestionOptions(original, () => rolls.shift());
      assertSameQuestion(result, original);
      permutations.add(JSON.stringify(result.options));
      slots[result.correctIndex]++;
    }
    assert.equal(permutations.size, 24);
    assert.deepEqual(slots, [6, 6, 6, 6]);
    assert.deepEqual(original, before);
  }
});

test('Responses request uses a server credential and strict schema; extracts output after reasoning', async t => {
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    assert.equal(url, 'https://api.openai.com/v1/responses');
    assert.equal(init.headers.Authorization, 'Bearer test-only');
    const body = JSON.parse(init.body);
    assert.equal(body.store, false);
    assert.equal(body.text.format.strict, true);
    assert.equal(body.text.format.schema.properties.questions.minItems, 1);
    assert.deepEqual(body.text.format.schema.properties.questions.items.properties.topic.enum, ['integration']);
    const fields = body.text.format.schema.properties.questions.items.properties;
    for (const field of [fields.latexProblem, fields.options.items, fields.explanation.items]) {
      const allowed = new RegExp(field.pattern);
      assert.ok(allowed.test(String.raw`\frac{x}{2}`));
      assert.equal(allowed.test(JSON.parse(String.raw`"\frac{x}{2}"`)), false);
    }
    assert.equal(body.max_output_tokens, 3600);
    assert.ok(init.signal instanceof AbortSignal);
    return Response.json(complete);
  });
  t.mock.method(Math, 'random', () => 0);
  const [result] = await generateQuestionsOnServer('integration', 'easy', 1, 'test-only');
  assertSameQuestion(result, question);
  assert.equal(result.correctIndex, 3);
});

test('refusals, incomplete responses, invalid JSON and wrong question content fail closed', async t => {
  for (const payload of [
    { ...complete, status: 'incomplete' },
    { status: 'completed', output: [{ type: 'message', content: [{ type: 'refusal', refusal: 'No' }] }] },
    { status: 'completed', output: [{ type: 'message', content: [{ type: 'output_text', text: 'not json' }] }] },
    { status: 'completed', output: [{ type: 'message', content: [{ type: 'output_text', text: JSON.stringify({ questions: [{ ...question, topic: 'limits' }] }) }] }] },
    { status: 'completed', output: [] },
  ]) {
    t.mock.method(globalThis, 'fetch', async () => Response.json(payload));
    await assert.rejects(generateQuestionsOnServer('integration', 'easy', 1, 'test-only'), e => e.kind === 'invalid-output');
    t.mock.restoreAll();
  }
});

test('provider and transport errors never disclose keys or upstream details and are not retried', async t => {
  for (const status of [401, 429, 500]) {
    let calls = 0;
    t.mock.method(globalThis, 'fetch', async () => { calls++; return Response.json({ error: { message: 'sensitive-upstream-detail' } }, { status }); });
    await assert.rejects(generateQuestionsOnServer('integration', 'easy', 1, 'test-only'), e => e.kind === 'unavailable' && !e.message.includes('sensitive'));
    assert.equal(calls, 1);
    t.mock.restoreAll();
  }
  t.mock.method(globalThis, 'fetch', async () => { throw new DOMException('sensitive', 'TimeoutError'); });
  await assert.rejects(generateQuestionsOnServer('integration', 'easy', 1, 'test-only'), e => e.kind === 'timeout' && !e.message.includes('sensitive'));
});

test('unrenderable model explanations are rejected before the game starts', async t => {
  const bad = { ...question, explanation: [String.raw`\frac{x^{3}}{`] };
  t.mock.method(globalThis, 'fetch', async () => Response.json({ status: 'completed', output: [{ type: 'message', content: [{ type: 'output_text', text: JSON.stringify({ questions: [bad] }) }] }] }));
  await assert.rejects(generateQuestionsOnServer('integration','easy',1,'test-only'), e => e.kind === 'invalid-output');
});


test('recoverable JSON control escapes are returned as canonical LaTeX', async t => {
  for (const source of [JSON.parse(String.raw`"\frac{x}{2}"`),JSON.parse(String.raw`"\textnormal{Test}"`)]) {
    const bad = {...question, latexProblem:source};
    t.mock.method(globalThis, 'fetch', async () => Response.json({status:'completed',output:[{type:'message',content:[{type:'output_text',text:JSON.stringify({questions:[bad]})}]}]}));
    const result = await generateQuestionsOnServer('integration','easy',1,'test-only');
    assert.equal(result[0].latexProblem, source.includes('rac') ? String.raw`\frac{x}{2}` : String.raw`\textnormal{Test}`);
    t.mock.restoreAll();
  }
});


const responseWith = questions => Response.json({status:'completed',output:[{type:'message',content:[{type:'output_text',text:JSON.stringify({questions})}]}]});

test('duplicate choices are repaired once; persistent duplicates fail before a game starts', async t => {
  const duplicate = { ...question, options: [question.options[0], question.options[0], ...question.options.slice(2)] };
  assert.equal(questionOptionsAreDistinct({ options: [String.raw`\dfrac{x}{2}`, String.raw`\frac{x}{2}`, 'x', '2x'] }), false);
  assert.equal(questionOptionsAreDistinct({ options: [String.raw`\left(x+1\right)`, '(x + 1)', 'x', '2x'] }), false);
  for (const repaired of [question, duplicate]) {
    let calls = 0;
    t.mock.method(globalThis, 'fetch', async () => responseWith([++calls === 1 ? duplicate : repaired]));
    const result = generateQuestionsOnServer('integration', 'easy', 1, 'test-only');
    if (repaired === duplicate) await assert.rejects(result, e => e.kind === 'invalid-output');
    else assertSameQuestion((await result)[0], question);
    assert.equal(calls, 2);
    t.mock.restoreAll();
  }
});

test('one bounded notation repair shares the original deadline and retains valid questions', async t => {
  const bad = {...question, explanation:[String.raw`\frac{x^3}{`]};
  const calls=[];
  t.mock.method(globalThis,'fetch',async (url,init)=>{
    calls.push(init);
    return calls.length===1 ? responseWith([question,bad]) : responseWith([question]);
  });
  const result=await generateQuestionsOnServer('integration','easy',2,'test-only');
  assert.equal(result.length, 2);
  result.forEach(q => assertSameQuestion(q, question));
  assert.equal(calls.length,2);
  assert.equal(calls[0].signal,calls[1].signal);
  const repair=JSON.parse(calls[1].body);
  assert.equal(repair.text.format.schema.properties.questions.minItems,1);
  assert.ok(repair.max_output_tokens<=6000);
  assert.equal(repair.store,false);
});

test('notation repair stops after one attempt and cannot change the answer index', async t => {
  const bad={...question,explanation:[String.raw`\unknown{x}`]};
  for(const second of [bad,{...question,correctIndex:1}]){
    let calls=0;
    t.mock.method(globalThis,'fetch',async()=>responseWith([++calls===1?bad:second]));
    await assert.rejects(generateQuestionsOnServer('integration','easy',1,'test-only'),e=>e.kind==='invalid-output');
    assert.equal(calls,2);
    t.mock.restoreAll();
  }
  let calls=0;
  t.mock.method(globalThis,'fetch',async()=>{calls++;return responseWith(Array(4).fill(bad));});
  await assert.rejects(generateQuestionsOnServer('integration','easy',4,'test-only'),e=>e.kind==='invalid-output');
  assert.equal(calls,1);
});

test('unrecognized control characters remain invalid after normalization',async t=>{
  for (const source of ['x\u0001','\fnotACommand','\bunknown']) {
    t.mock.method(globalThis,'fetch',async()=>responseWith([{...question,latexProblem:source}]));
    await assert.rejects(generateQuestionsOnServer('integration','easy',1,'test-only'),e=>e.kind==='invalid-output');
    t.mock.restoreAll();
  }
});
