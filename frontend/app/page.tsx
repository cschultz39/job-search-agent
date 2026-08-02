import { getMetrics } from "@/lib/api";
import MetricsTiles from "@/components/MetricsTiles";

import StatusChart from "@/components/StatusChart";
import { getWeeklyHistory } from "@/lib/api";

export default async function Home() {
  const metrics = await getMetrics();
  const weeklyHistory = await getWeeklyHistory();

  return (
    <main className="max-w-[1180px] mx-auto px-10 py-8">
      <h1
        className="font-pixel font-bold text-3xl text-[color:var(--color-heading)] mb-8"
        style={{ textShadow: "2px 2px 0 var(--color-line)" }}
      >
        job search agent
      </h1>

      <h2 className="font-pixel font-semibold text-lg text-[color:var(--color-heading-light)] mb-4">status metrics</h2>
      <MetricsTiles data={metrics} />

      <div className="grid grid-cols-[1.4fr_1fr] gap-4 mt-6">
        <div>
        <h2 className="font-pixel font-semibold text-lg text-[color:var(--color-heading-light)] mb-4">status history</h2>
          <div className="card">
          <StatusChart data={weeklyHistory} />
          </div>
        </div>

        <div>
          <h2 className="font-pixel font-semibold text-lg text-[color:var(--color-heading-light)] mb-4">top unapplied</h2>
          <div className="card">
            <p className="text-sm text-[color:var(--color-ink-soft)]">Job list wired up in the next step.</p>
          </div>
        </div>
      </div>
    </main>
  );
}