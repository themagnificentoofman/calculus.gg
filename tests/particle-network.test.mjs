import test from 'node:test';
import assert from 'node:assert/strict';
import { NETWORK, advanceNode, boundaryOpacity, createNode, edgeOpacity, edgeProximity, nodeCount, proximity } from '../lib/particle-network.ts';

const idle = { x: 0, y: 0, active: false, held: false };
const node = () => ({ x: 400, y: 400, vx: 10, vy: -4, pushX: 0, pushY: 0, radius: 2 });

test('network density and randomized drift stay bounded on phone and large displays', () => {
  assert.ok(nodeCount(390, 844) >= 28 && nodeCount(390, 844) <= 48);
  assert.equal(nodeCount(8000, 8000), NETWORK.maxNodes);
  for (let i = 0; i < 100; i++) {
    const n = createNode(390, 844);
    const speed = Math.hypot(n.vx, n.vy);
    assert.ok(speed >= NETWORK.minSpeed - 1e-9 && speed <= NETWORK.maxSpeed + 1e-9);
    assert.ok(n.x >= 0 && n.x <= 390 && n.y >= 0 && n.y <= 844);
  }
});

test('idle drift is constant and independent of refresh rate', () => {
  for (const fps of [30, 60, 120]) {
    const n = node();
    for (let i = 0; i < fps * 4; i++) advanceNode(n, idle, 1 / fps, 1000, 1000);
    assert.ok(Math.abs(n.x - 440) < 1e-8);
    assert.ok(Math.abs(n.y - 384) < 1e-8);
    assert.equal(n.vx, 10); assert.equal(n.vy, -4);
  }
});

test('holding repels nearby nodes, release restores the original drift, and exact overlap stays finite', () => {
  const n = node(), original = node();
  const held = { x: 390, y: 400, active: true, held: true };
  for (let i = 0; i < 60; i++) { advanceNode(n, held, 1 / 60, 1000, 1000); advanceNode(original, idle, 1 / 60, 1000, 1000); }
  assert.ok(n.x > original.x + 20);
  assert.ok(Math.hypot(n.pushX, n.pushY) <= 110);
  for (let i = 0; i < 300; i++) advanceNode(n, idle, 1 / 60, 1000, 1000);
  assert.ok(Math.hypot(n.pushX, n.pushY) < 0.001);
  assert.equal(n.vx, original.vx); assert.equal(n.vy, original.vy);
  const overlap = node();
  advanceNode(overlap, { ...held, x: overlap.x, y: overlap.y }, 1 / 60, 1000, 1000);
  assert.ok(Object.values(overlap).every(Number.isFinite));
});

test('connections fade in and out without popping when crossing the distance limit', () => {
  let opacity = 0;
  opacity = edgeOpacity(opacity, 80, 1 / 60);
  assert.ok(opacity > 0 && opacity < 0.1);
  for (let i = 0; i < 60; i++) opacity = edgeOpacity(opacity, 80, 1 / 60);
  assert.ok(opacity > 0.5);
  const firstOutside = edgeOpacity(opacity, NETWORK.linkDistance + 1, 1 / 60);
  assert.ok(firstOutside > 0 && firstOutside < opacity);
  for (let i = 0; i < 120; i++) opacity = edgeOpacity(opacity, 200, 1 / 60);
  assert.ok(opacity < 0.001);
});

test('proximity highlights both nodes and the interior of an edge', () => {
  const pointer = { x: 100, y: 100, active: true, held: false };
  assert.equal(proximity(100, 100, pointer), 1);
  assert.equal(proximity(1000, 1000, pointer), 0);
  assert.equal(proximity(100, 100, idle), 0);
  const edge = edgeProximity({ ...node(), x: 40, y: 100 }, { ...node(), x: 160, y: 100 }, pointer);
  assert.equal(edge.t, 0.5); assert.equal(edge.light, 1);
});

test('wrapping happens offscreen and a suspended tab cannot produce a large position jump', () => {
  const n = { ...node(), x: 1000 + NETWORK.margin - 0.1, vx: 18 };
  assert.equal(advanceNode(n, idle, 1 / 60, 1000, 1000), true);
  assert.equal(boundaryOpacity(n, 1000, 1000), 0);
  const resumed = node(); advanceNode(resumed, idle, 60, 1000, 1000);
  assert.ok(resumed.x - 400 <= 0.5);
});
