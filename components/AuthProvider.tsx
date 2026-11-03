'use client';

import {usePathname} from 'next/navigation';
import React, { createContext, useContext, useEffect, useState } from 'react';
import { auth, db } from '@/firebase';
import { onAuthStateChanged, User, signInWithPopup, GoogleAuthProvider, signOut, createUserWithEmailAndPassword, signInWithEmailAndPassword, linkWithPopup, updateProfile as updateAuthProfile } from 'firebase/auth';
import { doc, onSnapshot } from 'firebase/firestore';
import { apiRequest, gameProgress } from '@/lib/game-session';
import { OperationType, handleFirestoreError } from '@/lib/firestore-errors';

interface UserProfile {
  uid: string;
  displayName: string;
  handle?: string;
  photoURL?: string;
  email: string;
  rating: number;
  classification: string;
  gamesPlayed: number;
  wins: number;
  losses: number;
  draws?: number;
  ratedGames?: number;
  topicRatedGames?: Record<string, number>;
  answeredQuestions?: number;
  correctAnswers?: number;
  createdAt: string;
  xp?: number;
  topicXp?: Record<string, number>;
  topicRatings?: Record<string, number>;
  settings?: {
    theme?: string;
    notifications?: boolean;
    soundEnabled?: boolean;
  };
  friends?: string[];
  lastActive?: number;
  color?: string;
}

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  loading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  updateUserProfile: (data: Partial<UserProfile>) => Promise<void>;
  signupWithEmail: (email: string, pass: string, name: string) => Promise<void>;
  loginWithEmail: (email: string, pass: string) => Promise<void>;
  linkGoogleAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
  updateUserProfile: async () => {},
  signupWithEmail: async () => {},
  loginWithEmail: async () => {},
  linkGoogleAccount: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const readOnlyReplay=usePathname().startsWith('/replay/');
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [profileError, setProfileError] = useState('');
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let revision = 0;
    let stopProfile = () => {};
    let stopResults = () => {};
    const unsubscribe = onAuthStateChanged(auth, async firebaseUser => {
      const current = ++revision;
      stopProfile(); stopResults();
      setUser(firebaseUser); setProfile(null); setLoading(true); setProfileError('');
      if (!firebaseUser) { setLoading(false); return; }
      const userRef = doc(db, 'users', firebaseUser.uid);
      try {
        if(!readOnlyReplay) await apiRequest('profile', {});
        if (current !== revision) return;
        // Keep XP/rating live; never delete or subtract legacy earned progress.
        stopProfile = onSnapshot(userRef, snapshot => {
          if (current !== revision) return;
          if (snapshot.exists()) setProfile(snapshot.data() as UserProfile);
          setLoading(false);
        }, error => { if (current === revision) { setProfileError('Your profile could not be refreshed.'); setLoading(false); } });
        if(!readOnlyReplay) stopResults = gameProgress.watchPendingResults(firebaseUser.uid, error => console.error('Pending result sync failed', error));
      } catch (error) {
        console.error('Profile setup failed', error);
        if (current === revision) { setLoading(false); setProfileError('Your profile could not be loaded.'); }
      }
    });
    return () => { revision++; unsubscribe(); stopProfile(); stopResults(); };
  }, [retry,readOnlyReplay]);

  useEffect(() => {
    if (readOnlyReplay || !user || profile?.uid !== user.uid) return;

    const updateLastActive = async () => {
      try {
        await apiRequest('profile', {});
      } catch (error) {
        // Silently fail for lastActive updates to not spam errors
        console.error('Failed to update lastActive', error);
      }
    };

    // Update immediately on mount/login
    updateLastActive();

    // Update every minute
    const interval = setInterval(updateLastActive, 60000);

    return () => clearInterval(interval);
  }, [user, profile?.uid,readOnlyReplay]);

  useEffect(() => {
    try { localStorage.setItem('soundEnabled', String(profile?.settings?.soundEnabled !== false)); } catch {}
  }, [profile?.settings?.soundEnabled, user?.uid]);

  const login = async () => {
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error('Login failed', error);
      throw new Error('Google sign-in failed. Please try again or use email sign-in.');
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      console.error('Logout failed', error);
    }
  };

  const signupWithEmail = async (email: string, pass: string, name: string) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, pass);
      await updateAuthProfile(userCredential.user, { displayName: name });
      
      await apiRequest('profile', { patch: { displayName: name } });
    } catch (error: any) {
      console.error('Signup failed', error);
      let errorMessage = 'An error occurred during signup.';
      if (error.code === 'auth/email-already-in-use') {
        errorMessage = 'This email is already in use.';
      } else if (error.code === 'auth/invalid-email') {
        errorMessage = 'Invalid email address.';
      } else if (error.code === 'auth/weak-password') {
        errorMessage = 'Password is too weak. It must be at least 6 characters.';
      }
      throw new Error(errorMessage);
    }
  };

  const loginWithEmail = async (email: string, pass: string) => {
    try {
      await signInWithEmailAndPassword(auth, email, pass);
    } catch (error: any) {
      console.error('Login failed', error);
      let errorMessage = 'An error occurred during login.';
      if (error.code === 'auth/user-not-found' || error.code === 'auth/invalid-credential') {
        errorMessage = 'Invalid email or password.';
      } else if (error.code === 'auth/wrong-password') {
        errorMessage = 'Invalid email or password.';
      } else if (error.code === 'auth/invalid-email') {
        errorMessage = 'Invalid email address.';
      } else if (error.code === 'auth/user-disabled') {
        errorMessage = 'This account has been disabled.';
      }
      throw new Error(errorMessage);
    }
  };

  const linkGoogleAccount = async () => {
    if (!user) return;
    const provider = new GoogleAuthProvider();
    try {
      await linkWithPopup(user, provider);
    } catch (error) {
      console.error('Link Google failed', error);
      throw error;
    }
  };

  const updateUserProfile = async (data: Partial<UserProfile>) => {
    if (!user || !profile) return;
    try {
      const userRef = doc(db, 'users', user.uid);
      try {
        await apiRequest('profile', { patch: data });
      } catch (error) {
        handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`);
      }
      setProfile(current => current ? { ...current, ...data } : current);
      
      if (data.displayName !== undefined || data.photoURL !== undefined) {
        const authUpdates: { displayName?: string; photoURL?: string } = {};
        if (data.displayName !== undefined) authUpdates.displayName = data.displayName;
        if (data.photoURL !== undefined && data.photoURL.length < 2000) authUpdates.photoURL = data.photoURL;
        
        if (Object.keys(authUpdates).length > 0) {
          await updateAuthProfile(user, authUpdates);
        }
      }
    } catch (error) {
      console.error('Update profile failed', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, profile, loading, login, logout, updateUserProfile, signupWithEmail, loginWithEmail, linkGoogleAccount }}>
      {profileError && <div role="alert" className="border-b border-red-500/30 bg-red-950 px-4 py-3 text-center text-sm text-red-100">{profileError} <button onClick={() => setRetry(value => value + 1)} className="ml-3 min-h-11 rounded-lg px-3 font-bold underline">Retry</button></div>}
      {children}
    </AuthContext.Provider>
  );
}
