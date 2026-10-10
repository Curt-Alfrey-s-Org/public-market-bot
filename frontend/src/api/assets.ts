/**
 * Assets API: list and upload pics/videos for appearance (avatar, background, splash).
 */

import axios from 'axios'
import { getAuthHeaders } from '@/lib/authToken'

const API_BASE =
  (typeof import.meta.env.VITE_API_URL === 'string' && import.meta.env.VITE_API_URL) || ''

export interface AssetEntry {
  path: string
  name: string
  type: 'image' | 'video'
}

export async function getAssets(): Promise<AssetEntry[]> {
  const { data } = await axios.get<{ files: AssetEntry[] }>(`${API_BASE}/api/assets`, {
    headers: getAuthHeaders(),
  })
  return data.files ?? []
}

export async function uploadAssets(files: File[]): Promise<string[]> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  const { data } = await axios.post<{ urls: string[] }>(`${API_BASE}/api/assets/upload`, form, {
    timeout: 60_000,
    headers: getAuthHeaders(),
  })
  return data.urls ?? []
}
