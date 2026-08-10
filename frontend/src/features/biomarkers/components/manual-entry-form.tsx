import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  createBiomarkerMeasurementsMutation,
  listBiomarkersOptions,
} from '@/client/@tanstack/react-query.gen'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { invalidateBiomarkerSeries } from '@/features/biomarkers/api'
import { BiomarkerSelect } from '@/features/biomarkers/components/biomarker-select'
import { localIsoDate } from '@/lib/date'

// Self-contained Add-data tab for entering one measurement by hand.
export function ManualEntryForm() {
  const queryClient = useQueryClient()
  const biomarkers = useQuery(listBiomarkersOptions())
  const [slug, setSlug] = useState('')
  const [value, setValue] = useState('')
  const [unit, setUnit] = useState('')
  const [referenceLow, setReferenceLow] = useState('')
  const [referenceHigh, setReferenceHigh] = useState('')
  const [measuredAt, setMeasuredAt] = useState(() => localIsoDate(new Date()))

  const findBiomarker = (s: string) => biomarkers.data?.find((b) => b.slug === s)
  const selected = findBiomarker(slug)

  const create = useMutation({
    ...createBiomarkerMeasurementsMutation(),
    onSuccess: ([created]) => {
      invalidateBiomarkerSeries(queryClient)
      setValue('')
      toast.success(`Added ${created.display_name} — ${created.value} ${created.unit}`)
    },
  })

  function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!slug || !value || !measuredAt) return
    create.mutate({
      body: [
        {
          biomarker_slug: slug,
          value,
          unit: unit || undefined,
          measured_at: measuredAt,
          reference_low: referenceLow || undefined,
          reference_high: referenceHigh || undefined,
        },
      ],
    })
  }

  return (
    <form className="flex flex-col gap-3" onSubmit={onSubmit}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="biomarker">Biomarker</Label>
        <BiomarkerSelect
          id="biomarker"
          modal
          triggerClassName="w-full"
          biomarkers={biomarkers.data ?? []}
          value={slug}
          placeholder={biomarkers.isPending ? 'Loading biomarkers…' : 'Pick a biomarker'}
          onChange={(next) => {
            setSlug(next)
            const picked = findBiomarker(next)
            if (picked) setUnit(picked.canonical_unit)
            // Ranges are biomarker-specific; don't carry them across a switch.
            setReferenceLow('')
            setReferenceHigh('')
          }}
        />
        {biomarkers.isError && <ApiErrorAlert error={biomarkers.error} />}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="value">Value</Label>
          <Input
            id="value"
            inputMode="decimal"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="5.4"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="unit">Unit</Label>
          <Input id="unit" value={unit} onChange={(e) => setUnit(e.target.value)} />
          {selected && unit && unit !== selected.canonical_unit && (
            <p className="text-xs text-muted-foreground">
              Catalogue unit is {selected.canonical_unit}.
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="reference-low">Reference low</Label>
          <Input
            id="reference-low"
            inputMode="decimal"
            value={referenceLow}
            onChange={(e) => setReferenceLow(e.target.value)}
            placeholder="optional"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="reference-high">Reference high</Label>
          <Input
            id="reference-high"
            inputMode="decimal"
            value={referenceHigh}
            onChange={(e) => setReferenceHigh(e.target.value)}
            placeholder="optional"
          />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="measured-at">Measured on</Label>
        <Input
          id="measured-at"
          type="date"
          value={measuredAt}
          onChange={(e) => setMeasuredAt(e.target.value)}
        />
      </div>

      {create.isError && <ApiErrorAlert error={create.error} />}

      <div>
        <Button type="submit" disabled={!slug || !value || !measuredAt || create.isPending}>
          {create.isPending ? 'Adding…' : 'Add measurement'}
        </Button>
      </div>
    </form>
  )
}
