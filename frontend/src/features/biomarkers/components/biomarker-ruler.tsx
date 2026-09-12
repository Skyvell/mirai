import { cn } from 'cn'
import { computeBiomarkerStatus, type BiomarkerStatus } from '@/features/biomarkers/status'

const TICKS = 63

// Scale padding per end, as a fraction of the reference width. Derived from l.png:
// 12 of the 62 tick intervals fall outside the reference range at each end.
const PAD = 12 / 38

const TICK_CLASS: Record<BiomarkerStatus, string> = {
  critical: 'h-1.25 bg-foreground/10',
  normal: 'h-2.75 bg-foreground/20',
  optimal: 'h-4.5 bg-foreground/35',
}

type BiomarkerRulerProps = {
  value: number
  referenceLow: number | null
  referenceHigh: number | null
  optimalLow: number | null
  optimalHigh: number | null
}

type Bounds = Omit<BiomarkerRulerProps, 'value'>
type Range = { min: number; max: number }

export function BiomarkerRuler({ value, ...bounds }: BiomarkerRulerProps) {
  const range = drawnRange(bounds)
  if (range === null) return null

  return (
    <div className="relative h-5.25">
      <Ticks tiers={tierPerTick(range, bounds)} />
      <Pin percent={percentOf(value, range)} />
    </div>
  )
}

function Ticks({ tiers }: { tiers: BiomarkerStatus[] }) {
  return (
    <div className="absolute inset-x-0 bottom-0 flex items-end justify-between">
      {tiers.map((tier, i) => (
        <div key={i} className={cn('w-px', TICK_CLASS[tier])} />
      ))}
    </div>
  )
}

function Pin({ percent }: { percent: number }) {
  return (
    <div
      className="absolute inset-y-0 flex -translate-x-1/2 flex-col items-center"
      style={{ left: `${percent}%` }}
    >
      <div className="size-1.25 rounded-full bg-(--status-color)" />
      <div className="w-0.5 grow bg-(--status-color)" />
    </div>
  )
}

// The reference band padded at both ends, falling back to the optimal bound where
// a reference bound is missing. Without both ends there is no scale to draw.
function drawnRange({ referenceLow, referenceHigh, optimalLow, optimalHigh }: Bounds): Range | null {
  const low = referenceLow ?? optimalLow
  const high = referenceHigh ?? optimalHigh
  if (low === null || high === null) return null

  const pad = PAD * (high - low)
  return { min: low - pad, max: high + pad }
}

function percentOf(value: number, { min, max }: Range): number {
  return ((Math.min(Math.max(value, min), max) - min) / (max - min)) * 100
}

// A tick's tier is the status its own position would read, so the scale and the
// label can never disagree.
function tierPerTick(range: Range, bounds: Bounds): BiomarkerStatus[] {
  return Array.from({ length: TICKS }, (_, i) => {
    const value = range.min + (i / (TICKS - 1)) * (range.max - range.min)
    return computeBiomarkerStatus({ value, ...bounds })
  })
}
