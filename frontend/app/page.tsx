import MetricsTiles from "@/components/MetricsTiles";
import { getMetrics } from "@/lib/api";

import StatusChart from "@/components/StatusChart";
import { getWeeklyHistory } from "@/lib/api";

import UnappliedJobs from "@/components/UnappliedJobs";
import { getUnappliedJobs } from "@/lib/api";

import ChatWidget from "@/components/ChatWidget";

export default async function Home() {
  const metrics = await getMetrics();
  const weeklyHistory = await getWeeklyHistory();
  const unappliedJobs = await getUnappliedJobs();

  return (
    <main className="max-w-295 mx-auto px-10 py-8">
      <h1
        className="font-pixel font-bold text-3xl text-heading mb-8"
        style={{ textShadow: "2px 2px 0 var(--color-line)" }}
      >
        welcome back to the job search!
      </h1>

      <h2 className="font-pixel font-semibold text-lg text-heading-light mb-4">status metrics</h2>
      <MetricsTiles data={metrics} />

      <div className="grid grid-cols-[1.4fr_1fr] gap-4 mt-6">
        <div>
        <h2 className="font-pixel font-semibold text-lg text-heading-light mb-4">status history</h2>
          <div className="card">
          <StatusChart data={weeklyHistory} />
          </div>
        </div>

        <div>
          <h2 className="font-pixel font-semibold text-lg text-heading-light mb-4">top unapplied</h2>
          <div className="card" style={{ height: 312, overflowY: "auto", padding: "14px 16px" }}>
            <UnappliedJobs initialJobs={unappliedJobs} />
          </div>
        </div>
      </div>
      <ChatWidget />
    </main>
  );
}