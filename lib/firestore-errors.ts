export enum OperationType {
  CREATE = 'create', UPDATE = 'update', DELETE = 'delete', LIST = 'list', GET = 'get', WRITE = 'write',
}
// Keep account identities and diagnostic JSON out of user-facing error messages.
export function handleFirestoreError(error: unknown, operationType: OperationType, path: string | null): never {
  const message = error instanceof Error ? error.message : 'The operation could not be completed. Please retry.';
  console.error('Data operation failed', { operationType, path, message });
  throw new Error(message);
}
