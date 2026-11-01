import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { setTheme, useTheme } from '@/lib/theme'

export function ThemeToggle() {
  const theme = useTheme()

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
    >
      {theme === 'dark' ? <Sun /> : <Moon />}
    </Button>
  )
}
