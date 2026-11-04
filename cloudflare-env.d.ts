declare namespace Cloudflare {
  interface Env {
    DB?: D1Database;
    BUCKET?: R2Bucket;
    OPENAI_API_KEY?: string;
    FIREBASE_SERVICE_ACCOUNT_JSON?: string;
    OPENAI_MODEL?: string;
    RESEND_API_KEY?: string;
    CONTACT_FROM_EMAIL?: string;
    BANK_PILOT_PUBLIC_KEY?: string;
    BANK_PILOT_EXPIRES_AT?: string;
    BANK_OPERATOR_PUBLIC_KEY?: string;
    BANK_OPERATOR_EXPIRES_AT?: string;
    CONTENT_RELEASE_PUBLIC_KEY?: string;
    CONTENT_RELEASE_EXPIRES_AT?: string;
    CONTENT_RELEASE_ALLOWANCE?: string;
  }
}
