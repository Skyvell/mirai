import { LayoutGrid, Rows3, Search } from 'lucide-react'
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { BIOMARKER_STATUSES, parseStatus, type BiomarkerStatus } from '../domain/status'
import { parseViewMode, type BiomarkerViewMode } from '../domain/view-mode'

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
  viewMode: BiomarkerViewMode
  onViewModeChange: (value: BiomarkerViewMode) => void
}

export function BiomarkerToolbar({
  query,
  onQueryChange,
  statusFilter,
  onStatusFilterChange,
  viewMode,
  onViewModeChange,
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
        onValueChange={(value) => onStatusFilterChange(parseStatus(value))}
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
      <ToggleGroup
        type="single"
        value={viewMode}
        onValueChange={(value) => {
          const next = parseViewMode(value)
          if (next !== undefined) onViewModeChange(next)
        }}
        variant="outline"
        className="ml-auto hidden md:flex"
      >
        <ToggleGroupItem value="tile" aria-label="Show as a grid of tiles">
          <LayoutGrid />
        </ToggleGroupItem>
        <ToggleGroupItem value="row" aria-label="Show as stacked rows">
          <Rows3 />
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  )
}
