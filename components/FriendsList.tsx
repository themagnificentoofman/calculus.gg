/* eslint-disable @next/next/no-img-element */
'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { db } from '@/firebase';
import { collection, query, where, getDocs, doc, updateDoc, arrayUnion, arrayRemove, onSnapshot, addDoc, deleteDoc, or } from 'firebase/firestore';
import { UserPlus, UserMinus, Users, Search, X, Check, XCircle, Swords } from 'lucide-react';
import { handleFirestoreError, OperationType } from '@/lib/firestore-errors';
import { useRouter } from 'next/navigation';

interface FriendProfile {
  uid: string;
  displayName: string;
  photoURL: string;
  lastActive?: number;
}

interface FriendRequest {
  id: string;
  from: string;
  to: string;
  status: 'pending' | 'accepted' | 'rejected';
  createdAt: number;
  fromProfile?: FriendProfile;
}

interface GameInvite {
  id: string;
  from: string;
  to: string;
  gameId: string;
  status: 'pending' | 'accepted' | 'rejected';
  createdAt: number;
  fromProfile?: FriendProfile;
}

export function FriendsList() {
  const { user, profile } = useAuth();
  const router = useRouter();
  const [friends, setFriends] = useState<FriendProfile[]>([]);
  const [friendRequests, setFriendRequests] = useState<FriendRequest[]>([]);
  const [sentRequests, setSentRequests] = useState<FriendRequest[]>([]);
  const [gameInvites, setGameInvites] = useState<GameInvite[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FriendProfile[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const isOpenRef = useRef(isOpen);
  
  useEffect(() => {
    isOpenRef.current = isOpen;
  }, [isOpen]);
  const [newInvite, setNewInvite] = useState<GameInvite | null>(null);

  useEffect(() => {
    if (newInvite) {
      const timer = setTimeout(() => setNewInvite(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [newInvite]);

  useEffect(() => {
    if (!user) return;

    // Fetch friends
    const unsubscribes: (() => void)[] = [];
    const fetchFriends = async () => {
      if (!profile?.friends) {
        setFriends([]);
        return;
      }
      
      const currentFriendIds = new Set(profile.friends);
      setFriends(prev => prev.filter(f => currentFriendIds.has(f.uid)));

      for (const friendId of profile.friends) {
        const unsub = onSnapshot(doc(db, 'users', friendId), (docSnap) => {
          if (docSnap.exists()) {
            const data = docSnap.data();
            setFriends(prev => {
              const existing = prev.filter(f => f.uid !== friendId);
              return [...existing, {
                uid: friendId,
                displayName: data.displayName || 'Unknown',
                photoURL: data.photoURL || '',
                lastActive: data.lastActive
              }].sort((a, b) => a.displayName.localeCompare(b.displayName));
            });
          }
        }, (error) => handleFirestoreError(error, OperationType.GET, `users/${friendId}`));
        unsubscribes.push(unsub);
      }
    };

    fetchFriends();

    // Fetch pending friend requests
    const requestsQuery = query(
      collection(db, 'friendRequests'),
      where('to', '==', user.uid),
      where('status', '==', 'pending')
    );

    const unsubRequests = onSnapshot(requestsQuery, async (snapshot) => {
      const requests: FriendRequest[] = [];
      for (const docSnap of snapshot.docs) {
        const data = docSnap.data() as Omit<FriendRequest, 'id'>;
        
        // Fetch profile of the sender
        try {
          const senderDoc = await getDocs(query(collection(db, 'users'), where('__name__', '==', data.from)));
          let fromProfile: FriendProfile | undefined;
          if (!senderDoc.empty) {
            const senderData = senderDoc.docs[0].data();
            fromProfile = {
              uid: data.from,
              displayName: senderData.displayName || 'Unknown',
              photoURL: senderData.photoURL || '',
            };
          }
          
          requests.push({
            id: docSnap.id,
            ...data,
            fromProfile
          });
        } catch (error) {
          console.error("Failed to fetch sender profile", error);
        }
      }
      setFriendRequests(requests);
    }, (error) => handleFirestoreError(error, OperationType.LIST, 'friendRequests'));

    // Fetch sent friend requests
    const sentRequestsQuery = query(
      collection(db, 'friendRequests'),
      where('from', '==', user.uid),
      where('status', '==', 'pending')
    );

    const unsubSentRequests = onSnapshot(sentRequestsQuery, (snapshot) => {
      const requests: FriendRequest[] = [];
      snapshot.forEach((docSnap) => {
        requests.push({ id: docSnap.id, ...docSnap.data() } as FriendRequest);
      });
      setSentRequests(requests);
    }, (error) => handleFirestoreError(error, OperationType.LIST, 'friendRequests'));

    // Fetch pending game invites
    const invitesQuery = query(
      collection(db, 'gameInvites'),
      where('to', '==', user.uid),
      where('status', '==', 'pending')
    );

    const unsubInvites = onSnapshot(invitesQuery, async (snapshot) => {
      const invites: GameInvite[] = [];
      let addedInvite: GameInvite | null = null;
      for (const change of snapshot.docChanges()) {
        if (change.type === 'added') {
          const data = change.doc.data() as Omit<GameInvite, 'id'>;
          try {
            const senderDoc = await getDocs(query(collection(db, 'users'), where('__name__', '==', data.from)));
            let fromProfile: FriendProfile | undefined;
            if (!senderDoc.empty) {
              const senderData = senderDoc.docs[0].data();
              fromProfile = {
                uid: data.from,
                displayName: senderData.displayName || 'Unknown',
                photoURL: senderData.photoURL || '',
              };
            }
            addedInvite = { id: change.doc.id, ...data, fromProfile };
          } catch (error) {
            console.error("Failed to fetch sender profile", error);
          }
        }
      }

      for (const docSnap of snapshot.docs) {
        const data = docSnap.data() as Omit<GameInvite, 'id'>;
        
        try {
          const senderDoc = await getDocs(query(collection(db, 'users'), where('__name__', '==', data.from)));
          let fromProfile: FriendProfile | undefined;
          if (!senderDoc.empty) {
            const senderData = senderDoc.docs[0].data();
            fromProfile = {
              uid: data.from,
              displayName: senderData.displayName || 'Unknown',
              photoURL: senderData.photoURL || '',
            };
          }
          
          invites.push({
            id: docSnap.id,
            ...data,
            fromProfile
          });
        } catch (error) {
          console.error("Failed to fetch sender profile", error);
        }
      }
      setGameInvites(invites);
      if (addedInvite && !isOpenRef.current) {
        setNewInvite(addedInvite);
      }
    }, (error) => handleFirestoreError(error, OperationType.LIST, 'gameInvites'));

    return () => {
      unsubscribes.forEach(unsub => unsub());
      unsubRequests();
      unsubSentRequests();
      unsubInvites();
    };
  }, [user, profile?.friends]);

  const handleSearch = async () => {
    if (!searchQuery.trim() || !user) return;
    setIsSearching(true);
    try {
      const usersRef = collection(db, 'users');
      // Query by displayName or handle
      const q = query(
        usersRef, 
        or(
          where('displayName', '>=', searchQuery),
          where('handle', '>=', searchQuery)
        )
      );
      const querySnapshot = await getDocs(q);
      
      const results: FriendProfile[] = [];
      querySnapshot.forEach((doc) => {
        if (doc.id !== user.uid) {
          const data = doc.data();
          // Client-side filter to ensure it matches either displayName or handle
          const matchesName = data.displayName?.toLowerCase().includes(searchQuery.toLowerCase());
          const matchesHandle = data.handle?.toLowerCase().includes(searchQuery.toLowerCase());
          
          if (matchesName || matchesHandle) {
            results.push({
              uid: doc.id,
              displayName: data.displayName || 'Unknown',
              photoURL: data.photoURL || '',
            });
          }
        }
      });
      setSearchResults(results);
    } catch (error) {
      handleFirestoreError(error, OperationType.LIST, 'users');
    } finally {
      setIsSearching(false);
    }
  };

  const sendFriendRequest = async (friendId: string) => {
    if (!user) return;
    try {
      await addDoc(collection(db, 'friendRequests'), {
        from: user.uid,
        to: friendId,
        status: 'pending',
        createdAt: Date.now()
      });
      // Optionally show a success toast here
      setSearchQuery('');
      setSearchResults([]);
    } catch (error) {
      handleFirestoreError(error, OperationType.CREATE, 'friendRequests');
    }
  };

  const acceptRequest = async (request: FriendRequest) => {
    if (!user) return;
    try {
      // Update request status
      await updateDoc(doc(db, 'friendRequests', request.id), {
        status: 'accepted'
      });
      
      // Add to each other's friends list
      await updateDoc(doc(db, 'users', user.uid), {
        friends: arrayUnion(request.from)
      });
      await updateDoc(doc(db, 'users', request.from), {
        friends: arrayUnion(user.uid)
      });
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `friendRequests/${request.id}`);
    }
  };

  const rejectRequest = async (requestId: string) => {
    try {
      await updateDoc(doc(db, 'friendRequests', requestId), {
        status: 'rejected'
      });
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `friendRequests/${requestId}`);
    }
  };

  const cancelRequest = async (requestId: string) => {
    try {
      await deleteDoc(doc(db, 'friendRequests', requestId));
    } catch (error) {
      handleFirestoreError(error, OperationType.DELETE, `friendRequests/${requestId}`);
    }
  };

  const acceptInvite = async (invite: GameInvite) => {
    try {
      await updateDoc(doc(db, 'gameInvites', invite.id), {
        status: 'accepted'
      });
      setIsOpen(false);
      router.push(`/play/pvp?join=${invite.gameId}`);
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `gameInvites/${invite.id}`);
    }
  };

  const rejectInvite = async (inviteId: string) => {
    try {
      await updateDoc(doc(db, 'gameInvites', inviteId), {
        status: 'rejected'
      });
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `gameInvites/${inviteId}`);
    }
  };

  const removeFriend = async (friendId: string) => {
    if (!user) return;
    try {
      await updateDoc(doc(db, 'users', user.uid), {
        friends: arrayRemove(friendId)
      });
      await updateDoc(doc(db, 'users', friendId), {
        friends: arrayRemove(user.uid)
      });
      setFriends(prev => prev.filter(f => f.uid !== friendId));
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`);
    }
  };

  const inviteToGame = (friendId: string) => {
    setIsOpen(false);
    router.push(`/play/pvp?invite=${friendId}`);
  };

  const isOnline = (lastActive?: number) => {
    if (!lastActive) return false;
    return (Date.now() - lastActive) < 5 * 60 * 1000;
  };

  if (!user) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-4">
      {newInvite && !isOpen && (
        <div className="bg-indigo-600 text-white p-4 rounded-2xl shadow-xl flex items-center gap-4 animate-in slide-in-from-bottom-5 fade-in duration-300">
          <img src={newInvite.fromProfile?.photoURL || `https://api.dicebear.com/7.x/avataaars/svg?seed=${newInvite.from}`} alt="Profile" className="w-10 h-10 rounded-full bg-indigo-800" />
          <div className="flex flex-col">
            <span className="font-bold">{newInvite.fromProfile?.displayName || 'Someone'}</span>
            <span className="text-sm text-indigo-200">Invited you to play!</span>
          </div>
          <div className="flex gap-2 ml-2">
            <button onClick={() => { acceptInvite(newInvite); setNewInvite(null); }} className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors">
              <Check className="w-4 h-4" />
            </button>
            <button onClick={() => { rejectInvite(newInvite.id); setNewInvite(null); }} className="p-2 bg-black/20 hover:bg-black/30 rounded-lg transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
      {isOpen ? (
        <div className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-zinc-200 rounded-2xl shadow-2xl w-80 sm:w-96 overflow-hidden flex flex-col h-[32rem]">
          <div className="p-4 border-b dark:border-zinc-800 border-zinc-200 flex justify-between items-center dark:bg-zinc-950 bg-zinc-50">
            <h3 className="font-bold flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-500" />
              Friends
            </h3>
            <button onClick={() => setIsOpen(false)} className="dark:text-zinc-400 text-zinc-500 dark:hover:text-white hover:text-zinc-900 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-4 border-b dark:border-zinc-800 border-zinc-200 dark:bg-zinc-900 bg-white/50">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Search users by name or handle..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 dark:bg-zinc-950 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
              />
              <button
                onClick={handleSearch}
                disabled={isSearching}
                className="bg-indigo-600 hover:bg-indigo-500 text-white p-2 rounded-lg transition-colors disabled:opacity-50"
              >
                <Search className="w-4 h-4" />
              </button>
            </div>
            {searchQuery && (
              <button 
                onClick={() => { setSearchQuery(''); setSearchResults([]); }}
                className="text-xs dark:text-zinc-500 text-zinc-400 dark:hover:text-zinc-300 hover:text-zinc-600 mt-2 transition-colors"
              >
                Clear search
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-6">
            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="space-y-2">
                <div className="px-2 text-xs font-bold dark:text-zinc-500 text-zinc-400 uppercase tracking-wider">Search Results</div>
                {searchResults.map(result => {
                  const isFriend = profile?.friends?.includes(result.uid);
                  const sentReq = sentRequests.find(r => r.to === result.uid);
                  const receivedReq = friendRequests.find(r => r.from === result.uid);
                  
                  return (
                  <div key={result.uid} className="flex items-center justify-between p-3 dark:bg-zinc-950 bg-zinc-50/50 border dark:border-zinc-800 border-zinc-200/50 rounded-xl hover:dark:border-zinc-700 border-zinc-300 transition-colors">
                    <div className="flex items-center gap-3">
                      <img src={result.photoURL || `https://api.dicebear.com/7.x/avataaars/svg?seed=${result.uid}`} alt={result.displayName} className="w-10 h-10 rounded-full dark:bg-zinc-800 bg-zinc-200" />
                      <span className="text-sm font-medium">{result.displayName}</span>
                    </div>
                    {isFriend ? (
                      <span className="text-xs dark:text-zinc-500 text-zinc-400 px-2">Friend</span>
                    ) : sentReq ? (
                      <button 
                        onClick={() => cancelRequest(sentReq.id)}
                        className="text-xs dark:text-zinc-500 text-zinc-400 hover:text-red-400 px-2 transition-colors"
                      >
                        Cancel Request
                      </button>
                    ) : receivedReq ? (
                      <div className="flex items-center gap-1">
                        <button 
                          onClick={() => acceptRequest(receivedReq)} 
                          className="p-1.5 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-white rounded-lg transition-colors"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <button 
                        onClick={() => sendFriendRequest(result.uid)} 
                        className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600 hover:text-white rounded-lg text-xs font-bold transition-colors"
                      >
                        <UserPlus className="w-3.5 h-3.5" /> Add
                      </button>
                    )}
                  </div>
                )})}
              </div>
            )}

            {/* Pending Requests */}
            {!searchQuery && friendRequests.length > 0 && (
              <div className="space-y-2">
                <div className="px-2 text-xs font-bold text-amber-500 uppercase tracking-wider">Pending Requests</div>
                {friendRequests.map(request => (
                  <div key={request.id} className="flex items-center justify-between p-3 bg-amber-500/5 border border-amber-500/20 rounded-xl">
                    <div className="flex items-center gap-3">
                      <img src={request.fromProfile?.photoURL || `https://api.dicebear.com/7.x/avataaars/svg?seed=${request.from}`} alt={request.fromProfile?.displayName || 'Unknown'} className="w-10 h-10 rounded-full dark:bg-zinc-800 bg-zinc-200" />
                      <span className="text-sm font-medium">{request.fromProfile?.displayName || 'Unknown'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <button 
                        onClick={() => acceptRequest(request)} 
                        className="p-1.5 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-white rounded-lg transition-colors"
                        title="Accept"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => rejectRequest(request.id)} 
                        className="p-1.5 bg-red-500/20 text-red-400 hover:bg-red-500 hover:text-white rounded-lg transition-colors"
                        title="Reject"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Game Invites */}
            {!searchQuery && gameInvites.length > 0 && (
              <div className="space-y-2">
                <div className="px-2 text-xs font-bold text-indigo-500 uppercase tracking-wider">Game Invites</div>
                {gameInvites.map(invite => (
                  <div key={invite.id} className="flex items-center justify-between p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-xl">
                    <div className="flex items-center gap-3">
                      <img src={invite.fromProfile?.photoURL || `https://api.dicebear.com/7.x/avataaars/svg?seed=${invite.from}`} alt={invite.fromProfile?.displayName || 'Unknown'} className="w-10 h-10 rounded-full dark:bg-zinc-800 bg-zinc-200" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium">{invite.fromProfile?.displayName || 'Unknown'}</span>
                        <span className="text-xs text-indigo-400">Invited you to play</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button 
                        onClick={() => acceptInvite(invite)} 
                        className="p-1.5 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-white rounded-lg transition-colors"
                        title="Accept"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => rejectInvite(invite.id)} 
                        className="p-1.5 bg-red-500/20 text-red-400 hover:bg-red-500 hover:text-white rounded-lg transition-colors"
                        title="Reject"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Friends List */}
            {!searchQuery && (
              <div className="space-y-2">
                <div className="px-2 text-xs font-bold dark:text-zinc-500 text-zinc-400 uppercase tracking-wider">Your Friends</div>
                {friends.length === 0 ? (
                  <div className="p-6 text-center text-sm dark:text-zinc-500 text-zinc-400 dark:bg-zinc-950 bg-zinc-50/30 rounded-xl border dark:border-zinc-800 border-zinc-200/30 dashed">
                    No friends yet. Search for users to add them!
                  </div>
                ) : (
                  friends.map(friend => {
                    const hasInvite = gameInvites.some(i => i.from === friend.uid);
                    return (
                    <div key={friend.uid} className="flex items-center justify-between p-3 dark:bg-zinc-950 bg-zinc-50/50 border dark:border-zinc-800 border-zinc-200/50 rounded-xl hover:dark:bg-zinc-900 bg-white/80 hover:dark:border-zinc-600 border-zinc-400 transition-colors group">
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <img src={friend.photoURL || `https://api.dicebear.com/7.x/avataaars/svg?seed=${friend.uid}`} alt={friend.displayName} className="w-10 h-10 rounded-full dark:bg-zinc-800 bg-zinc-200" />
                          {isOnline(friend.lastActive) ? (
                            <div className="w-3.5 h-3.5 absolute -bottom-0.5 -right-0.5 bg-green-500 rounded-full border-2 border-zinc-900" />
                          ) : (
                            <div className="w-3.5 h-3.5 absolute -bottom-0.5 -right-0.5 dark:bg-zinc-900 bg-white border-2 border-zinc-500 rounded-full" />
                          )}
                        </div>
                        <div className="flex flex-col">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium dark:text-zinc-200 text-zinc-800">{friend.displayName}</span>
                            {hasInvite && <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" title="Sent you an invite" />}
                          </div>
                          <span className="text-xs dark:text-zinc-500 text-zinc-400">{isOnline(friend.lastActive) ? 'Online' : 'Offline'}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          onClick={() => inviteToGame(friend.uid)} 
                          className="flex items-center gap-1 px-2 py-1.5 text-xs font-medium text-indigo-400 hover:text-white hover:bg-indigo-600 rounded-lg transition-colors"
                          title="Challenge to PvP"
                        >
                          <Swords className="w-3.5 h-3.5" /> Challenge
                        </button>
                        <button 
                          onClick={() => removeFriend(friend.uid)} 
                          className="p-1.5 text-zinc-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                          title="Remove Friend"
                        >
                          <UserMinus className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  )})
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white p-4 rounded-full shadow-lg shadow-indigo-500/20 transition-transform hover:scale-105 flex items-center justify-center relative"
        >
          <Users className="w-6 h-6" />
          {friendRequests.length > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full border-2 border-zinc-900" />
          )}
        </button>
      )}
    </div>
  );
}
