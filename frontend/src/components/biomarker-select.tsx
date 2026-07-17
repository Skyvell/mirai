import {
  useMemo,
  useState,
} from 'react'
import {
  Check,
  ChevronsUpDown,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import type { BiomarkerRead } from '@/client'

type BiomarkerSelectProps = {
  biomarkers: BiomarkerRead[]
  value: string
  onChange: (slug: string) => void
  placeholder?: string
  id?: string
  triggerClassName?: string
}

export function BiomarkerSelect({
  biomarkers,
  value,
  onChange,
  placeholder = 'Map to biomarker',
  id,
  triggerClassName,
}: BiomarkerSelectProps) {
  const [open, setOpen] = useState(false)

  // Present the biomarkers alphabetically.
  const sortedBiomarkers = useMemo(
    () => [...biomarkers].sort((a, b) => a.display_name.localeCompare(b.display_name)),
    [biomarkers],
  )

  // Resolve the selected slug to its biomarker for the trigger label.
  const selected = biomarkers.find((biomarker) => biomarker.slug === value)

  // Picking an item commits the mapping and closes the popover.
  function selectBiomarker(slug: string) {
    onChange(slug)
    setOpen(false)
  }

  // Match the query as a case-insensitive substring of the name or slug, replacing cmdk's fuzzy default.
  function matchSubstring(value: string, search: string, keywords?: string[]) {
    const haystack = [value, ...(keywords ?? [])].join(' ').toLowerCase()
    return haystack.includes(search.toLowerCase()) ? 1 : 0
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn('justify-between font-normal', triggerClassName)}
        >
          <span className={cn('truncate', !selected && 'text-muted-foreground')}>
            {selected ? selected.display_name : placeholder}
          </span>
          <ChevronsUpDown className="size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-0" align="start">
        <Command filter={matchSubstring}>
          <CommandInput placeholder="Search biomarkers…" />
          <CommandList>
            <CommandEmpty>No biomarker found.</CommandEmpty>
            {sortedBiomarkers.map((biomarker) => (
              <CommandItem
                key={biomarker.slug}
                value={biomarker.display_name}
                keywords={[biomarker.slug]}
                onSelect={() => selectBiomarker(biomarker.slug)}
              >
                <Check
                  className={cn('size-4', biomarker.slug === value ? 'opacity-100' : 'opacity-0')}
                />
                {biomarker.display_name}
              </CommandItem>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
