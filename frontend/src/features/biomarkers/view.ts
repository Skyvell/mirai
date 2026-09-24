export const BIOMARKER_VIEWS = ['tile', 'row'] as const
export type BiomarkerView = (typeof BIOMARKER_VIEWS)[number]

export function parseView(value: string | null): BiomarkerView | undefined {
  return BIOMARKER_VIEWS.find((view) => view === value)
}
