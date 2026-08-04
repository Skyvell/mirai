import { UserButton } from '@clerk/react'

import type { MeResponse } from '@/client'
import { ProfileForm } from '@/components/profile-form'

// Blocking first-run step: the app stays unreachable until sex + DOB are set,
// because every biomarker reference range depends on them.
export function Onboarding({ current }: { current: MeResponse }) {
  return (
    <div className="grid min-h-svh place-items-center bg-background p-6">
      <div className="w-full max-w-md">
        <div className="mb-10 flex items-center justify-between">
          <span className="text-lg font-semibold tracking-tight">Mirai</span>
          <UserButton />
        </div>

        <h1 className="text-2xl font-semibold tracking-tight">
          A couple of details first
        </h1>
        <p className="mt-2 text-muted-foreground">
          Your sex and date of birth set the reference ranges we compare every
          biomarker against. We ask once — you can change them later in Settings.
        </p>

        <div className="mt-8">
          <ProfileForm current={current} submitLabel="Continue" />
        </div>
      </div>
    </div>
  )
}
