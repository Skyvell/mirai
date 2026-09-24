import { useState } from 'react'

export const BIOMARKER_VIEWS = ['tile', 'row'] as const
export type BiomarkerView = (typeof BIOMARKER_VIEWS)[number]

const STORAGE_KEY = 'mirai.biomarkers.view'
const DEFAULT_VIEW: BiomarkerView = 'tile'

function readStoredView(): BiomarkerView {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    return BIOMARKER_VIEWS.find((view) => view === stored) ?? DEFAULT_VIEW
  } catch {
    return DEFAULT_VIEW
  }
}

function writeStoredView(view: BiomarkerView) {
  try {
    window.localStorage.setItem(STORAGE_KEY, view)
  } catch {
    return
  }
}

export function useBiomarkerView() {
  const [view, setView] = useState<BiomarkerView>(readStoredView)

  const selectView = (next: BiomarkerView) => {
    setView(next)
    writeStoredView(next)
  }

  return { view, selectView }
}
