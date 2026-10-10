import type { ReactNode } from 'react'
import {
  AlfaAskAiDock,
  AlfaAskAiProvider,
  AlfaWidgetProvider,
} from '@alfa-ai/chat-widget'
import { useAuth } from '@/context/AuthContext'
import { getAuthHeaders } from '@/lib/authToken'
import {
  alfaAvatarSrc,
  marketEmptyStateHint,
  marketPageHint,
  marketPlaceholder,
} from '@/lib/alfaWidgetCopy'
import { MarketAlfaRouteSync } from '@/components/MarketAlfaRouteSync'

export function AlfaWidgetShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  return (
    <AlfaWidgetProvider
      config={{
        avatarSrc: alfaAvatarSrc(),
        apiBasePath: '/api/ai',
        storagePrefix: 'market_pie5',
        getAuthHeaders,
        onUnauthenticated: () => void logout(),
        showModelPicker: false,
        pageHint: marketPageHint,
        placeholder: marketPlaceholder,
        emptyStateHint: marketEmptyStateHint,
      }}
    >
      <AlfaAskAiProvider>
        {children}
        <MarketAlfaRouteSync />
        <AlfaAskAiDock
          enabled={!!user}
          accountLabel={user?.user ?? ''}
        />
      </AlfaAskAiProvider>
    </AlfaWidgetProvider>
  )
}
