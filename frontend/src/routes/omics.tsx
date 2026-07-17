import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'

export const Route = createFileRoute('/omics')({
  component: OmicsComponent,
})

function OmicsComponent() {
  return (
    <Page
      title="Omics"
      description="Genomics, transcriptomics, epigenomics, proteomics, metabolomics, and microbiome."
    />
  )
}
