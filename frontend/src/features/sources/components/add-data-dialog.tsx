import { Suspense, lazy, useState } from 'react'
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

// Every way data gets in, registered by the feature that owns it. Adding a
// source — an Oura connection, a genome file — is one entry here plus a
// self-contained component over there; this file stays the same size.
// Loaded lazily: the trigger sits in the always-mounted nav, so a static import
// would put every tab's dependencies on the shell's critical path.
const TABS = [
  {
    value: 'upload',
    label: 'Upload lab PDF',
    Component: lazy(() =>
      import('@/features/lab-uploads/components/upload-tab').then((m) => ({
        default: m.UploadTab,
      })),
    ),
  },
  {
    value: 'manual',
    label: 'Manual entry',
    Component: lazy(() =>
      import('@/features/biomarkers/components/manual-entry-form').then((m) => ({
        default: m.ManualEntryForm,
      })),
    ),
  },
]

export function AddDataDialog() {
  const [open, setOpen] = useState(false)

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
        <Tabs defaultValue="upload">
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
              <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
                <Component />
              </Suspense>
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
