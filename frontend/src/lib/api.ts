import { client } from '@/client/client.gen'

/** Point the generated client at the backend and attach the Clerk Bearer token. */
export function configureApiClient(getToken: () => Promise<string | null>) {
  client.setConfig({
    baseUrl: import.meta.env.VITE_API_URL,
    auth: async () => (await getToken()) ?? undefined,
  })
}

/** Surface FastAPI's `detail` from a thrown error body, falling back to the raw error. */
export function apiErrorMessage(error: unknown): string {
  if (
    error !== null &&
    typeof error === 'object' &&
    'detail' in error &&
    typeof error.detail === 'string'
  ) {
    return error.detail
  }
  return error instanceof Error ? error.message : String(error)
}
