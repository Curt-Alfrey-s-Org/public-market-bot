/**
 * Profile settings - display user info
 */

import { useAuth } from '@/context/AuthContext'

export function ProfileSettings() {
  const { user } = useAuth()
  const role = user && typeof user === 'object' && 'role' in user ? (user as { role: string }).role : 'User'

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <h3 className="text-lg font-semibold text-white mb-2">Profile</h3>
      <div className="space-y-1 text-sm">
        <p className="text-slate-400">
          <span className="text-slate-500">Role:</span>{' '}
          <span className="text-slate-200">{role}</span>
        </p>
      </div>
    </div>
  )
}
