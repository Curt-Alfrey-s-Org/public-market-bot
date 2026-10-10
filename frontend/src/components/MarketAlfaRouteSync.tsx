import { useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { useAlfaAskAiRegistration } from '@alfa-ai/chat-widget'

const PATH_TO_PAGE: Record<string, string> = {
  '/': 'dashboard',
  '/trades': 'trades',
  '/pending-trades': 'pending-trades',
  '/reports/decisions': 'decision-report',
  '/settings': 'settings',
}

export function marketPageFromPath(pathname: string): string | null {
  return PATH_TO_PAGE[pathname] ?? null
}

/** Registers the current route so the shared ALFa dock knows which page context to send. */
export function MarketAlfaRouteSync() {
  const location = useLocation()

  const registration = useMemo(() => {
    const page = marketPageFromPath(location.pathname)
    if (!page) return null
    return {
      page,
      playerName: '',
      context: { path: location.pathname },
    }
  }, [location.pathname])

  useAlfaAskAiRegistration(registration)
  return null
}
