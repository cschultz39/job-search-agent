import { getMetrics } from "@/lib/api";
import MetricsTiles from "@/components/MetricsTiles";

export default async function Home() {
  const metrics = await getMetrics();

  return (
    <main className="max-w-[1180px] mx-auto px-10 py-8">
      <h1 className="font-serif font-bold text-3xl text-[color:var(--color-heading)] mb-8">Job Search Agent</h1>

      <div className="grid grid-cols-2 gap-8">
        <div>
          <h2 className="font-serif font-semibold text-lg text-[color:var(--color-heading)] mb-4">Metrics</h2>
          <MetricsTiles data={metrics} />
          <div className="card">
            <p className="font-semibold text-sm text-[color:var(--color-ink-soft)] mb-3">
              Status breakdown over time (weekly)
            </p>
            <p className="text-sm text-[color:var(--color-ink-soft)]">Chart wired up in the next step.</p>
          </div>
        </div>

        <div>
          <h2 className="font-serif font-semibold text-lg text-[color:var(--color-heading)] mb-4">Top 10 unapplied jobs</h2>
          <div className="card">
            <p className="text-sm text-[color:var(--color-ink-soft)]">Job list wired up in the next step.</p>
          </div>
        </div>
      </div>
    </main>
  );
}