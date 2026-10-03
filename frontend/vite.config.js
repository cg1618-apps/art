import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// outDir is outside frontend/ because uvicorn serves the built bundle from the
// repository root. port 5176 and the 8003 proxy are this app's slots in the
// box-wide allocation: uvicorn = the app's registry port, Vite = 5173 + (port
// - 8000), so all four apps run at once without collisions.
export default defineConfig({
  plugins: [react(), tailwindcss()],
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
  // The automatic JSX runtime under vitest, as food's: Vite 8 compiles the app
  // with oxc, vitest 3 still transforms with esbuild, whose default is the
  // classic runtime. Set only under vitest, because vite warns when a build
  // sees both options.
  ...(process.env.VITEST ? { esbuild: { jsx: 'automatic' } } : {}),
  test: {
    environment: 'jsdom',
    globals: false,
    include: ['src/**/*.test.{js,jsx}'],
  },
})
