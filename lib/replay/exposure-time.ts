/** A display is a weak preference, never an attempt. Use the earliest plausible
 * aligned time; a missing/uncertain clock falls back to the server's round time,
 * never to upload receipt. This also covers unfinished Test rounds. */
export function displayExposureTime(segment: {serverAnchorAt?: number; clockUncertain?: boolean},
  event: {monotonicMs: number}, anchorMs: number, uncertaintyMs: number,
  game: {createdAt?: unknown; finishedAt?: number}, receivedAt: number): number | null {
  const created = game.createdAt instanceof Date ? game.createdAt.getTime()
    : typeof game.createdAt === 'number' ? game.createdAt : Date.parse(String(game.createdAt));
  if (!Number.isFinite(created) || created > receivedAt) return null;
  const end = Number.isFinite(game.finishedAt) ? Math.min(receivedAt, game.finishedAt!) : receivedAt;
  if (end < created) return null;
  if (segment.clockUncertain || !Number.isFinite(segment.serverAnchorAt) ||
      !Number.isFinite(anchorMs) || anchorMs < 0 || anchorMs > 7 * 86400_000 ||
      !Number.isFinite(uncertaintyMs) || uncertaintyMs < 0 || uncertaintyMs > 60_000) return created;
  const estimate = segment.serverAnchorAt! + event.monotonicMs - anchorMs;
  if (!Number.isFinite(estimate) || estimate + uncertaintyMs < created || estimate - uncertaintyMs > end) return created;
  return Math.max(created, Math.min(end, estimate - uncertaintyMs));
}
