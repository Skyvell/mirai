import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'

export const Route = createFileRoute('/_authenticated/omics')({
  component: () => <Page title="Omics" description="Genomics, transcriptomics, epigenomics, proteomics, metabolomics, and microbiome." />,
})
