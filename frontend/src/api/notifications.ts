/**
 * Notifications API - Stub for admin features
 * This is a simplified version since market-pie5-bot doesn't have full notification system
 */

export interface NotificationPreferences {
  email_enabled?: boolean
  notify_rank_changes?: boolean
  notify_analysis_complete?: boolean
}

const defaultPrefs: NotificationPreferences = {
  email_enabled: true,
  notify_rank_changes: true,
  notify_analysis_complete: true,
}

export const notificationsApi = {
  async getPreferences() {
    return {
      data: defaultPrefs,
    }
  },

  async updatePreferences(prefs: NotificationPreferences) {
    return {
      data: prefs,
    }
  },
}
