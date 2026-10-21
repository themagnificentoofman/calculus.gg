import { createRemoteJWKSet, jwtVerify } from 'jose';

const googleKeys = createRemoteJWKSet(new URL('https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com'), {
  timeoutDuration: 5000,
});

// Firebase ID tokens are verified with Google's signing keys. No service-account
// key is needed. Revoked/disabled accounts may remain valid until token expiry.
export async function verifyFirebaseToken(token, projectId, keys = googleKeys) {
  const { payload } = await jwtVerify(token, keys, {
    algorithms: ['RS256'],
    audience: projectId,
    issuer: `https://securetoken.google.com/${projectId}`,
    requiredClaims: ['exp', 'iat', 'auth_time', 'sub'],
  });
  const now = Math.floor(Date.now() / 1000);
  if (typeof payload.sub !== 'string' || payload.sub.length === 0 || payload.sub.length > 128 ||
      typeof payload.iat !== 'number' || payload.iat > now ||
      typeof payload.auth_time !== 'number' || payload.auth_time > now) {
    throw new Error('Invalid Firebase token claims');
  }
  return payload.sub;
}
