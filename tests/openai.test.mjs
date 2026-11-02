import test from 'node:test';
import assert from 'node:assert/strict';
import { generateQuestionsOnServer } from '../lib/server/generate-questions.ts';

const question = { latexProblem: '\\int 2x\\,dx', options: ['x^2+C', '2+C', 'x+C', '2x^2+C'], correctIndex: 0, explanation: ['\\int 2x\\,dx=x^2+C'], topic: 'integration', difficulty: 'easy' };
const complete = { status: 'completed', output: [{ type: 'reasoning' }, { type: 'message', content: [{ type: 'output_text', text: JSON.stringify({ questions: [question] }) }] }] };

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
  assert.deepEqual(await generateQuestionsOnServer('integration', 'easy', 1, 'test-only'), [question]);
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


test('new model output cannot silently render JSON control escapes as different mathematics', async t => {
  for (const source of [JSON.parse(String.raw`"\frac{x}{2}"`),JSON.parse(String.raw`"\textnormal{Test}"`)]) {
    const bad = {...question, latexProblem:source};
    t.mock.method(globalThis, 'fetch', async () => Response.json({status:'completed',output:[{type:'message',content:[{type:'output_text',text:JSON.stringify({questions:[bad]})}]}]}));
    await assert.rejects(generateQuestionsOnServer('integration','easy',1,'test-only'), e=>e.kind==='invalid-output');
    t.mock.restoreAll();
  }
});
