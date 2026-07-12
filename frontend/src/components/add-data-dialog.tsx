import { useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  createMeasurementMutation,
  listBiomarkerCatalogOptions,
  listBiomarkersQueryKey,
  listLabUploadsQueryKey,
  uploadLabMutation,
} from '@/client/@tanstack/react-query.gen'
import type { CatalogBiomarker } from '@/client'
import { apiErrorMessage } from '@/lib/api'

export function AddDataDialog() {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)

  return (
    <Dialog
      open={open}
      // Ignore close requests while an upload is parsing (~30 s).
      onOpenChange={(next) => {
        if (!next && busy) return
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
          <TabsContent value="upload" className="pt-2">
            <UploadTab onBusyChange={setBusy} />
          </TabsContent>
          <TabsContent value="manual" className="pt-2">
            <ManualEntryTab />
          </TabsContent>
        </Tabs>
        <DialogClose asChild>
          <Link
            to="/sources"
            className="text-sm text-muted-foreground underline underline-offset-3 hover:text-foreground"
          >
            Manage your sources →
          </Link>
        </DialogClose>
      </DialogContent>
    </Dialog>
  )
}

function UploadTab({ onBusyChange }: { onBusyChange: (busy: boolean) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()
  const upload = useMutation({
    ...uploadLabMutation(),
    onMutate: () => onBusyChange(true),
    onSettled: () => onBusyChange(false),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listBiomarkersQueryKey() })
      queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
    },
  })

  function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    // Reset so re-selecting the same file fires onChange again.
    event.target.value = ''
    if (file) upload.mutate({ body: { file } })
  }

  const result = upload.data

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
          {upload.isPending ? 'Parsing report… (takes up to 30 s)' : 'Choose PDF'}
        </Button>
      </div>

      {upload.isError && (
        <p className="text-sm text-destructive">{apiErrorMessage(upload.error)}</p>
      )}

      {result && (
        <div className="text-sm text-muted-foreground">
          <p>
            Added {result.measurements.length} measurement
            {result.measurements.length === 1 ? '' : 's'}
            {result.measured_at ? ` from a report collected ${result.measured_at}` : ''}.
          </p>
          {result.skipped.length > 0 && (
            <>
              <p className="font-medium">Skipped</p>
              <ul className="list-inside list-disc">
                {result.skipped.map((s, i) => (
                  <li key={`${s.name}-${i}`}>
                    {s.name} ({s.reason})
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  )
}

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

function ManualEntryTab() {
  const queryClient = useQueryClient()
  const catalog = useQuery(listBiomarkerCatalogOptions())
  const [slug, setSlug] = useState('')
  const [value, setValue] = useState('')
  const [unit, setUnit] = useState('')
  const [measuredAt, setMeasuredAt] = useState(today)
  const [lastAdded, setLastAdded] = useState<string | null>(null)

  const byCategory = useMemo(() => {
    const groups = new Map<string, CatalogBiomarker[]>()
    for (const b of catalog.data ?? []) {
      const group = groups.get(b.category)
      if (group) group.push(b)
      else groups.set(b.category, [b])
    }
    return groups
  }, [catalog.data])

  const selected = catalog.data?.find((b) => b.slug === slug)

  const create = useMutation({
    ...createMeasurementMutation(),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: listBiomarkersQueryKey() })
      setValue('')
      setLastAdded(`${created.display_name} — ${created.value} ${created.unit}`)
    },
  })

  function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!slug || !value || !measuredAt) return
    setLastAdded(null)
    create.mutate({
      path: { slug },
      body: {
        value,
        unit: unit || undefined,
        measured_at: measuredAt,
      },
    })
  }

  return (
    <form className="flex flex-col gap-3" onSubmit={onSubmit}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="biomarker">Biomarker</Label>
        <Select
          value={slug}
          onValueChange={(next) => {
            setSlug(next)
            const picked = catalog.data?.find((b) => b.slug === next)
            if (picked) setUnit(picked.canonical_unit)
          }}
        >
          <SelectTrigger id="biomarker" className="w-full">
            <SelectValue
              placeholder={catalog.isPending ? 'Loading catalogue…' : 'Pick a biomarker'}
            />
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
