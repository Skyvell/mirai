export function matchesQuery(name: string, query: string | undefined): boolean {
  const needle = query?.trim().toLowerCase() ?? ''
  if (needle === '') return true

  return name.toLowerCase().includes(needle)
}
