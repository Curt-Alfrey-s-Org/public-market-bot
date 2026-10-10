import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId?: string
}

/**
 * Catches render errors; logs in all environments (not only dev), chunk-load aware UI.
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    const errorId = `err_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`
    return { hasError: true, error, errorInfo: null, errorId }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Only log in development mode
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    } else {
      console.error('ErrorBoundary:', error?.message, this.state.errorId)
    }

    this.setState({ errorInfo })

    this.props.onError?.(error, errorInfo)

    try {
      const sentry = (window as unknown as { Sentry?: { captureException?: (e: Error, ctx?: unknown) => void } })
        .Sentry
      sentry?.captureException?.(error, {
        extra: { componentStack: errorInfo.componentStack, errorId: this.state.errorId },
      })
    } catch {
      /* optional Sentry */
    }
  }

  reset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null, errorId: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        if (React.isValidElement(this.props.fallback)) {
          return React.cloneElement(this.props.fallback as React.ReactElement<{ onRetry?: () => void }>, {
            ...(this.props.fallback as React.ReactElement).props,
            onRetry: this.reset,
          })
        }
        return this.props.fallback
      }

      const err = this.state.error
      const isChunkLoadError =
        err?.message?.includes('Failed to fetch dynamically imported module') ||
        err?.message?.includes('Loading chunk') ||
        err?.message?.includes('ChunkLoadError')

      return (
        <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-50 px-4">
          <div className="border border-slate-700 bg-slate-900/90 rounded-xl p-4 sm:p-6 max-w-md w-full shadow-xl">
            <div className="flex justify-center mb-4 text-amber-500 text-4xl" aria-hidden>
              ⚠
            </div>
            <h2 className="text-xl font-semibold text-slate-50 mb-2 text-center">
              {isChunkLoadError ? 'Page failed to load' : 'Something went wrong'}
            </h2>
            <p className="text-sm text-slate-400 mb-6 text-center">
              {isChunkLoadError
                ? 'A required part of the app could not load. Try refreshing the page, or wait if the server is updating.'
                : 'An unexpected error occurred. You can try again or reload the page.'}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                type="button"
                onClick={this.reset}
                className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-sky-600 text-white text-sm font-medium hover:bg-sky-500 transition-colors"
              >
                Try again
              </button>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-800 text-slate-100 text-sm border border-slate-600 hover:bg-slate-700 transition-colors"
              >
                Reload Page
              </button>
              <button
                type="button"
                onClick={() => (window.location.href = '/')}
                className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-800 text-slate-100 text-sm border border-slate-600 hover:bg-slate-700 transition-colors"
              >
                Home
              </button>
            </div>
            {this.props.showDetails && err && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-300">
                  Technical details
                </summary>
                <pre className="mt-2 text-xs bg-slate-950/80 border border-slate-800 p-3 rounded overflow-auto max-h-48 text-slate-300">
                  {this.state.errorId && (
                    <div className="mb-2">
                      <strong>Error ID:</strong> {this.state.errorId}
                    </div>
                  )}
                  {err.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            {import.meta.env.DEV && err && !this.props.showDetails && (
              <pre className="mt-4 text-xs text-slate-500 overflow-auto max-h-32">{err.message}</pre>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
