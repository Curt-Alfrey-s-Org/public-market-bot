/**
 * Hook for user settings aggregation
 */

import { useNotificationPrefs } from './useNotificationPrefs'
import { useAuth } from '@/context/AuthContext'

export function useUserSettings() {
  const auth = useAuth()
  const user = 'user' in auth ? auth.user : undefined
  const isAdmin = 'isAdmin' in auth ? auth.isAdmin : false
  const notificationPrefs = useNotificationPrefs()

  return {
    user,
    isAdmin,
    notificationPrefs,
  }
}
