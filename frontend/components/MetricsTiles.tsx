import { STATUS_COLORS, STATUS_LABELS, STATUS_ORDER } from "@/lib/statusColors";

type Metrics = Record<string, number>;

export default function MetricsTiles({ data }: { data: Metrics }) {
  return (
    <div className="grid grid-cols-8 gap-3 mb-6">
      {STATUS_ORDER.map((status) => (
        <div
          key={status}
          className="tile"
          style={{ ["--c1" as any]: STATUS_COLORS[status].fill, ["--c1-d" as any]: STATUS_COLORS[status].dark }}
        >
          <div className="font-sans font-bold text-2xl relative">{data[status] ?? 0}</div>
          <div className="text-[9.5px] uppercase tracking-wide opacity-90 mt-1 relative">{STATUS_LABELS[status]}</div>
        </div>
      ))}
    </div>
  );
}