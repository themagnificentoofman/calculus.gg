'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { auth, db } from '@/firebase';
import { onAuthStateChanged, User, signInWithPopup, GoogleAuthProvider, signOut, createUserWithEmailAndPassword, signInWithEmailAndPassword, linkWithPopup, updateProfile as updateAuthProfile } from 'firebase/auth';
import { doc, getDoc, setDoc, updateDoc } from 'firebase/firestore';
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
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        // Fetch or create user profile
        const userRef = doc(db, 'users', firebaseUser.uid);
        let userSnap;
        try {
          userSnap = await getDoc(userRef);
        } catch (error) {
          handleFirestoreError(error, OperationType.GET, `users/${firebaseUser.uid}`);
          return;
        }
        
        if (userSnap.exists()) {
          const data = userSnap.data() as UserProfile;
          
          // Reset 'All' topic XP if it exists
          if (data.topicXp && (data.topicXp['All'] !== undefined || data.topicXp['all'] !== undefined)) {
            const allXp = (data.topicXp['All'] || 0) + (data.topicXp['all'] || 0);
            const newXp = Math.max(0, (data.xp || 0) - allXp);
            
            const newTopicXp = { ...data.topicXp };
            delete newTopicXp['All'];
            delete newTopicXp['all'];
            
            const newTopicRatings = { ...data.topicRatings };
            if (newTopicRatings) {
              delete newTopicRatings['All'];
              delete newTopicRatings['all'];
            }
            
            try {
              await updateDoc(userRef, {
                xp: newXp,
                topicXp: newTopicXp,
                topicRatings: newTopicRatings || {}
              });
              data.xp = newXp;
              data.topicXp = newTopicXp;
              data.topicRatings = newTopicRatings;
            } catch (error) {
              console.error('Failed to reset All topic XP', error);
            }
          }
          
          setProfile(data);
        } else {
          const newProfile: UserProfile = {
            uid: firebaseUser.uid,
            displayName: firebaseUser.displayName || 'Anonymous Calc Bro',
            handle: `user${firebaseUser.uid.substring(0, 6)}`,
            photoURL: firebaseUser.photoURL || '',
            email: firebaseUser.email || '',
            rating: 0,
            classification: 'Novice',
            gamesPlayed: 0,
            wins: 0,
            losses: 0,
            createdAt: new Date().toISOString(),
            xp: 0,
            topicXp: { integration: 0, differentiation: 0, limits: 0 },
            topicRatings: { integration: 0, differentiation: 0, limits: 0 },
            settings: {
              theme: 'dark',
              notifications: true,
              soundEnabled: true
            },
            friends: [],
            lastActive: Date.now()
          };
          try {
            await setDoc(userRef, newProfile);
          } catch (error) {
            handleFirestoreError(error, OperationType.CREATE, `users/${firebaseUser.uid}`);
          }
          setProfile(newProfile);
        }
      } else {
        setProfile(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (!user) return;

    const updateLastActive = async () => {
      try {
        await updateDoc(doc(db, 'users', user.uid), {
          lastActive: Date.now()
        });
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
  }, [user]);

  const login = async () => {
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error('Login failed', error);
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
      
      // Update the firestore document if it was already created by onAuthStateChanged
      const userRef = doc(db, 'users', userCredential.user.uid);
      let userSnap;
      try {
        userSnap = await getDoc(userRef);
      } catch (error) {
        handleFirestoreError(error, OperationType.GET, `users/${userCredential.user.uid}`);
        return;
      }
      
      if (userSnap.exists()) {
        try {
          await updateDoc(userRef, { displayName: name });
        } catch (error) {
          handleFirestoreError(error, OperationType.UPDATE, `users/${userCredential.user.uid}`);
        }
        if (profile && profile.uid === userCredential.user.uid) {
          setProfile({ ...profile, displayName: name });
        }
      }
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
        await updateDoc(userRef, data);
      } catch (error) {
        handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`);
      }
      setProfile({ ...profile, ...data });
      
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
      {children}
    </AuthContext.Provider>
  );
}
