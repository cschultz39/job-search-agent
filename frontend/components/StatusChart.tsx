"use client";

import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { STATUS_COLORS, STATUS_LABELS, STATUS_ORDER } from "@/lib/statusColors";

type WeeklySnapshot = { week_of: string } & Record<string, number | string>;

function SingleStatusTooltip({ active, payload, label, hoveredStatus }: any) {
    if (!active || !hoveredStatus || !payload) return null;
    const hoveredEntry = payload.find((p: any) => p.dataKey === hoveredStatus);
    if (!hoveredEntry) return null;

    const grouped = payload.filter((p: any) => Math.abs(p.value - hoveredEntry.value) <= 10);
  
    return (
      <div style={{ background: "#fff", border: "2px solid var(--color-line)", borderRadius: 0, padding: "6px 10px" }}>
        <p style={{ color: "var(--color-ink)", fontSize: 12, margin: 0 }}>{label}</p>
        {grouped.map((entry: any) => (
            <p key={entry.dataKey} style={{ color: entry.color, fontSize: 12, margin: 0, fontWeight: 600 }}>
            {STATUS_LABELS[entry.dataKey]}: {entry.value}
            </p>
        ))}
      </div>
    );
  }

export default function StatusChart({ data }: { data: WeeklySnapshot[] }) {
    const [hoveredStatus, setHoveredStatus] = useState<string | null>(null);

    return (
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--color-line)" strokeDasharray="0" />
          <XAxis dataKey="week_of" tick={{ fontSize: 11, fill: "var(--color-ink-soft)" }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--color-ink-soft)" }} />
          <Tooltip content={<SingleStatusTooltip hoveredStatus={hoveredStatus} />} />
            {STATUS_ORDER.map((status) => (
            <Line
                key={status}
                type="step"
                dataKey={status}
                name={status}
                stroke={STATUS_COLORS[status].dark}
                strokeWidth={3}
                dot={{ r: 3, fill: STATUS_COLORS[status].dark, strokeWidth: 0 }}
                activeDot={{
                    r: 5,
                    onMouseOver: () => setHoveredStatus(status),
                    onMouseLeave: () => setHoveredStatus(null),
                }}
                isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }