import { AlertCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { extractApiErrorMessage } from '@/lib/api'

// Message covers failures reported as data (e.g. a stored parse error) rather
// than a thrown request error.
export function ApiErrorAlert(props: { error: unknown } | { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertCircle />
      <AlertDescription>
        {'message' in props ? props.message : extractApiErrorMessage(props.error)}
      </AlertDescription>
    </Alert>
  )
}
