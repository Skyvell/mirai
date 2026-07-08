const API_URL = import.meta.env.VITE_API_URL

/** Fetch a backend endpoint with the Clerk bearer token, surfacing FastAPI's `detail` on error. */
async function authedFetch(path: string, token: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { ...init?.headers, Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `${path} failed: ${res.status}`)
  }
  return res
}

/** Fetch the authenticated caller's identity from the backend, proving JWT verification. */
export async function getMe(token: string): Promise<{ user_id: string }> {
  const res = await authedFetch('/me', token)
  return res.json()
}

export interface Measurement {
  biomarker_slug: string
  display_name: string
  value: string
  unit: string
  reference_low: string | null
  reference_high: string | null
}

export interface SkippedMarker {
  name: string
  value: string
  unit: string | null
  reason: string
}

export interface LabUploadResult {
  upload_id: string
  measured_at: string | null
  measurements: Measurement[]
  skipped: SkippedMarker[]
}

/** Upload a lab PDF for parsing. FormData sets its own multipart Content-Type. */
export async function uploadLabPdf(token: string, file: File): Promise<LabUploadResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await authedFetch('/lab-uploads', token, { method: 'POST', body: form })
  return res.json()
}

export interface MeasurementPoint {
  measured_at: string | null
  value: string
  unit: string
  reference_low: string | null
  reference_high: string | null
}

export interface BiomarkerSeries {
  slug: string
  display_name: string
  category: string
  canonical_unit: string
  measurements: MeasurementPoint[]
}

/** Fetch the caller's biomarkers, each with its measurement series sorted by date ascending. */
export async function getBiomarkers(token: string): Promise<BiomarkerSeries[]> {
  const res = await authedFetch('/biomarkers', token)
  return res.json()
}
