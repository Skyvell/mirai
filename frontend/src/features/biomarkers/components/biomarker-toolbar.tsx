import { Search } from 'lucide-react'
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { BIOMARKER_STATUSES, type BiomarkerStatus } from '@/features/biomarkers/status'

const ALL_STATUSES = 'all'

const STATUS_LABELS: Record<BiomarkerStatus, string> = {
  optimal: 'Optimal',
  normal: 'Normal',
  critical: 'Critical',
}

type BiomarkerToolbarProps = {
  query: string
  onQueryChange: (value: string) => void
  statusFilter: BiomarkerStatus | undefined
  onStatusFilterChange: (value: BiomarkerStatus | undefined) => void
}

function parseStatusFilter(value: string): BiomarkerStatus | undefined {
  return BIOMARKER_STATUSES.find((status) => status === value)
}

export function BiomarkerToolbar({
  query,
  onQueryChange,
  statusFilter,
  onStatusFilterChange,
}: BiomarkerToolbarProps) {
  return (
    <div className="flex items-center gap-2">
      <InputGroup className="max-w-xs">
        <InputGroupAddon>
          <Search />
        </InputGroupAddon>
        <InputGroupInput
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search markers"
          aria-label="Search markers"
        />
      </InputGroup>
      <Select
        value={statusFilter ?? ALL_STATUSES}
        onValueChange={(value) => onStatusFilterChange(parseStatusFilter(value))}
      >
        <SelectTrigger className="w-40" aria-label="Filter by status">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_STATUSES}>All statuses</SelectItem>
          {BIOMARKER_STATUSES.map((status) => (
            <SelectItem key={status} value={status}>
              {STATUS_LABELS[status]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
