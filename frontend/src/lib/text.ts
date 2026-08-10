// "1 measurement" / "3 measurements"; add-an-s covers every noun we use.
export function pluralize(count: number, noun: string): string {
  return `${count} ${noun}${count === 1 ? '' : 's'}`
}
