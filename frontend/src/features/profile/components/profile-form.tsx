import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { differenceInYears, format } from 'date-fns'
import { CalendarIcon, Check } from 'lucide-react'

import type { MeResponse } from '@/client'
import {
  currentUserQueryKey,
  updateCurrentUserMutation,
} from '@/client/@tanstack/react-query.gen'
import {
  parseDateOfBirth,
  profileSchema,
  type ProfileFormValues,
} from '@/features/profile/schema'
import { cn } from '@/lib/utils'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Label } from '@/components/ui/label'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'

const SEX_OPTIONS = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
] as const

// Fixed calendar bounds; the upper bound ("today") stays inline as it is time-dependent.
const MIN_MONTH = new Date(1900, 0)
const DEFAULT_MONTH = new Date(1990, 0)

export function ProfileForm({
  current,
  submitLabel = 'Save',
}: {
  current: MeResponse
  submitLabel?: string
}) {
  const queryClient = useQueryClient()
  const [dobOpen, setDobOpen] = useState(false)

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    mode: 'onTouched',
    defaultValues: {
      sex: current.sex ?? undefined,
      dateOfBirth: parseDateOfBirth(current.date_of_birth),
    },
  })

  const update = useMutation({
    ...updateCurrentUserMutation(),
    onSuccess: (data) => {
      // The PATCH response is the authoritative MeResponse; seeding the cache
      // flips the onboarding gate without a redundant refetch.
      queryClient.setQueryData(currentUserQueryKey(), data)

      toast.success('Profile saved')
    },
  })

  function onSubmit(values: ProfileFormValues) {
    update.mutate({
      body: {
        sex: values.sex,
        date_of_birth: format(values.dateOfBirth, 'yyyy-MM-dd'),
      },
    })
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-6">
        <FormField
          control={form.control}
          name="sex"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Biological sex</FormLabel>
              <FormControl>
                <RadioGroup
                  value={field.value}
                  onValueChange={field.onChange}
                  className="grid grid-cols-2 gap-3"
                >
                  {SEX_OPTIONS.map((option) => (
                    <Label
                      key={option.value}
                      htmlFor={`sex-${option.value}`}
                      className="flex cursor-pointer items-center justify-between rounded-lg border border-input bg-background px-4 py-3 font-medium transition-colors hover:bg-accent has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5"
                    >
                      <span>{option.label}</span>
                      <RadioGroupItem
                        id={`sex-${option.value}`}
                        value={option.value}
                        className="sr-only"
                      />
                      {field.value === option.value && (
                        <Check className="size-4 text-primary" />
                      )}
                    </Label>
                  ))}
                </RadioGroup>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="dateOfBirth"
          render={({ field }) => (
            <FormItem className="flex flex-col">
              <FormLabel>Date of birth</FormLabel>
              <Popover open={dobOpen} onOpenChange={setDobOpen}>
                <PopoverTrigger asChild>
                  <FormControl>
                    <Button
                      type="button"
                      variant="outline"
                      className={cn(
                        'w-full justify-start gap-2 font-normal',
                        !field.value && 'text-muted-foreground',
                      )}
                    >
                      <CalendarIcon className="size-4" />
                      {field.value
                        ? format(field.value, 'd MMMM yyyy')
                        : 'Select your date of birth'}
                    </Button>
                  </FormControl>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    captionLayout="dropdown"
                    selected={field.value}
                    onSelect={(date) => {
                      field.onChange(date)
                      if (date) setDobOpen(false)
                    }}
                    startMonth={MIN_MONTH}
                    endMonth={new Date()}
                    disabled={{ after: new Date() }}
                    defaultMonth={field.value ?? DEFAULT_MONTH}
                    autoFocus
                  />
                </PopoverContent>
              </Popover>
              {field.value ? (
                <FormDescription>{differenceInYears(new Date(), field.value)} years old</FormDescription>
              ) : null}
              <FormMessage />
            </FormItem>
          )}
        />

        {update.isError && <ApiErrorAlert error={update.error} />}

        <Button type="submit" className="w-full" disabled={update.isPending}>
          {update.isPending ? 'Saving…' : submitLabel}
        </Button>
      </form>
    </Form>
  )
}
