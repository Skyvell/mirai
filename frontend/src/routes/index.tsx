import { createFileRoute } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'

export const Route = createFileRoute('/')({
  component: HomeComponent,
})

function HomeComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-start gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Mirai</h1>
      <p className="text-muted-foreground">
        Track your blood biomarkers and optimize your health.
      </p>
      <Button>Get started</Button>
    </div>
  )
}
