import { Link } from 'react-router-dom'

interface PageErrorFallbackProps {
  onRetry?: () => void
}

/**
 * Route-level error fallback. "Try again" resets the boundary; "Go to Dashboard" navigates away.
 * ErrorBoundary injects onRetry when using this as fallback.
 */
export default function PageErrorFallback({ onRetry }: PageErrorFallbackProps) {
  return (
    <div
      className="flex flex-col items-center justify-center min-h-[40vh] px-4"
      role="alert"
      aria-live="assertive"
    >
      <div className="bg-card border border-destructive rounded-lg p-6 max-w-md w-full">
        <h2 className="text-lg font-bold text-destructive mb-2">Something went wrong</h2>
        <p className="text-sm text-muted-foreground mb-4">
          This page encountered an error. Try again or go back to the dashboard.
        </p>
        <div className="flex gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              aria-label="Try loading this page again"
            >
              Try again
            </button>
          )}
          <Link
            to="/"
            className="px-4 py-2 bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 transition-colors"
            aria-label="Go to dashboard"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}
