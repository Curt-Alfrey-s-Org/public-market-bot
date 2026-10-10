const STORAGE_KEY = 'market-bot-appearance'

export type BackgroundType = 'video' | 'image' | 'none'
export type SplashType = 'video' | 'image' | 'none'
export type BackgroundObjectFit = 'cover' | 'contain' | 'fill' | 'none' | 'scale-down'

export interface AppearanceSettings {
  avatarUrl?: string
  avatarNone?: boolean
  backgroundUrl?: string
  backgroundType?: BackgroundType
  splashUrl?: string
  splashType?: SplashType
  backgroundPositionX?: number
  backgroundPositionY?: number
  backgroundScale?: number
  backgroundObjectFit?: BackgroundObjectFit
}

const DEFAULT_AVATAR = '/assets/avatar-default.png'
const DEFAULT_BG = '/assets/video/grok-video-a1fee053-2343-4013-a0de-0445458248cf.mp4'

const defaults: AppearanceSettings = {
  avatarUrl: DEFAULT_AVATAR,
  avatarNone: false,
  backgroundUrl: DEFAULT_BG,
  backgroundType: 'video',
  splashUrl: DEFAULT_BG,
  splashType: 'video',
  backgroundPositionX: 0,
  backgroundPositionY: 0,
  backgroundScale: 1,
  backgroundObjectFit: 'cover',
}

export function getAppearance(): AppearanceSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...defaults }
    const parsed = JSON.parse(raw) as Partial<AppearanceSettings>
    return {
      avatarUrl: parsed.avatarUrl ?? defaults.avatarUrl,
      avatarNone: parsed.avatarNone ?? defaults.avatarNone,
      backgroundUrl: parsed.backgroundUrl ?? defaults.backgroundUrl,
      backgroundType: parsed.backgroundType ?? defaults.backgroundType,
      splashUrl: parsed.splashUrl ?? defaults.splashUrl,
      splashType: parsed.splashType ?? defaults.splashType,
      backgroundPositionX: parsed.backgroundPositionX ?? defaults.backgroundPositionX,
      backgroundPositionY: parsed.backgroundPositionY ?? defaults.backgroundPositionY,
      backgroundScale: parsed.backgroundScale ?? defaults.backgroundScale,
      backgroundObjectFit: parsed.backgroundObjectFit ?? defaults.backgroundObjectFit,
    }
  } catch {
    return { ...defaults }
  }
}

export function setAppearance(settings: Partial<AppearanceSettings>): void {
  const current = getAppearance()
  const next: AppearanceSettings = {
    ...defaults,
    ...current,
    ...settings,
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  window.dispatchEvent(new Event('appearance-changed'))
}

export function resetAppearanceToDefaults(): void {
  setAppearance(defaults)
}
