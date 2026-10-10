import { AlfaWidgetProvider, AlfaChatPopup } from '@alfa-ai/chat-widget'
import { getAuthHeaders } from '@/lib/authToken'
import {
  alfaAvatarSrc,
  marketEmptyStateHint,
  marketPageHint,
  marketPlaceholder,
} from '@/lib/alfaWidgetCopy'

/** Popup window route (/alfa-chat) - same geometry as contracts-bot. */
export default function AlfaChatPopupPage() {
  return (
    <AlfaWidgetProvider
      config={{
        avatarSrc: alfaAvatarSrc(),
        apiBasePath: '/api/ai',
        storagePrefix: 'market_pie5',
        getAuthHeaders,
        showModelPicker: false,
        pageHint: marketPageHint,
        placeholder: marketPlaceholder,
        emptyStateHint: marketEmptyStateHint,
      }}
    >
      <AlfaChatPopup />
    </AlfaWidgetProvider>
  )
}
