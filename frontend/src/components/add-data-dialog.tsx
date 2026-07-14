import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { BiomarkerSelect } from '@/components/biomarker-select'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  createBiomarkerMeasurementsMutation,
  listBiomarkerSeriesQueryKey,
  listBiomarkersOptions,
  listLabUploadsQueryKey,
  uploadLabMutation,
} from '@/client/@tanstack/react-query.gen'
import { apiErrorMessage } from '@/lib/api'
import { localIsoDate } from '@/lib/utils'

// Owned by the dialog (not the tab) so the uploaded confirmation survives tab
// switches; reset on each open so an old confirmation doesn't resurface.
function useUploadLab() {
  const queryClient = useQueryClient()
  return useMutation({
    ...uploadLabMutation(),
    // Parsing is async: the new report appears under Sources as pending.
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
    },
  })
}

export function AddDataDialog() {
  const [open, setOpen] = useState(false)
  const upload = useUploadLab()

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) upload.reset()
        setOpen(next)
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm">Add data</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add data</DialogTitle>
          <DialogDescription>
            Upload a lab report or enter a biomarker value manually.
          </DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="upload">
          <TabsList className="w-full">
            <TabsTrigger value="upload">Upload lab PDF</TabsTrigger>
            <TabsTrigger value="manual">Manual entry</TabsTrigger>
          </TabsList>
          {/* forceMount keeps a half-filled form alive across tab switches;
              the dialog unmounting on close still resets it per session. */}
          <TabsContent value="upload" forceMount className="pt-2 data-[state=inactive]:hidden">
            <UploadTab upload={upload} />
          </TabsContent>
          <TabsContent value="manual" forceMount className="pt-2 data-[state=inactive]:hidden">
            <ManualEntryTab />
          </TabsContent>
        </Tabs>
        {/* Not DialogClose: the Link's preventDefault would swallow Radix's
            close, leaving the dialog open over the new route. */}
        <Link
          to="/sources"
          onClick={() => setOpen(false)}
          className="text-sm text-muted-foreground underline underline-offset-3 hover:text-foreground"
        >
          Manage your sources →
        </Link>
      </DialogContent>
    </Dialog>
  )
}

function UploadTab({ upload }: { upload: ReturnType<typeof useUploadLab> }) {
  const inputRef = useRef<HTMLInputElement>(null)

  function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    // Reset so re-selecting the same file fires onChange again.
    event.target.value = ''
    if (file) upload.mutate({ body: { file } })
  }

  return (
    <div className="flex flex-col gap-3">
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={onFileChange}
      />
      <div>
        <Button onClick={() => inputRef.current?.click()} disabled={upload.isPending}>
          {upload.isPending ? 'Uploading…' : 'Choose PDF'}
        </Button>
      </div>

      {upload.isError && (
        <p className="text-sm text-destructive">{apiErrorMessage(upload.error)}</p>
      )}

      {upload.isSuccess && (
        <p className="text-sm text-muted-foreground">
          Report uploaded — we&rsquo;re reading it now. Find it under Sources to review the
          extracted values before they&rsquo;re added to your record.
        </p>
      )}
    </div>
  )
}

function today(): string {
  return localIsoDate(new Date())
}

function ManualEntryTab() {
  const queryClient = useQueryClient()
  const catalog = useQuery(listBiomarkersOptions())
  const [slug, setSlug] = useState('')
  const [value, setValue] = useState('')
  const [unit, setUnit] = useState('')
  const [referenceLow, setReferenceLow] = useState('')
  const [referenceHigh, setReferenceHigh] = useState('')
  const [measuredAt, setMeasuredAt] = useState(today)
  const [lastAdded, setLastAdded] = useState<string | null>(null)

  const findBiomarker = (s: string) => catalog.data?.find((b) => b.slug === s)
  const selected = findBiomarker(slug)

  const create = useMutation({
    ...createBiomarkerMeasurementsMutation(),
    onSuccess: ([created]) => {
      queryClient.invalidateQueries({ queryKey: listBiomarkerSeriesQueryKey() })
      setValue('')
      setLastAdded(`${created.display_name} — ${created.value} ${created.unit}`)
    },
  })

  function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!slug || !value || !measuredAt) return
    setLastAdded(null)
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
          triggerClassName="w-full"
          catalogue={catalog.data ?? []}
          value={slug}
          placeholder={catalog.isPending ? 'Loading catalogue…' : 'Pick a biomarker'}
          onChange={(next) => {
            setSlug(next)
            const picked = findBiomarker(next)
            if (picked) setUnit(picked.canonical_unit)
            // Ranges are biomarker-specific; don't carry them across a switch.
            setReferenceLow('')
            setReferenceHigh('')
          }}
        />
        {catalog.isError && (
          <p className="text-sm text-destructive">{apiErrorMessage(catalog.error)}</p>
        )}
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

      {create.isError && (
        <p className="text-sm text-destructive">{apiErrorMessage(create.error)}</p>
      )}
      {lastAdded && <p className="text-sm text-muted-foreground">Added {lastAdded}.</p>}

      <div>
        <Button
          type="submit"
          disabled={!slug || !value || !measuredAt || create.isPending}
        >
          {create.isPending ? 'Adding…' : 'Add measurement'}
        </Button>
      </div>
    </form>
  )
}
