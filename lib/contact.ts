export const CONTACT_COOLDOWN_SECONDS = 60;
export const CONTACT_DAILY_LIMIT = 10;
export const CONTACT_TOPICS = {
  bug: 'Bug report',
  balance: 'Balance feedback',
  question: 'Question or suggestion',
} as const;
export type ContactTopic = keyof typeof CONTACT_TOPICS;
