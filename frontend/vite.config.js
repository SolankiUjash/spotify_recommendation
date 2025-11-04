import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: ['spotify.ujash.live'],
    hmr: {
      protocol: 'wss',
      host: 'spotify.ujash.live',
      clientPort: 443,
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Ensure Spotify redirects to /callback hit the backend FastAPI app
      '/callback': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})


