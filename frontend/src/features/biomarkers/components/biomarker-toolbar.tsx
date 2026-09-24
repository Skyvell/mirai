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
import { BIOMARKER_STATUSES, type BiomarkerStatus } from '@/features/biomarkers/status'
import { BIOMARKER_VIEWS, type BiomarkerView } from '@/features/biomarkers/use-biomarker-view'

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
  view: BiomarkerView
  onViewChange: (value: BiomarkerView) => void
}

function parseStatusFilter(value: string): BiomarkerStatus | undefined {
  return BIOMARKER_STATUSES.find((status) => status === value)
}

function parseView(value: string): BiomarkerView | undefined {
  return BIOMARKER_VIEWS.find((view) => view === value)
}

export function BiomarkerToolbar({
  query,
  onQueryChange,
  statusFilter,
  onStatusFilterChange,
  view,
  onViewChange,
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
      <ToggleGroup
        type="single"
        value={view}
        onValueChange={(value) => {
          const next = parseView(value)
          if (next !== undefined) onViewChange(next)
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
