export function computePercentageChange(currentValue: number, previousValue: number): number {
  return Math.round(((currentValue - previousValue) / previousValue) * 100)
}
