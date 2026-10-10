import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'

interface SystemPageProps {
  sidebarOpen?: boolean
  onSidebarToggle?: () => void
}

interface SystemInfo {
  cpu_usage: number
  cpu_count: number
  memory_usage: number
  memory_total: number
  memory_available: number
  disk_usage: number
  disk_total: number
  disk_free: number
  uptime: number
  timestamp: string
}

export default function SystemPage({ sidebarOpen: _sidebarOpen, onSidebarToggle }: SystemPageProps) {
  const { data: systemInfo, isLoading, isError, error } = useQuery<SystemInfo>({
    queryKey: ['system'],
    queryFn: async () => {
      const response = await apiClient.get('/api/system')
      const data = response.data
      return data.system || data
    },
    refetchInterval: 2000, // Update every 2 seconds for real-time monitoring
    retry: 2,
    retryDelay: 1000,
  })

  if (isLoading) {
    return (
      <div className="flex flex-col h-screen bg-black/90 text-foreground">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-muted rounded w-1/4"></div>
              <div className="h-64 bg-muted rounded"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isError || !systemInfo) {
    return (
      <div className="flex flex-col h-screen bg-black/90 text-foreground">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            <div className="bg-destructive/10 border border-destructive rounded-lg p-6">
              <h2 className="text-xl font-semibold text-destructive mb-2">Error Loading System Info</h2>
              <p className="text-muted-foreground">
                {error instanceof Error ? error.message : 'Failed to load system information'}
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`
    } else if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    }
    return `${secs}s`
  }

  const formatBytes = (bytes: number) => {
    const gb = bytes / (1024 ** 3)
    if (gb >= 1) {
      return `${gb.toFixed(2)} GB`
    }
    const mb = bytes / (1024 ** 2)
    if (mb >= 1) {
      return `${mb.toFixed(2)} MB`
    }
    const kb = bytes / 1024
    return `${kb.toFixed(2)} KB`
  }

  const getUsageColor = (usage: number) => {
    if (usage >= 90) return 'bg-red-500'
    if (usage >= 75) return 'bg-yellow-500'
    if (usage >= 50) return 'bg-blue-500'
    return 'bg-green-500'
  }

  const getUsageTextColor = (usage: number) => {
    if (usage >= 90) return 'text-red-400'
    if (usage >= 75) return 'text-yellow-400'
    if (usage >= 50) return 'text-blue-400'
    return 'text-green-400'
  }

  return (
    <div className="flex flex-col h-screen bg-black/90 text-foreground overflow-hidden">
      {/* Header */}
      <header className="bg-card/50 backdrop-blur-sm border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {onSidebarToggle && (
            <button
              onClick={onSidebarToggle}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold">System Monitor</h1>
            <p className="text-sm text-muted-foreground">
              Real-time system resource monitoring • Updated {new Date(systemInfo.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
        <div className="text-sm text-muted-foreground">
          Uptime: {formatUptime(systemInfo.uptime)}
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* CPU Section - htop style */}
          <div className="bg-card border border-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">CPU Usage</h2>
              <div className="text-sm text-muted-foreground">
                {systemInfo.cpu_count} Core{systemInfo.cpu_count !== 1 ? 's' : ''}
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <div className="w-24 text-sm font-mono text-muted-foreground">Overall:</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
                      <div
                        className={`h-full ${getUsageColor(systemInfo.cpu_usage)} transition-all duration-300`}
                        style={{ width: `${Math.min(systemInfo.cpu_usage, 100)}%` }}
                      />
                    </div>
                    <div className={`w-16 text-right font-mono font-semibold ${getUsageTextColor(systemInfo.cpu_usage)}`}>
                      {systemInfo.cpu_usage.toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Memory Section - htop style */}
          <div className="bg-card border border-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Memory Usage</h2>
              <div className="text-sm text-muted-foreground font-mono">
                {formatBytes(systemInfo.memory_total * 1024 ** 3)} Total
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <div className="w-24 text-sm font-mono text-muted-foreground">Used:</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
                      <div
                        className={`h-full ${getUsageColor(systemInfo.memory_usage)} transition-all duration-300`}
                        style={{ width: `${Math.min(systemInfo.memory_usage, 100)}%` }}
                      />
                    </div>
                    <div className="flex gap-4 text-sm font-mono">
                      <div className={`w-20 text-right ${getUsageTextColor(systemInfo.memory_usage)}`}>
                        {systemInfo.memory_usage.toFixed(1)}%
                      </div>
                      <div className="w-24 text-right text-muted-foreground">
                        {formatBytes((systemInfo.memory_total - systemInfo.memory_available) * 1024 ** 3)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground font-mono">
                <div className="w-24"></div>
                <div className="flex-1 flex justify-between">
                  <span>Available: {formatBytes(systemInfo.memory_available * 1024 ** 3)}</span>
                  <span>Total: {formatBytes(systemInfo.memory_total * 1024 ** 3)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Disk Section - htop style */}
          <div className="bg-card border border-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Disk Usage</h2>
              <div className="text-sm text-muted-foreground font-mono">
                {formatBytes(systemInfo.disk_total * 1024 ** 3)} Total
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <div className="w-24 text-sm font-mono text-muted-foreground">Used:</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
                      <div
                        className={`h-full ${getUsageColor(systemInfo.disk_usage)} transition-all duration-300`}
                        style={{ width: `${Math.min(systemInfo.disk_usage, 100)}%` }}
                      />
                    </div>
                    <div className="flex gap-4 text-sm font-mono">
                      <div className={`w-20 text-right ${getUsageTextColor(systemInfo.disk_usage)}`}>
                        {systemInfo.disk_usage.toFixed(1)}%
                      </div>
                      <div className="w-24 text-right text-muted-foreground">
                        {formatBytes((systemInfo.disk_total - systemInfo.disk_free) * 1024 ** 3)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground font-mono">
                <div className="w-24"></div>
                <div className="flex-1 flex justify-between">
                  <span>Free: {formatBytes(systemInfo.disk_free * 1024 ** 3)}</span>
                  <span>Total: {formatBytes(systemInfo.disk_total * 1024 ** 3)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* System Information Table - top/htop style */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">System Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-sm text-muted-foreground">CPU Cores:</span>
                  <span className="font-mono font-semibold">{systemInfo.cpu_count}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-sm text-muted-foreground">CPU Usage:</span>
                  <span className={`font-mono font-semibold ${getUsageTextColor(systemInfo.cpu_usage)}`}>
                    {systemInfo.cpu_usage.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-sm text-muted-foreground">Memory Usage:</span>
                  <span className={`font-mono font-semibold ${getUsageTextColor(systemInfo.memory_usage)}`}>
                    {systemInfo.memory_usage.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-sm text-muted-foreground">Disk Usage:</span>
                  <span className={`font-mono font-semibold ${getUsageTextColor(systemInfo.disk_usage)}`}>
                    {systemInfo.disk_usage.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-sm text-muted-foreground">Memory Total:</span>
                  <span className="font-mono font-semibold">{formatBytes(systemInfo.memory_total * 1024 ** 3)}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-sm text-muted-foreground">Memory Available:</span>
                  <span className="font-mono font-semibold">{formatBytes(systemInfo.memory_available * 1024 ** 3)}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-sm text-muted-foreground">Disk Total:</span>
                  <span className="font-mono font-semibold">{formatBytes(systemInfo.disk_total * 1024 ** 3)}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-sm text-muted-foreground">Disk Free:</span>
                  <span className="font-mono font-semibold">{formatBytes(systemInfo.disk_free * 1024 ** 3)}</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-muted-foreground">System Uptime:</span>
                  <span className="font-mono font-semibold">{formatUptime(systemInfo.uptime)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Status Legend */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-6 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-green-500"></div>
                <span className="text-muted-foreground">&lt; 50%</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-blue-500"></div>
                <span className="text-muted-foreground">50-75%</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-yellow-500"></div>
                <span className="text-muted-foreground">75-90%</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500"></div>
                <span className="text-muted-foreground">&gt; 90%</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
