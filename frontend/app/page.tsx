import { getMetrics } from "@/lib/api";

export default async function Home() {
  const metrics = await getMetrics();

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold">Job Search Agent</h1>
      <pre className="mt-4">{JSON.stringify(metrics, null, 2)}</pre>
    </main>
  );
}