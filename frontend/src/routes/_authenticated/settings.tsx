import { createFileRoute } from '@tanstack/react-router'
import { SettingsPage } from '@/features/profile'

export const Route = createFileRoute('/_authenticated/settings')({
  component: SettingsPage,
})
