const API_URL = import.meta.env.VITE_API_URL

/** Fetch the authenticated caller's identity from the backend, proving JWT verification. */
export async function getMe(token: string): Promise<{ user_id: string }> {
  const res = await fetch(`${API_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    throw new Error(`GET /me failed: ${res.status}`)
  }
  return res.json()
}
