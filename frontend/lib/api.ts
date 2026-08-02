const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getMetrics() {
    const res = await fetch(`${API_URL}/metrics`)
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return res.json();
}