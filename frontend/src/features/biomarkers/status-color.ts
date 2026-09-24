import { cn } from 'cn'
import type { BiomarkerStatus } from '@/features/biomarkers/status'

const STATUS_COLOR_VAR =
  'data-[status=optimal]:[--status-color:var(--optimal)] ' +
  'data-[status=normal]:[--status-color:var(--normal)] ' +
  'data-[status=critical]:[--status-color:var(--critical)]'

export function resolveStatusColorProps(status: BiomarkerStatus, className?: string) {
  return { 'data-status': status, className: cn(STATUS_COLOR_VAR, className) }
}
