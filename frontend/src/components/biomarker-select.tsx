import { useMemo } from 'react'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { BiomarkerRead } from '@/client'

export function BiomarkerSelect({
  catalogue,
  value,
  onChange,
  placeholder = 'Map to biomarker',
  id,
  triggerClassName,
}: {
  catalogue: BiomarkerRead[]
  value: string
  onChange: (slug: string) => void
  placeholder?: string
  id?: string
  triggerClassName?: string
}) {
  const byCategory = useMemo(() => {
    const groups = new Map<string, BiomarkerRead[]>()
    for (const b of catalogue) {
      const group = groups.get(b.category)
      if (group) group.push(b)
      else groups.set(b.category, [b])
    }
    return groups
  }, [catalogue])

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger id={id} className={triggerClassName}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {[...byCategory.entries()].map(([category, biomarkers]) => (
          <SelectGroup key={category}>
            <SelectLabel>{category}</SelectLabel>
            {biomarkers.map((b) => (
              <SelectItem key={b.slug} value={b.slug}>
                {b.display_name}
              </SelectItem>
            ))}
          </SelectGroup>
        ))}
      </SelectContent>
    </Select>
  )
}
