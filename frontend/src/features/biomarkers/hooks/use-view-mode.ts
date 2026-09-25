import { useState } from 'react'
import { parseViewMode, type BiomarkerViewMode } from '../domain/view-mode'

const STORAGE_KEY = 'mirai.biomarkers.view'
const DEFAULT_VIEW_MODE: BiomarkerViewMode = 'tile'

function readStoredViewMode(): BiomarkerViewMode {
  try {
    return parseViewMode(window.localStorage.getItem(STORAGE_KEY)) ?? DEFAULT_VIEW_MODE
  } catch {
    return DEFAULT_VIEW_MODE
  }
}

function writeStoredViewMode(viewMode: BiomarkerViewMode) {
  try {
    window.localStorage.setItem(STORAGE_KEY, viewMode)
  } catch {
    return
  }
}

export function useViewMode() {
  const [viewMode, setViewMode] = useState<BiomarkerViewMode>(readStoredViewMode)

  const selectViewMode = (next: BiomarkerViewMode) => {
    setViewMode(next)
    writeStoredViewMode(next)
  }

  return { viewMode, selectViewMode }
}
