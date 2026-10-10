/**
 * Simple toast notification system for market-pie5-bot.
 */

let toastContainer: HTMLDivElement | null = null

function ensureToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div')
    toastContainer.className = 'fixed top-4 right-4 z-50 space-y-2'
    document.body.appendChild(toastContainer)
  }
  return toastContainer
}

function createToast(message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') {
  ensureToastContainer()
  const container = ensureToastContainer()

  const toast = document.createElement('div')
  const bgColor =
    type === 'success'
      ? 'bg-green-600'
      : type === 'error'
        ? 'bg-red-600'
        : type === 'warning'
          ? 'bg-amber-600'
          : 'bg-blue-600'

  toast.className = `${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 min-w-[300px]`
  toast.innerHTML = `
    <span>${message}</span>
    <button class="ml-auto text-white/80 hover:text-white" onclick="this.parentElement.remove()">×</button>
  `

  container.appendChild(toast)

  setTimeout(() => {
    toast.remove()
  }, 4000)
}

export const toast = Object.assign(
  (message: string) => createToast(message, 'info'),
  {
    success: (message: string) => createToast(message, 'success'),
    error: (message: string) => createToast(message, 'error'),
    info: (message: string) => createToast(message, 'info'),
    warning: (message: string) => createToast(message, 'warning'),
    authError: (message: string) => createToast(message, 'error'),
    networkError: () =>
      createToast('Cannot reach the server. Check your connection and try again.', 'error'),
    timeoutError: () => createToast('Request timed out. Try again in a moment.', 'error'),
    apiError: (status: number, _code?: string, detail?: string) =>
      createToast(detail || `Request failed (${status})`, 'error'),
  }
)

export default toast
