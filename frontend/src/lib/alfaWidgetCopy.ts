import type { AskAIPageId } from '@alfa-ai/chat-widget'

/** ALFa avatar with ?v=build_hash so CDN/PWA do not serve a stale PNG after deploy. */
export function alfaAvatarSrc(): string {
  const base = '/branding/alfa-ai-avatar.png'
  const buildHash = (import.meta.env.VITE_API_BUILD_HASH as string | undefined)?.trim()
  if (buildHash && buildHash !== 'unknown') {
    return `${base}?v=${encodeURIComponent(buildHash)}`
  }
  return base
}

export function marketPageHint(page: AskAIPageId): string {
  switch (page) {
    case 'dashboard':
      return 'Factual narration for dashboard metrics - not financial advice'
    case 'trades':
      return 'Questions about recent trades shown on this page'
    case 'pending-trades':
      return 'Questions about pending orders and queue status'
    case 'decision-report':
      return 'Questions about bot decision logs and rationale'
    case 'settings':
      return 'Questions about bot settings and configuration'
    default:
      return 'Factual narration for this page - not financial advice'
  }
}

export function marketPlaceholder(page: AskAIPageId): string {
  switch (page) {
    case 'dashboard':
      return 'Ask about performance stats or what you see on the dashboard...'
    case 'trades':
      return 'Ask about trades listed on this page...'
    case 'pending-trades':
      return 'Ask about pending trades or order status...'
    case 'decision-report':
      return 'Ask about decision report entries...'
    case 'settings':
      return 'Ask about settings on this page...'
    default:
      return 'Ask ALFa about what you see on this page...'
  }
}

export function marketEmptyStateHint(page: AskAIPageId): string {
  switch (page) {
    case 'dashboard':
      return 'Ask what the numbers mean or how to read the dashboard.'
    case 'trades':
      return 'Ask about trade history or patterns in the list.'
    case 'pending-trades':
      return 'Ask about pending orders or what the bot is waiting on.'
    case 'decision-report':
      return 'Ask how to interpret a decision or what a signal means.'
    case 'settings':
      return 'Ask what a setting does or how options interact.'
    default:
      return 'NOT FINANCIAL ADVICE. Answers describe data on the current page only.'
  }
}
