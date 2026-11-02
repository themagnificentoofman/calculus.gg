import { gameApi } from '@/lib/server/runtime-api';
export const dynamic = 'force-dynamic';
export const POST = (request: Request) => gameApi('social', request);
