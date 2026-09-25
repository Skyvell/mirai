import type { BiomarkerRead } from '@/client'

export function findBiomarker(
  biomarkers: BiomarkerRead[] | undefined,
  slug: string,
): BiomarkerRead | undefined {
  return biomarkers?.find((biomarker) => biomarker.slug === slug)
}
