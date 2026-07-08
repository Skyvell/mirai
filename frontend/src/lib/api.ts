import type { CreateClientConfig } from '@/client/client.gen'

let getToken: (() => Promise<string | null>) | undefined

/** Inject Clerk's token getter; the client reads it per authenticated request. */
export function setApiTokenGetter(getter: () => Promise<string | null>) {
  getToken = getter
}

/** Applied by the generated client at creation (runtimeConfigPath in openapi-ts.config.ts). */
export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: import.meta.env.VITE_API_URL,
  auth: async () => (await getToken?.()) ?? undefined,
})

/** Surface FastAPI's `detail` from a thrown error body, falling back to the raw error. */
export function apiErrorMessage(error: unknown): string {
  if (error !== null && typeof error === 'object' && 'detail' in error) {
    const { detail } = error as { detail: unknown }
    if (typeof detail === 'string') return detail
    // 422 validation errors carry a list of {msg, loc, type}.
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (d && typeof d === 'object' && 'msg' in d ? String(d.msg) : String(d)))
        .join('; ')
    }
  }
  return error instanceof Error ? error.message : String(error)
}
