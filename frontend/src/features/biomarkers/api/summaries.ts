import { useQueries, type UseQueryResult } from '@tanstack/react-query'
import { parseISO } from 'date-fns'
import type {
  BiomarkerIntervalRead,
  BiomarkerIntervalsBySlug,
  BiomarkerRead,
  BiomarkerSeriesBySlug,
  MeResponse,
} from '@/client'
import {
  currentUserOptions,
  listBiomarkerSeriesOptions,
} from '@/client/@tanstack/react-query.gen'
import { isProfileComplete, type CompleteProfile } from '@/features/profile'
import { findBiomarker } from '../domain/catalogue'
import { selectBiomarkerBand, type BiomarkerInterval } from '../domain/intervals'
import type { BiomarkerSummary } from '../domain/summary'
import { biomarkerIntervalsOptions, biomarkersOptions } from './queries'

type MapBiomarkerSummariesInput = {
  series: BiomarkerSeriesBySlug
  biomarkers: BiomarkerRead[]
  intervalsBySlug: BiomarkerIntervalsBySlug
  profile: CompleteProfile
}

type BiomarkerSummaryQueries = [
  UseQueryResult<BiomarkerSeriesBySlug, unknown>,
  UseQueryResult<BiomarkerRead[], unknown>,
  UseQueryResult<BiomarkerIntervalsBySlug, unknown>,
  UseQueryResult<MeResponse, unknown>,
]

function mapBiomarkerInterval(band: BiomarkerIntervalRead | undefined): BiomarkerInterval | null {
  if (band === undefined) return null

  return {
    low: band.low === null ? null : Number(band.low),
    high: band.high === null ? null : Number(band.high),
  }
}

function mapBiomarkerSummaries({
  series,
  biomarkers,
  intervalsBySlug,
  profile,
}: MapBiomarkerSummariesInput): BiomarkerSummary[] {
  const dateOfBirth = parseISO(profile.date_of_birth)

  return Object.entries(series).flatMap(([slug, points]) => {
    const latest = points.at(-1)
    if (latest === undefined) return []

    const previous = points.at(-2)
    const measuredAt = parseISO(latest.measured_at)
    const bands = intervalsBySlug[slug] ?? []
    const subject = { sex: profile.sex, dateOfBirth, measuredAt }

    return {
      slug,
      name: findBiomarker(biomarkers, slug)?.display_name ?? slug,
      value: Number(latest.value),
      unit: latest.unit,
      intervals: {
        reference: mapBiomarkerInterval(selectBiomarkerBand(bands, 'reference', subject)),
        optimal: mapBiomarkerInterval(selectBiomarkerBand(bands, 'optimal', subject)),
      },
      previousValue: previous === undefined ? null : Number(previous.value),
      measuredAt,
    }
  })
}

// Module scope keeps the reference stable, so useQueries re-runs the mapping
// only when a query result changes.
function combineBiomarkerSummaryQueries(queries: BiomarkerSummaryQueries) {
  const [series, biomarkers, intervals, me] = queries
  const failed = queries.find((query) => query.isError)

  const data =
    series.data !== undefined &&
    biomarkers.data !== undefined &&
    intervals.data !== undefined &&
    me.data !== undefined &&
    isProfileComplete(me.data)
      ? mapBiomarkerSummaries({
          series: series.data,
          biomarkers: biomarkers.data,
          intervalsBySlug: intervals.data,
          profile: me.data,
        })
      : undefined

  return { data, isError: failed !== undefined, error: failed?.error ?? null }
}

export function useBiomarkerSummaries() {
  return useQueries({
    queries: [
      listBiomarkerSeriesOptions(),
      biomarkersOptions(),
      biomarkerIntervalsOptions(),
      currentUserOptions(),
    ],
    combine: combineBiomarkerSummaryQueries,
  })
}
