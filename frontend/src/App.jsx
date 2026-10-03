import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import AppRoutes from './routes'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // One user: refetching on every window focus is noise, and the data
      // changes when this person changes it.
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
