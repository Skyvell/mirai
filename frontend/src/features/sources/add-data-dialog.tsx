import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { prefetchBiomarkerCatalogue } from '@/features/biomarkers/api'
import { ManualEntryForm } from '@/features/biomarkers/components/manual-entry-form'
import { UploadTab } from '@/features/lab-uploads/components/upload-tab'

// Every way data gets in, registered by the feature that owns it. Adding a
// source — an Oura connection, a genome file — is one entry here plus a
// self-contained component over there; this file stays the same size.
const TABS = [
  { value: 'upload', label: 'Upload lab PDF', Component: UploadTab },
  { value: 'manual', label: 'Manual entry', Component: ManualEntryForm },
] as const

export function AddDataDialog() {
  const [open, setOpen] = useState(false)

  // Warm the catalogue when the shell mounts, not when the dialog opens, so the
  // picker is already populated by the time anyone reaches it.
  const queryClient = useQueryClient()
  useEffect(() => {
    prefetchBiomarkerCatalogue(queryClient)
  }, [queryClient])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
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
        <Tabs defaultValue={TABS[0].value}>
          <TabsList className="w-full">
            {TABS.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
          {/* forceMount keeps a half-filled form alive across tab switches;
              the dialog unmounting on close still resets it per session. */}
          {TABS.map(({ value, Component }) => (
            <TabsContent
              key={value}
              value={value}
              forceMount
              className="pt-2 data-[state=inactive]:hidden"
            >
              <Component />
            </TabsContent>
          ))}
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
