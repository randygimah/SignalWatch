import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'

import App from './App'

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  )
}

test('shows the API connection state', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok', service: 'signalwatch-api', version: '0.1.0' }),
    }),
  )

  renderApp()

  expect(screen.getByRole('heading', { name: 'SignalWatch' })).toBeInTheDocument()
  expect(await screen.findByText('Analysis service online · v0.1.0')).toBeInTheDocument()
})

