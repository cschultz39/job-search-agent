const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getMetrics() {
    const res = await fetch(`${API_URL}/metrics`)
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return res.json();
}

export async function getWeeklyHistory() {
    const res = await fetch(`${API_URL}/history`)
    if (!res.ok) throw new Error("Failed to fetch history");
    return res.json();
}

