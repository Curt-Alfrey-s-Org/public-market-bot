/**
 * User Settings - Profile, Payment, API Keys
 */

import { useAuth } from '../context/AuthContext'

function ProfileSettings() {
  const { user } = useAuth()
  const role = user?.role ?? 'User'
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <h3 className="text-lg font-semibold text-white mb-2">Profile</h3>
      <p className="text-sm text-slate-400">Role: <span className="text-slate-200">{role}</span></p>
    </div>
  )
}

function PaymentMethod() {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <h3 className="text-lg font-semibold text-white mb-2">Payment</h3>
      <p className="text-sm text-slate-400">Payment options are managed by your administrator.</p>
    </div>
  )
}

function ApiKeyManagement() {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <h3 className="text-lg font-semibold text-white mb-2">API Keys</h3>
      <p className="text-sm text-slate-400">Contact your administrator for API key access.</p>
    </div>
  )
}

export default function UserSettings() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-bold text-white">User Settings</h1>
        <p className="mt-1 text-slate-400">Manage your profile and preferences.</p>
      </header>
      <div className="grid gap-6 sm:grid-cols-1 lg:grid-cols-2">
        <ProfileSettings />
        <PaymentMethod />
        <ApiKeyManagement />
      </div>
    </div>
  )
}
