import type { Store, Data } from './firestore-admin.ts';
import { GameError, identifier, lobbyExpired } from './game-engine.ts';
export async function socialAction(store: Store, uid: string, action: string, input: Data, now = Date.now()) {
  const other = input.to || input.friendId;
  if (other) { identifier(other); if (other === uid) throw new GameError('Choose another player.'); }
  if (input.id) identifier(input.id);
  return store.transaction(async tx => {
    if (action === 'request') {
      const id = `${uid}_${other}`;
      const [me, target, existing, reverse] = await Promise.all([tx.get(`users/${uid}`), tx.get(`users/${other}`), tx.get(`friendRequests/${id}`), tx.get(`friendRequests/${other}_${uid}`)]);
      if (!me || !target) throw new GameError('Player not found.', 404);
      if (me.friends?.includes(other) || existing?.status === 'pending') return {};
      if (reverse?.status === 'pending') throw new GameError('This player has already sent you a request. Accept it in Friends.', 409);
      if ((me.friends || []).length >= 100 || (target.friends || []).length >= 100) throw new GameError('Friend limit reached.');
      if (me.lastFriendRequest && now - me.lastFriendRequest < 2000) throw new GameError('Please wait before sending another request.', 429);
      tx.set(`friendRequests/${id}`, { from: uid, to: other, status: 'pending', createdAt: new Date(now) });
      tx.set(`users/${uid}`, { ...me, lastFriendRequest: now }); return { id };
    }
    if (action === 'remove') {
      const [me, target] = await Promise.all([tx.get(`users/${uid}`), tx.get(`users/${other}`)]);
      if (!me || !target) throw new GameError('Player not found.', 404);
      if (!me.friends?.includes(other) && !target.friends?.includes(uid)) return {};
      tx.delete(`friendRequests/${uid}_${other}`); tx.delete(`friendRequests/${other}_${uid}`);
      tx.set(`users/${uid}`, { ...me, friends: (me.friends || []).filter((p: string) => p !== other) });
      tx.set(`users/${other}`, { ...target, friends: (target.friends || []).filter((p: string) => p !== uid) }); return {};
    }
    if (action === 'invite') {
      const gameId = identifier(input.gameId), id = `${gameId}_${other}`;
      const [game, me, target, existing] = await Promise.all([tx.get(`games/${gameId}`), tx.get(`users/${uid}`), tx.get(`users/${other}`), tx.get(`gameInvites/${id}`)]);
      if (!game || !me || !target || !game.players.includes(uid) || game.status !== 'waiting' || !['pvp', 'multiplayer'].includes(game.mode) || !me.friends?.includes(other) || !target.friends?.includes(uid)) throw new GameError('This invitation is not allowed.', 403);
      if (lobbyExpired(game as any, now) || game.players.includes(other) || game.players.length >= (game.mode === 'pvp' ? 2 : 10)) throw new GameError('This lobby is no longer available.', 409);
      if (existing?.status === 'pending') return { id };
      if (me.lastGameInvite && now - me.lastGameInvite < 2000) throw new GameError('Please wait before sending another invitation.', 429);
      tx.set(`users/${uid}`, { ...me, lastGameInvite: now });
      tx.set(`gameInvites/${id}`, { from: uid, to: other, gameId, mode: game.mode, status: 'pending', createdAt: new Date(now) }); return { id };
    }
    const invite = action.startsWith('invite_'), collection = invite ? 'gameInvites' : 'friendRequests';
    const path = `${collection}/${identifier(input.id)}`, record = await tx.get(path);
    if (!record || ![record.from, record.to].includes(uid)) throw new GameError('Request not found.', 404);
    if (action === 'cancel') { if (record.from !== uid) throw new GameError('Only the sender can cancel.', 403); tx.delete(path); return {}; }
    if (record.to !== uid) throw new GameError('Only the recipient can respond.', 403);
    if (!['accept', 'reject', 'invite_accept', 'invite_reject'].includes(action)) throw new GameError('Invalid request action.');
    if (record.status !== 'pending') return record;
    if (action === 'accept') {
      const [from, to] = await Promise.all([tx.get(`users/${record.from}`), tx.get(`users/${record.to}`)]);
      if (!from || !to || (from.friends || []).length >= 100 || (to.friends || []).length >= 100) throw new GameError('Friend limit reached.');
      tx.delete(`friendRequests/${record.to}_${record.from}`);
      tx.set(`users/${record.from}`, { ...from, friends: [...new Set([...(from.friends || []), record.to])] });
      tx.set(`users/${record.to}`, { ...to, friends: [...new Set([...(to.friends || []), record.from])] });
    }
    const status = action.endsWith('accept') ? 'accepted' : 'rejected';
    tx.set(path, { ...record, status }); return { ...record, status };
  });
}
