import { cn } from 'cn'
import type { BiomarkerIntervals } from '@/features/biomarkers/intervals'
import { computeBiomarkerStatus, type BiomarkerStatus } from '@/features/biomarkers/status'
import {
  computePercentWithin,
  expandInterval,
  sampleInterval,
  type Interval,
} from '@/lib/math/interval'

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
  intervals: BiomarkerIntervals
}

export function BiomarkerRuler({ value, intervals }: BiomarkerRulerProps) {
  const range = computeDrawnRange(intervals)
  if (range === null) return null

  return (
    <div className="flex flex-col gap-1.5">
      <div className="relative h-5.25" aria-hidden="true">
        <Ticks statuses={computeTickStatuses(range, intervals)} />
        <Pin percent={computePercentWithin(value, range)} />
      </div>
      <Marks intervals={intervals} range={range} />
    </div>
  )
}

function Ticks({ statuses }: { statuses: BiomarkerStatus[] }) {
  return (
    <div className="absolute inset-x-0 bottom-0 flex items-end justify-between">
      {statuses.map((status, i) => (
        <div key={i} className={cn('w-px', TICK_CLASS[status])} />
      ))}
    </div>
  )
}

// Requires an ancestor defining --status-color; BiomarkerCard sets it from the
// measurement's status.
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

function Marks({ intervals, range }: { intervals: BiomarkerIntervals; range: Interval }) {
  const { reference, optimal } = intervals

  // Reference and optimal bounds often coincide, and two labels at one position
  // would overprint.
  const marks = [...new Set([reference?.low, optimal?.low, optimal?.high, reference?.high])]
    .filter((mark): mark is number => mark !== null && mark !== undefined)
    .sort((a, b) => a - b)

  return (
    <div className="relative h-4 text-[11px] text-muted-foreground">
      {marks.map((mark) => (
        <span
          key={mark}
          className="absolute -translate-x-1/2"
          style={{ left: `${computePercentWithin(mark, range)}%` }}
        >
          {mark}
        </span>
      ))}
    </div>
  )
}

// The reference band padded at both ends, falling back to the optimal bound where
// a reference bound is missing. Without both ends there is no scale to draw.
function computeDrawnRange({ reference, optimal }: BiomarkerIntervals): Interval | null {
  const min = reference?.low ?? optimal?.low ?? null
  const max = reference?.high ?? optimal?.high ?? null
  if (min === null || max === null) return null

  return expandInterval({ min, max }, PAD)
}

// Each tick reports the status its own position would read, so the scale and the
// label can never disagree.
function computeTickStatuses(range: Interval, intervals: BiomarkerIntervals): BiomarkerStatus[] {
  return sampleInterval(range, TICKS).map((value) => computeBiomarkerStatus({ value, intervals }))
}
