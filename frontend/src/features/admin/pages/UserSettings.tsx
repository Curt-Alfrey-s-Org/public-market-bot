/**
 * User Settings - NotificationPreferences, PaymentMethod, ApiKeyManagement, ProfileSettings
 */

import { NotificationPreferences } from '../components/NotificationPreferences'
import { PaymentMethod } from '../components/PaymentMethod'
import { ApiKeyManagement } from '../components/ApiKeyManagement'
import { ProfileSettings } from '../components/ProfileSettings'

export function UserSettings() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-bold text-white">User Settings</h1>
        <p className="mt-1 text-slate-400">
          Manage notification preferences, payment methods, and profile.
        </p>
      </header>

      <div className="grid gap-6 sm:grid-cols-1 lg:grid-cols-2">
        <ProfileSettings />
        <NotificationPreferences />
        <PaymentMethod />
        <ApiKeyManagement />
      </div>
    </div>
  )
}
