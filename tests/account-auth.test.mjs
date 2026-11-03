import test from 'node:test';
import assert from 'node:assert/strict';
import { initializeApp, deleteApp } from 'firebase/app';
import { getAuth, connectAuthEmulator, signOut, signInWithEmailAndPassword, signInWithCredential, linkWithCredential, GoogleAuthProvider } from 'firebase/auth';
import { AccountCreatedError, authErrorMessage, createEmailAccount, connectGoogleAccount } from '../lib/account-auth.ts';

test('disabled email provider and popup errors have actionable messages without SDK details', () => {
  assert.match(authErrorMessage({ code: 'auth/operation-not-allowed' }, 'signup'), /Email and password.*unavailable/);
  assert.match(authErrorMessage({ code: 'auth/popup-blocked' }, 'link-google'), /Allow pop-ups/);
  assert.match(authErrorMessage({ code: 'auth/network-request-failed' }, 'signup'), /internet connection/);
  assert.equal(authErrorMessage(new Error('internal diagnostic'), 'signup').includes('internal diagnostic'), false);
});

test('invalid display names fail before an account can be created', async () => {
  for (const name of ['   ', 'x'.repeat(100)]) {
    await assert.rejects(createEmailAccount(null, 'test@example.test', 'password', name, () => assert.fail('profile must not be saved')), /display name/);
  }
});

test('Google linking requires sign-in and never substitutes another account on a conflict', async () => {
  await assert.rejects(connectGoogleAccount({ currentUser: null }), /Sign in before linking/);
  const user = { uid: 'existing-progress-owner', providerData: [{ providerId: 'password' }] };
  const auth = { currentUser: user };
  await assert.rejects(connectGoogleAccount(auth, async (target, provider) => {
    assert.equal(target, user);
    assert.equal(provider.providerId, 'google.com');
    assert.equal(provider.customParameters.prompt, 'select_account');
    throw { code: 'auth/credential-already-in-use' };
  }), /another Calculus Ninja account/);
  assert.equal(auth.currentUser, user);
  user.providerData.push({ providerId: 'google.com' });
  assert.equal(await connectGoogleAccount(auth, () => assert.fail('already linked')), user);
});

const emulator = process.env.FIREBASE_AUTH_EMULATOR_HOST;
test('email signup, profile recovery, and Google linking retain the same account', { skip: emulator !== '127.0.0.1:9099' }, async t => {
  const apps = [];
  const session = () => {
    const app = initializeApp({ projectId: 'demo-calculus-rendering', apiKey: 'emulator-only' }, `auth-${crypto.randomUUID()}`);
    apps.push(app);
    const auth = getAuth(app);
    connectAuthEmulator(auth, `http://${emulator}`, { disableWarnings: true });
    return auth;
  };
  const password = 'Qa-Password-937!';
  try {
    await t.test('signup saves the name; either linked provider signs in to the original UID', async () => {
      const auth = session(), email = `signup-${crypto.randomUUID()}@example.test`;
      let savedName;
      const user = await createEmailAccount(auth, ` ${email} `, password, '  Email Ninja  ', async name => { savedName = name; });
      assert.equal(user.displayName, 'Email Ninja');
      assert.equal(savedName, 'Email Ninja');
      const uid = user.uid;
      const progressByUid = new Map([[uid, { xp: 125, gamesPlayed: 7 }]]);
      // The Auth emulator accepts unsigned Google ID tokens; this never reaches Google.
      const claims = { sub: crypto.randomUUID(), email, email_verified: true, name: 'Google Ninja', aud: 'emulator-only', iss: 'https://accounts.google.com', iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 3600 };
      const token = `${Buffer.from(JSON.stringify({ alg: 'none', typ: 'JWT' })).toString('base64url')}.${Buffer.from(JSON.stringify(claims)).toString('base64url')}.`;
      const googleCredential = GoogleAuthProvider.credential(token);
      const linked = await connectGoogleAccount(auth, target => linkWithCredential(target, googleCredential));
      assert.equal(linked.uid, uid);
      assert.deepEqual(linked.providerData.map(p => p.providerId).sort(), ['google.com', 'password']);
      await signOut(auth);
      assert.equal((await signInWithEmailAndPassword(auth, email, password)).user.uid, uid);
      await signOut(auth);
      assert.equal((await signInWithCredential(auth, googleCredential)).user.uid, uid);
      assert.deepEqual(progressByUid.get(auth.currentUser.uid), { xp: 125, gamesPlayed: 7 });

      const otherAuth = session();
      const other = await createEmailAccount(otherAuth, `other-${crypto.randomUUID()}@example.test`, password, 'Other Ninja', async () => {});
      await assert.rejects(connectGoogleAccount(otherAuth, target => linkWithCredential(target, googleCredential)), /another Calculus Ninja account/);
      assert.equal(otherAuth.currentUser.uid, other.uid);
      assert.deepEqual(otherAuth.currentUser.providerData.map(p => p.providerId), ['password']);
    });

    await t.test('a profile outage reports account creation and the password still works', async () => {
      const auth = session(), email = `recover-${crypto.randomUUID()}@example.test`;
      await assert.rejects(createEmailAccount(auth, email, password, 'Recover Ninja', async () => { throw new Error('profile unavailable'); }), AccountCreatedError);
      const uid = auth.currentUser.uid;
      await signOut(auth);
      assert.equal((await signInWithEmailAndPassword(auth, email, password)).user.uid, uid);
    });
  } finally {
    await Promise.all(apps.map(deleteApp));
  }
});
