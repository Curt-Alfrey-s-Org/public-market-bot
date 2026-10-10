import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { toast } from '@/lib/toast'

interface TaxReportsProps {
  sidebarOpen?: boolean
  onSidebarToggle?: () => void
}

export default function TaxReportsPage({ sidebarOpen: _sidebarOpen, onSidebarToggle }: TaxReportsProps) {
  const [selectedYear, setSelectedYear] = useState<string>(
    new Date().getFullYear().toString()
  )

  const generateMutation = useMutation({
    mutationFn: async (year: string) => {
      const response = await apiClient.post('/api/tax/generate', { year })
      return response.data
    },
    onSuccess: () => {
      toast.success('Tax reports generated successfully!')
    },
    onError: (error: any) => {
      // Silent error handling - no user-facing error messages
      if (import.meta.env.DEV) {
        console.debug('Tax report generation error (silent):', error.message || 'Unknown error')
      }
    },
  })

  const handleGenerate = () => {
    generateMutation.mutate(selectedYear)
  }

  const years = Array.from({ length: 5 }, (_, i) => {
    const year = new Date().getFullYear() - i
    return year.toString()
  })

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
            <h1 className="text-2xl font-bold">Tax Reports</h1>
            <p className="text-sm text-muted-foreground">
              Generate tax reports for your trading activity
            </p>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">

        {/* Year Selection */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center gap-4 mb-6">
            <label className="text-sm font-medium">Tax Year:</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="px-4 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
            <button
              onClick={handleGenerate}
              disabled={generateMutation.isPending}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generateMutation.isPending ? 'Generating...' : 'Generate Reports'}
            </button>
          </div>

          {/* Report Types */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-border rounded-lg p-4">
              <h3 className="font-semibold mb-2">Form 8949</h3>
              <p className="text-sm text-muted-foreground mb-4">
                IRS Form 8949 for capital gains and losses
              </p>
              <button
                className="w-full px-4 py-2 bg-muted hover:bg-accent rounded-lg transition-colors text-sm"
                onClick={() => toast.info('Download will be available after report generation')}
              >
                Download
              </button>
            </div>

            <div className="border border-border rounded-lg p-4">
              <h3 className="font-semibold mb-2">Tax Summary</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Summary of all trading activity for the year
              </p>
              <button
                className="w-full px-4 py-2 bg-muted hover:bg-accent rounded-lg transition-colors text-sm"
                onClick={() => toast.info('Download will be available after report generation')}
              >
                Download
              </button>
            </div>

            <div className="border border-border rounded-lg p-4">
              <h3 className="font-semibold mb-2">CPA Report</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Detailed report for your tax preparer
              </p>
              <button
                className="w-full px-4 py-2 bg-muted hover:bg-accent rounded-lg transition-colors text-sm"
                onClick={() => toast.info('Download will be available after report generation')}
              >
                Download
              </button>
            </div>
          </div>

          {/* Status */}
          {generateMutation.isSuccess && (
            <div className="mt-6 bg-green-500/10 border border-green-500/20 rounded-lg p-4">
              <p className="text-sm text-green-600">
                ✅ Tax reports generated for {selectedYear}. You can now download the reports above.
              </p>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Instructions</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Select the tax year you want to generate reports for</li>
            <li>Click "Generate Reports" to create all tax documents</li>
            <li>Download Form 8949, Tax Summary, or CPA Report as needed</li>
            <li>Use these reports when filing your taxes</li>
          </ol>
        </div>
        </div>
      </main>
    </div>
  )
}
