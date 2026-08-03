import { useQuery } from '@tanstack/react-query'

import { getHealth } from './api'

function StatusIndicator() {
  const health = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    retry: 1,
  })

  if (health.isPending) {
    return <p className="font-mono text-sm text-slate-500">Connecting to analysis service…</p>
  }

  if (health.isError) {
    return (
      <p role="alert" className="font-mono text-sm text-red-700">
        Analysis service unavailable
      </p>
    )
  }

  return (
    <div className="flex items-center gap-2 font-mono text-sm text-slate-600">
      <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" aria-hidden="true" />
      Analysis service online · v{health.data.version}
    </div>
  )
}

export default function App() {
  return (
    <main className="min-h-screen bg-[#f9f9ff] px-6 py-12 text-[#111c2d] md:px-10">
      <section className="mx-auto max-w-6xl">
        <header className="mb-10 flex items-center justify-between border-b border-[#c2c6d6] pb-5">
          <div>
            <p className="mb-1 font-mono text-xs uppercase tracking-[0.16em] text-[#0058be]">
              RF intelligence
            </p>
            <h1 className="m-0 text-3xl font-bold tracking-tight">SignalWatch</h1>
          </div>
          <StatusIndicator />
        </header>

        <div className="rounded-lg border border-[#c2c6d6] bg-white p-8 shadow-[0_4px_12px_rgba(30,41,59,0.05)]">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
            Foundation ready
          </p>
          <h2 className="mb-3 text-2xl font-semibold">RF anomaly dashboard</h2>
          <p className="m-0 max-w-2xl leading-7 text-slate-600">
            The application shell is connected. Synthetic observations, anomaly scoring, incident
            explanations, and interactive analysis arrive in the next phases.
          </p>
        </div>
      </section>
    </main>
  )
}

