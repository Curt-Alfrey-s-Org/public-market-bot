import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/',
  plugins: [react()],
  server: {
    port: 5173,
    open: false,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://localhost:8002',
        changeOrigin: true,
      },
      '/ws': {
        target: (process.env.VITE_API_PROXY || 'http://localhost:8002').replace(/^http/, 'ws'),
        ws: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
