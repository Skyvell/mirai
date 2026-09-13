import type { ReactNode } from 'react'
import { cn } from 'cn'

type PageProps = {
  title: string
  description?: string
  width?: 'prose' | 'wide'
  children?: ReactNode
}

export function Page({ title, description, width = 'prose', children }: PageProps) {
  return (
    <div className={cn('mx-auto flex flex-col gap-4', width === 'wide' ? 'max-w-6xl' : 'max-w-2xl')}>
      <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
      {description ? <p className="max-w-2xl text-muted-foreground">{description}</p> : null}
      {children}
    </div>
  )
}
