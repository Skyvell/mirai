export const BIOMARKER_VIEW_MODES = ['tile', 'row'] as const
export type BiomarkerViewMode = (typeof BIOMARKER_VIEW_MODES)[number]

export function parseViewMode(value: string | null): BiomarkerViewMode | undefined {
  return BIOMARKER_VIEW_MODES.find((mode) => mode === value)
}
