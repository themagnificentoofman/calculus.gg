export type NetworkNode = { x: number; y: number; vx: number; vy: number; pushX: number; pushY: number; radius: number };
export type NetworkPointer = { x: number; y: number; active: boolean; held: boolean };
export type NetworkEdge = { a: number; b: number; opacity: number };
export const NETWORK = { minSpeed: 7, maxSpeed: 18, linkDistance: 155, lightRadius: 220, pushRadius: 145, maxNodes: 100, margin: 24 };
const clamp = (value: number, min = 0, max = 1) => Math.min(max, Math.max(min, value));

export function nodeCount(width: number, height: number) {
  return Math.round(clamp(width * height / 12500, 28, width < 600 ? 48 : NETWORK.maxNodes));
}

export function createNode(width: number, height: number, random = Math.random): NetworkNode {
  const direction = random() * Math.PI * 2;
  const speed = NETWORK.minSpeed + random() * (NETWORK.maxSpeed - NETWORK.minSpeed);
  return { x: random() * width, y: random() * height, vx: Math.cos(direction) * speed, vy: Math.sin(direction) * speed, pushX: 0, pushY: 0, radius: 1.3 + random() * 1.1 };
}

// Base velocity stays constant; a held pointer adds a bounded, damped impulse.
export function advanceNode(node: NetworkNode, pointer: NetworkPointer, seconds: number, width: number, height: number) {
  const dt = clamp(seconds, 0, 0.05);
  if (pointer.active && pointer.held) {
    const dx = node.x - pointer.x, dy = node.y - pointer.y;
    const distance = Math.hypot(dx, dy);
    if (distance < NETWORK.pushRadius) {
      const force = 240 * (1 - distance / NETWORK.pushRadius) ** 2 * dt;
      const direction = distance > 0.01 ? [dx / distance, dy / distance] : [node.vx / Math.hypot(node.vx, node.vy), node.vy / Math.hypot(node.vx, node.vy)];
      node.pushX += direction[0] * force;
      node.pushY += direction[1] * force;
    }
  }
  const speed = Math.hypot(node.pushX, node.pushY);
  if (speed > 110) { node.pushX *= 110 / speed; node.pushY *= 110 / speed; }
  node.x += (node.vx + node.pushX) * dt;
  node.y += (node.vy + node.pushY) * dt;
  const damping = Math.exp(-2.4 * dt);
  node.pushX *= damping; node.pushY *= damping;
  let wrapped = false;
  const m = NETWORK.margin;
  if (node.x < -m) { node.x = width + m; wrapped = true; }
  else if (node.x > width + m) { node.x = -m; wrapped = true; }
  if (node.y < -m) { node.y = height + m; wrapped = true; }
  else if (node.y > height + m) { node.y = -m; wrapped = true; }
  return wrapped;
}

export function edgeOpacity(current: number, distance: number, seconds: number, instant = false) {
  const target = distance < NETWORK.linkDistance ? 0.2 + 0.8 * (1 - distance / NETWORK.linkDistance) : 0;
  return instant ? target : current + (target - current) * (1 - Math.exp(-5 * seconds));
}

export function proximity(x: number, y: number, pointer: NetworkPointer) {
  if (!pointer.active) return 0;
  const strength = clamp(1 - Math.hypot(x - pointer.x, y - pointer.y) / NETWORK.lightRadius);
  return strength * strength * (3 - 2 * strength);
}

export function edgeProximity(a: NetworkNode, b: NetworkNode, pointer: NetworkPointer) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const t = clamp(((pointer.x - a.x) * dx + (pointer.y - a.y) * dy) / (dx * dx + dy * dy || 1));
  return { t, light: proximity(a.x + t * dx, a.y + t * dy, pointer) };
}

export function boundaryOpacity(node: NetworkNode, width: number, height: number) {
  return clamp(Math.min(node.x + NETWORK.margin, width + NETWORK.margin - node.x, node.y + NETWORK.margin, height + NETWORK.margin - node.y) / NETWORK.margin);
}
