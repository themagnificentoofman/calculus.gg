'use client';

import { useEffect, useRef } from 'react';
import { NETWORK, advanceNode, boundaryOpacity, createNode, edgeOpacity, edgeProximity, nodeCount, proximity, type NetworkEdge, type NetworkNode, type NetworkPointer } from '@/lib/particle-network';

export function WelcomeNetwork() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const surface = canvas?.parentElement;
    const host = surface?.parentElement;
    const context = canvas?.getContext('2d');
    if (!canvas || !surface || !host || !context) return;

    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const pointer: NetworkPointer = { x: 0, y: 0, active: false, held: false };
    let pointerId: number | null = null;
    let touchInput = false;
    let clientX = 0, clientY = 0;
    let nodes: NetworkNode[] = [];
    const edges = new Map<number, NetworkEdge>();
    let width = 0, height = 0, frame = 0, lastTime = 0;
    let disposed = false;
    const gray = (light: number) => { const value = Math.round(76 + 168 * light); return `rgb(${value}, ${value}, ${value})`; };

    function draw(seconds: number) {
      if (!context || !width || !height) return;
      const still = motion.matches;
      const wrapped = new Set<number>();
      if (!still) nodes.forEach((node, i) => { if (advanceNode(node, pointer, seconds, width, height)) wrapped.add(i); });
      // Never draw a fading connection across the canvas when an endpoint wraps.
      if (wrapped.size) for (const [key, edge] of edges) if (wrapped.has(edge.a) || wrapped.has(edge.b)) edges.delete(key);
      context.clearRect(0, 0, width, height);
      const lights = nodes.map(node => proximity(node.x, node.y, pointer));
      const visibility = nodes.map(node => boundaryOpacity(node, width, height));
      for (let a = 0; a < nodes.length; a++) for (let b = a + 1; b < nodes.length; b++) {
        const from = nodes[a], to = nodes[b];
        const distance = Math.hypot(from.x - to.x, from.y - to.y);
        const key = a * NETWORK.maxNodes + b;
        const existing = edges.get(key);
        if (!existing && distance >= NETWORK.linkDistance) continue;
        const opacity = edgeOpacity(existing?.opacity || 0, distance, seconds, still);
        if (opacity < 0.003 && distance >= NETWORK.linkDistance) { edges.delete(key); continue; }
        edges.set(key, { a, b, opacity });
        const near = edgeProximity(from, to, pointer);
        const gradient = context.createLinearGradient(from.x, from.y, to.x, to.y);
        gradient.addColorStop(0, gray(lights[a]));
        if (near.t > 0.01 && near.t < 0.99) gradient.addColorStop(near.t, gray(near.light));
        gradient.addColorStop(1, gray(lights[b]));
        context.strokeStyle = gradient;
        context.globalAlpha = opacity * visibility[a] * visibility[b] * (0.42 + 0.25 * near.light);
        context.lineWidth = 0.75 + 0.3 * near.light;
        context.beginPath(); context.moveTo(from.x, from.y); context.lineTo(to.x, to.y); context.stroke();
      }
      nodes.forEach((node, i) => {
        const light = lights[i];
        if (light > 0.1) {
          context.globalAlpha = visibility[i] * light * 0.07;
          context.fillStyle = '#ffffff';
          context.beginPath(); context.arc(node.x, node.y, node.radius * 4, 0, Math.PI * 2); context.fill();
        }
        context.globalAlpha = visibility[i] * (0.8 + 0.2 * light);
        context.fillStyle = gray(light);
        context.beginPath(); context.arc(node.x, node.y, node.radius, 0, Math.PI * 2); context.fill();
      });
      context.globalAlpha = 1;
    }

    function tick(time: number) {
      frame = 0;
      if (disposed || document.hidden || motion.matches) return;
      const seconds = lastTime ? Math.min((time - lastTime) / 1000, 0.05) : 1 / 60;
      lastTime = time;
      draw(seconds);
      frame = requestAnimationFrame(tick);
    }
    function start() {
      if (!disposed && !document.hidden && !motion.matches && !frame) frame = requestAnimationFrame(tick);
    }
    function stop() { cancelAnimationFrame(frame); frame = 0; lastTime = 0; }
    function refreshPointer() {
      if (!surface) return;
      const rect = surface.getBoundingClientRect();
      pointer.x = clientX - rect.left; pointer.y = clientY - rect.top;
      pointer.active = pointer.x >= 0 && pointer.y >= 0 && pointer.x <= width && pointer.y <= height;
    }
    function resize() {
      if (!canvas || !surface || !context || disposed) return;
      const rect = surface.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      const nextWidth = rect.width, nextHeight = rect.height;
      if (width && height) nodes.forEach(node => { node.x *= nextWidth / width; node.y *= nextHeight / height; });
      width = nextWidth; height = nextHeight;
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      const count = nodeCount(width, height);
      nodes = nodes.slice(0, count);
      while (nodes.length < count) nodes.push(createNode(width, height));
      for (const [key, edge] of edges) if (edge.b >= count) edges.delete(key);
      if (pointer.active) refreshPointer();
      draw(0); start();
    }
    function move(event: PointerEvent) {
      if (!event.isPrimary || (pointerId !== null && event.pointerId !== pointerId)) return;
      touchInput = event.pointerType === 'touch';
      clientX = event.clientX; clientY = event.clientY; refreshPointer();
      if (motion.matches) draw(0);
    }
    function press(event: PointerEvent) {
      if (!event.isPrimary || event.button !== 0) return;
      move(event);
      // Links and controls retain their ordinary click/tap behavior.
      if ((event.target as Element)?.closest('a, button, input, select, textarea, [role="button"]')) return;
      pointerId = event.pointerId; pointer.held = true;
    }
    function release(event: PointerEvent) {
      if (pointerId !== null && event.pointerId !== pointerId) return;
      pointerId = null; pointer.held = false;
      if (event.pointerType !== 'mouse' || event.type === 'pointercancel') pointer.active = false;
      if (motion.matches) draw(0);
    }
    function clear() { pointer.active = false; pointer.held = false; pointerId = null; if (motion.matches) draw(0); }
    function contextMenu(event: MouseEvent) {
      if (touchInput && !(event.target as Element)?.closest('a, button, input, select, textarea, [role="button"]')) event.preventDefault();
    }
    function scroll() { if (pointer.active) { refreshPointer(); if (motion.matches) draw(0); } }
    function visibility() { stop(); clear(); start(); }
    function motionChange() { stop(); nodes.forEach(node => { node.pushX = 0; node.pushY = 0; }); draw(0); start(); }

    const observer = new ResizeObserver(resize);
    observer.observe(surface);
    host.addEventListener('pointermove', move, { passive: true });
    host.addEventListener('pointerdown', press, { passive: true });
    host.addEventListener('pointerleave', clear, { passive: true });
    host.addEventListener('contextmenu', contextMenu);
    window.addEventListener('pointerup', release, { passive: true });
    window.addEventListener('pointercancel', release, { passive: true });
    window.addEventListener('blur', clear);
    window.addEventListener('scroll', scroll, { passive: true });
    window.addEventListener('resize', resize, { passive: true });
    document.addEventListener('visibilitychange', visibility);
    motion.addEventListener('change', motionChange);
    resize();
    return () => {
      disposed = true; stop(); observer.disconnect();
      host.removeEventListener('pointermove', move); host.removeEventListener('pointerdown', press); host.removeEventListener('pointerleave', clear);
      host.removeEventListener('contextmenu', contextMenu);
      window.removeEventListener('pointerup', release); window.removeEventListener('pointercancel', release); window.removeEventListener('blur', clear);
      window.removeEventListener('scroll', scroll); window.removeEventListener('resize', resize);
      document.removeEventListener('visibilitychange', visibility); motion.removeEventListener('change', motionChange);
    };
  }, []);

  return <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden">
    <canvas ref={canvasRef} className="block h-full w-full" />
    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_35%,rgba(9,9,11,0.5),transparent_65%)]" />
  </div>;
}
