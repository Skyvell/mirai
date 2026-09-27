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
import { cn } from 'cn'
import type { BiomarkerRead } from '@/client'
import { findBiomarker } from '../domain/catalogue'
import { matchesBiomarkerName } from '../domain/filters'

// Replaces cmdk's fuzzy default, so this picker and the biomarkers page search
// agree on what matches; `1 : 0` is cmdk's score contract.
function scoreBiomarker(value: string, search: string, keywords?: string[]): number {
  return [value, ...(keywords ?? [])].some((text) => matchesBiomarkerName(text, search)) ? 1 : 0
}

type BiomarkerComboboxProps = {
  biomarkers: BiomarkerRead[]
  value: string
  onChange: (slug: string) => void
  placeholder?: string
  id?: string
  triggerClassName?: string
  modal?: boolean
}

export function BiomarkerCombobox({
  biomarkers,
  value,
  onChange,
  placeholder = 'Map to biomarker',
  id,
  triggerClassName,
  modal,
}: BiomarkerComboboxProps) {
  const [open, setOpen] = useState(false)

  // Present the biomarkers alphabetically.
  const sortedBiomarkers = useMemo(
    () => [...biomarkers].sort((a, b) => a.display_name.localeCompare(b.display_name)),
    [biomarkers],
  )

  // Resolve the selected slug to its biomarker for the trigger label.
  const selected = findBiomarker(biomarkers, value)

  // Picking an item commits the mapping and closes the popover.
  function selectBiomarker(slug: string) {
    onChange(slug)
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen} modal={modal}>
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
        <Command filter={scoreBiomarker}>
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
