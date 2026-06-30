import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/omics')({
  component: OmicsComponent,
})

function OmicsComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Omics</h1>
      <p className="text-muted-foreground">
        Genomics, transcriptomics, epigenomics, proteomics, metabolomics, and
        microbiome.
      </p>
    </div>
  )
}
