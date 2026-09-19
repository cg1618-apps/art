import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// outDir is outside frontend/ because uvicorn serves the built bundle from the
// repository root. port 5176 and the 8003 proxy are this app's slots in the
// box-wide allocation: uvicorn = the app's registry port, Vite = 5173 + (port
// - 8000), so all four apps run at once without collisions.
export default defineConfig({
  plugins: [react()],
  build: { outDir: '../frontend_dist', emptyOutDir: true },
  server: {
    port: 5176,
    strictPort: true,
    // Both prefixes: this app's health path is /health, not /api/health, so
    // proxying /api alone would leave the dev server answering it with the SPA.
    proxy: {
      '/api': 'http://localhost:8003',
      '/health': 'http://localhost:8003',
    },
  },
})
