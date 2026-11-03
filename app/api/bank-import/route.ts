export const dynamic = 'force-dynamic';
// Milestone 1 is complete. No credential or request can reopen this endpoint.
// Operator source and immutable receipts remain available for audited recovery.
export function POST() {
  return Response.json({error: 'Unavailable'}, {status: 404, headers: {'Cache-Control': 'no-store'}});
}
