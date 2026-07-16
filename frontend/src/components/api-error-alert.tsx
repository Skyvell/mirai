import { AlertCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiErrorMessage } from '@/lib/api'

// Message covers failures reported as data (e.g. a stored parse error) rather
// than a thrown request error.
export function ApiErrorAlert({
  error,
  message,
}: {
  error?: unknown
  message?: string
}) {
  return (
    <Alert variant="destructive">
      <AlertCircle />
      <AlertDescription>{message ?? apiErrorMessage(error)}</AlertDescription>
    </Alert>
  )
}
