'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { db } from '@/firebase';
import { doc, updateDoc, arrayUnion, onSnapshot } from 'firebase/firestore';
import { Send, MessageSquare } from 'lucide-react';
import { handleFirestoreError, OperationType } from '@/lib/firestore-errors';

interface ChatMessage {
  senderId: string;
  senderName: string;
  text: string;
  timestamp: number;
}

interface ChatProps {
  gameId: string;
  messages: ChatMessage[];
}

export function Chat({ gameId, messages }: ChatProps) {
  const { user, profile } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !user) return;

    const message: ChatMessage = {
      senderId: user.uid,
      senderName: profile?.displayName || 'Player',
      text: newMessage.trim(),
      timestamp: Date.now()
    };

    setNewMessage('');

    try {
      await updateDoc(doc(db, 'games', gameId), {
        messages: arrayUnion(message)
      });
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `games/${gameId}`);
    }
  };

  return (
    <div className="fixed bottom-4 left-4 z-40">
      {isOpen ? (
        <div className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-zinc-200 rounded-2xl shadow-2xl w-80 flex flex-col h-96 overflow-hidden">
          <div className="p-3 border-b dark:border-zinc-800 border-zinc-200 flex justify-between items-center dark:bg-zinc-950 bg-zinc-50">
            <h3 className="font-bold flex items-center gap-2 text-sm dark:text-white text-zinc-900">
              <MessageSquare className="w-4 h-4 text-indigo-500" />
              Game Chat
            </h3>
            <button onClick={() => setIsOpen(false)} className="dark:text-zinc-400 text-zinc-500 dark:hover:text-white hover:text-zinc-900 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-xs dark:text-zinc-500 text-zinc-400 mt-4">No messages yet. Say hi!</div>
            ) : (
              messages.map((msg, idx) => {
                const isMe = msg.senderId === user?.uid;
                const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                return (
                  <div key={idx} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}>
                    <div className={`flex items-baseline gap-2 mb-1 px-1 ${isMe ? 'flex-row-reverse' : 'flex-row'}`}>
                      <span className="text-xs font-medium dark:text-zinc-400 text-zinc-500">{isMe ? 'You' : msg.senderName}</span>
                      <span className="text-[10px] dark:text-zinc-600 text-zinc-400">{time}</span>
                    </div>
                    <div className={`px-3 py-2.5 rounded-2xl text-sm max-w-[85%] break-words whitespace-pre-wrap leading-relaxed shadow-sm ${isMe ? 'bg-indigo-600 text-white rounded-tr-sm' : 'dark:bg-zinc-800 bg-zinc-100 dark:text-zinc-200 text-zinc-800 rounded-tl-sm'}`}>
                      {msg.text}
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={sendMessage} className="p-3 border-t dark:border-zinc-800 border-zinc-200 dark:bg-zinc-950 bg-zinc-50 flex gap-2">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 dark:text-white text-zinc-900 transition-colors"
              maxLength={100}
            />
            <button
              type="submit"
              disabled={!newMessage.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white p-2 rounded-lg transition-colors flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="dark:bg-zinc-800 bg-white dark:hover:bg-zinc-700 hover:bg-zinc-50 dark:text-white text-zinc-900 p-3 rounded-full shadow-lg transition-transform hover:scale-105 flex items-center justify-center relative border dark:border-zinc-700 border-zinc-200"
        >
          <MessageSquare className="w-5 h-5" />
          {messages.length > 0 && (
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-indigo-500 rounded-full border-2 dark:border-zinc-900 border-white" />
          )}
        </button>
      )}
    </div>
  );
}
