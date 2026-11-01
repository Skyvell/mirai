import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts/core'
import type { ComposeOption } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import type { LineSeriesOption } from 'echarts/charts'
import {
  DatasetComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components'
import type {
  DatasetComponentOption,
  GridComponentOption,
  LegendComponentOption,
  MarkAreaComponentOption,
  TitleComponentOption,
  TooltipComponentOption,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { subYears } from 'date-fns'
import { Page } from '@/components/page'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { useTheme } from '@/lib/theme'

echarts.use([
  LineChart,
  DatasetComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  TitleComponent,
  TooltipComponent,
  CanvasRenderer,
])

type EChartsOption = ComposeOption<
  | LineSeriesOption
  | DatasetComponentOption
  | GridComponentOption
  | LegendComponentOption
  | MarkAreaComponentOption
  | TitleComponentOption
  | TooltipComponentOption
>

type DetailsRangeArea = NonNullable<NonNullable<LineSeriesOption['markArea']>['data']>[number]

const measurements: { measured_at: string; value: number; status: 'optimal' | 'normal' | 'critical' }[] = [
  { measured_at: '2025-01-14', value: 150, status: 'normal' },
  { measured_at: '2025-03-02', value: 230, status: 'critical' },
  { measured_at: '2025-03-20', value: 224, status: 'critical' },
  { measured_at: '2025-07-08', value: 218, status: 'critical' },
  { measured_at: '2025-11-25', value: 135, status: 'normal' },
  { measured_at: '2026-02-11', value: 147, status: 'normal' },
  { measured_at: '2026-08-04', value: 260, status: 'critical' },
]

const referenceRange: { start: string; end: string; low: number | null; high: number | null }[] = [
  { start: '2021-10-19', end: '2025-09-10', low: 100, high: 200 },
  { start: '2025-09-10', end: '2026-10-19', low: 110, high: 215 },
]

const timeframeYears = { '1y': 1, '3y': 3, '5y': 5, all: null }

const option: EChartsOption = {
  backgroundColor: 'transparent',
  title: { text: 'Total cholesterol', left: 'center' },
  tooltip: { trigger: 'axis' },
  legend: { data: ['Measurement', { name: 'Reference range', icon: 'rect' }] },
  xAxis: {
    type: 'time',
    name: 'Time',
    axisLabel: { formatter: '{MMM} {yyyy}' },
  },
  yAxis: { type: 'value', name: 'mg/dL' },
  dataset: { source: measurements },
  series: [
    {
      name: 'Measurement',
      type: 'line',
      encode: { x: 'measured_at', y: 'value' },
      showSymbol: true,
      lineStyle: { color: '#3aa0ff', width: 2 },
      itemStyle: { color: '#3aa0ff' },
    },
    {
      name: 'Reference range',
      type: 'line',
      data: referenceRange.flatMap(({ start, end, high }) => [
        [start, high],
        [end, high],
      ]),
      symbol: 'none',
      silent: true,
      tooltip: { show: false },
      itemStyle: { color: 'rgba(58, 160, 255, 0.15)' },
      lineStyle: { color: '#3aa0ff', type: 'dashed', width: 1, opacity: 0.7 },
      markArea: {
        silent: true,
        itemStyle: { color: 'rgba(58, 160, 255, 0.15)' },
        data: referenceRange.map(({ start, end, low, high }): DetailsRangeArea => [
          { xAxis: start, yAxis: low ?? undefined },
          { xAxis: end, yAxis: high ?? undefined },
        ]),
      },
    },
    {
      name: 'Reference range',
      type: 'line',
      data: referenceRange.flatMap(({ start, end, low }) => [
        [start, low],
        [end, low],
      ]),
      symbol: 'none',
      silent: true,
      tooltip: { show: false },
      lineStyle: { color: '#3aa0ff', type: 'dashed', width: 1, opacity: 0.7 },
    },
  ],
}

export function DetailsPage() {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<ReturnType<typeof echarts.init> | null>(null)
  const theme = useTheme()
  const [timeframe, setTimeframe] = useState<keyof typeof timeframeYears>('all')

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const chart = echarts.init(container, theme === 'dark' ? 'dark' : undefined)
    chart.setOption(option)
    chartRef.current = chart

    const observer = new ResizeObserver(() => chart.resize())
    observer.observe(container)

    return () => {
      observer.disconnect()
      chart.dispose()
      chartRef.current = null
    }
  }, [theme])

  useEffect(() => {
    const years = timeframeYears[timeframe]
    chartRef.current?.setOption({
      xAxis: { min: years === null ? measurements[0].measured_at : subYears(new Date(), years), max: new Date() },
    })
  }, [timeframe, theme])

  return (
    <Page title="Details" width="wide">
      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        value={timeframe}
        onValueChange={(value) => {
          if (value in timeframeYears) setTimeframe(value as keyof typeof timeframeYears)
        }}
        className="self-end"
      >
        {Object.keys(timeframeYears).map((key) => (
          <ToggleGroupItem key={key} value={key} className="px-3 uppercase">
            {key}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
      <div ref={containerRef} className="h-125 w-full" />
    </Page>
  )
}
