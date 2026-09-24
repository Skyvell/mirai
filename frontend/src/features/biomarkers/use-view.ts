import { useState } from 'react'
import { parseView, type BiomarkerView } from '@/features/biomarkers/view'

const STORAGE_KEY = 'mirai.biomarkers.view'
const DEFAULT_VIEW: BiomarkerView = 'tile'

function readStoredView(): BiomarkerView {
  try {
    return parseView(window.localStorage.getItem(STORAGE_KEY)) ?? DEFAULT_VIEW
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

export function useView() {
  const [view, setView] = useState<BiomarkerView>(readStoredView)

  const selectView = (next: BiomarkerView) => {
    setView(next)
    writeStoredView(next)
  }

  return { view, selectView }
}
