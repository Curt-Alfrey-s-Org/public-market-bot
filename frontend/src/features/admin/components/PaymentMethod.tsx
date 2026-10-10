/**
 * Payment method / subscription status
 */

import { Link } from 'react-router-dom'

export function PaymentMethod() {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <h3 className="text-lg font-semibold text-white mb-2">Payment Method</h3>
      <p className="text-sm text-slate-400 mb-4">
        Manage your AI Coach subscription and payment methods.
      </p>
      <Link
        to="/ai-coach"
        className="inline-flex items-center px-4 py-2 rounded-lg bg-sky-600 text-white text-sm font-medium hover:bg-sky-500 transition-colors"
      >
        Go to AI Coach →
      </Link>
    </div>
  )
}
