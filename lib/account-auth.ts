import { createUserWithEmailAndPassword, GoogleAuthProvider, linkWithPopup, updateProfile } from 'firebase/auth';
import type { Auth } from 'firebase/auth';

type AuthAction = 'signup' | 'email-login' | 'google-login' | 'link-google';

export function authErrorMessage(error: unknown, action: AuthAction): string {
  const code = error && typeof error === 'object' && 'code' in error ? error.code : '';
  switch (code) {
    case 'auth/operation-not-allowed':
      return action === 'signup' || action === 'email-login'
        ? 'Email and password sign-in is currently unavailable. Please try Google or try again later.'
        : 'Google sign-in is currently unavailable. Please try again later.';
    case 'auth/email-already-in-use':
      return action === 'link-google'
        ? 'That Google account is already used by another Calculus Ninja account. Choose a different Google account.'
        : 'This email already has an account. Sign in with your password or Google.';
    case 'auth/credential-already-in-use':
      return 'That Google account is already used by another Calculus Ninja account. Choose a different Google account.';
    case 'auth/provider-already-linked': return 'A Google account is already linked to this account. Refresh Settings to see it.';
    case 'auth/account-exists-with-different-credential': return 'Sign in with your existing account first, then link Google in Settings → Account Security.';
    case 'auth/invalid-email': return 'Enter a valid email address.';
    case 'auth/weak-password': return 'Use a password with at least 6 characters.';
    case 'auth/password-does-not-meet-requirements': return 'This password does not meet the security requirements. Try a longer password with uppercase and lowercase letters, numbers, and symbols.';
    case 'auth/user-not-found':
    case 'auth/wrong-password':
    case 'auth/invalid-credential': return 'Invalid email or password. Please try again.';
    case 'auth/user-disabled': return 'This account has been disabled.';
    case 'auth/network-request-failed': return 'Check your internet connection and try again.';
    case 'auth/too-many-requests': return 'Too many attempts. Please wait a few minutes and try again.';
    case 'auth/popup-blocked': return 'Allow pop-ups for this site, then try Google again.';
    case 'auth/popup-closed-by-user':
    case 'auth/cancelled-popup-request': return 'The Google window was closed before finishing. Please try again.';
    case 'auth/requires-recent-login':
    case 'auth/user-token-expired': return 'Please sign out and sign in again, then retry.';
    default: return action === 'link-google'
      ? 'Google could not be linked. Please try again.'
      : action === 'signup' ? 'Your account could not be created. Please try again.' : 'Sign-in failed. Please try again.';
  }
}

export class AccountCreatedError extends Error {
  constructor() {
    super('Your account was created, but profile setup could not finish. Sign in with your new password, then check your display name in Settings.');
    this.name = 'AccountCreatedError';
  }
}

export async function createEmailAccount(auth: Auth, email: string, password: string, name: string, saveProfile: (name: string) => Promise<unknown>) {
  const displayName = name.trim();
  if (!displayName || displayName.length > 99) throw new Error('Enter a display name between 1 and 99 characters.');
  let credential;
  try {
    credential = await createUserWithEmailAndPassword(auth, email.trim(), password);
  } catch (error) {
    throw new Error(authErrorMessage(error, 'signup'));
  }
  // Authentication has succeeded. A profile outage must not imply that users
  // should create another account with the same email address.
  try {
    await updateProfile(credential.user, { displayName });
    await saveProfile(displayName);
  } catch {
    throw new AccountCreatedError();
  }
  return credential.user;
}

export async function connectGoogleAccount(auth: Auth, openPopup: typeof linkWithPopup = linkWithPopup) {
  const user = auth.currentUser;
  if (!user) throw new Error('Sign in before linking your Google account.');
  if (user.providerData.some(provider => provider.providerId === 'google.com')) return user;
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: 'select_account' });
  try {
    // Link to this UID so existing progress and email/password login survive.
    return (await openPopup(user, provider)).user;
  } catch (error) {
    throw new Error(authErrorMessage(error, 'link-google'));
  }
}
