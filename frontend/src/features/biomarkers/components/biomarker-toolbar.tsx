import { Search } from 'lucide-react'
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group'

type BiomarkerToolbarProps = {
  query: string
  onQueryChange: (value: string) => void
}

export function BiomarkerToolbar({ query, onQueryChange }: BiomarkerToolbarProps) {
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
    </div>
  )
}
