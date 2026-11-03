declare namespace Cloudflare {
  interface Env {
    DB?: D1Database;
    BUCKET?: R2Bucket;
    OPENAI_API_KEY?: string;
    FIREBASE_SERVICE_ACCOUNT_JSON?: string;
    OPENAI_MODEL?: string;
  }
}
