import StatsOverview from '@/components/StatsOverview'
import StatusBanner from '@/components/StatusBanner'
import { useRealtimeStats } from '@/hooks/useRealtimeStats'
import PerformanceChart from '@/components/PerformanceChart'
import DashboardActivity from '@/components/DashboardActivity'
import MonthlyReturnsChart from '@/components/MonthlyReturnsChart'
import ModeSelector from '@/components/ModeSelector'
import DraggableDashboard from '@/components/DraggableDashboard'
import { useBotStatus } from '@/hooks/useBotStatus'
import { useMemo } from 'react'

interface DashboardProps {
  sidebarOpen?: boolean
  onSidebarToggle?: () => void
}

export default function Dashboard({ sidebarOpen: _sidebarOpen = true, onSidebarToggle: _onSidebarToggle }: DashboardProps) {
  // Invalidate stats/trades when WebSocket sends stats or trade so numbers and curves update
  useRealtimeStats()
  const { data: botStatus } = useBotStatus()

  // Define dashboard widgets with default order
  const widgets = useMemo(() => [
    {
      id: 'mode-selector',
      title: 'Mode Selector',
      defaultOrder: 1,
      component: <ModeSelector currentMode={botStatus?.mode} botRunning={botStatus?.running} />,
    },
    {
      id: 'stats-overview',
      title: 'Stats Overview',
      defaultOrder: 2,
      component: <StatsOverview />,
    },
    {
      id: 'equity-chart',
      title: 'Equity Curve',
      defaultOrder: 3,
      component: <PerformanceChart type="equity" />,
    },
    {
      id: 'pnl-chart',
      title: 'P&L Trend',
      defaultOrder: 4,
      component: <PerformanceChart type="pnl" />,
    },
    {
      id: 'monthly-returns',
      title: 'Monthly Returns',
      defaultOrder: 5,
      component: <MonthlyReturnsChart />,
    },
    {
      id: 'recent-activity',
      title: 'Recent activity',
      defaultOrder: 6,
      component: <DashboardActivity />,
    },
  ], [botStatus?.mode, botStatus?.running])

  return (
    <div className="flex flex-col h-screen bg-black/90 text-foreground overflow-hidden">
      {/* Dashboard Content */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden">
        <div className="w-full h-full p-2 sm:p-4 md:p-6 lg:p-8">
          <div className="max-w-screen-2xl mx-auto">
            <StatusBanner />
            <div className="mb-4 sm:mb-6 md:mb-8">
              <h1 className="text-xl sm:text-2xl md:text-3xl font-bold mb-1 sm:mb-2">Dashboard</h1>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Hover over any widget to see the drag handle, then drag to rearrange. Your layout is saved automatically.
              </p>
            </div>
            <DraggableDashboard widgets={widgets} />
          </div>
        </div>
      </main>
    </div>
  )
}
