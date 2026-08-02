type Metrics = Record<string, number>;

const TILES = [
  { key: "not applied", label: "not applied", c1: "var(--color-emerald)", c2: "var(--color-emerald-d)", c3: "var(--color-gold)" },
  { key: "applied", label: "applied", c1: "var(--color-garnet)", c2: "var(--color-garnet-d)", c3: "var(--color-gold)" },
  { key: "oa", label: "oa", c1: "var(--color-gold)", c2: "var(--color-gold-d)", c3: "var(--color-emerald)" },
  { key: "behavioral interview", label: "behavioral", c1: "var(--color-teal)", c2: "var(--color-teal-d)", c3: "var(--color-gold)" },
  { key: "technical interview", label: "technical", c1: "var(--color-plum)", c2: "var(--color-plum-d)", c3: "var(--color-gold)" },
  { key: "offer", label: "offer", c1: "var(--color-emerald-d)", c2: "var(--color-emerald)", c3: "var(--color-gold)" },
  { key: "rejected", label: "rejected", c1: "var(--color-garnet-d)", c2: "var(--color-garnet)", c3: "var(--color-gold)" },
  { key: "withdrawn", label: "withdrawn", c1: "var(--color-teal-d)", c2: "var(--color-teal)", c3: "var(--color-gold)" },
];

export default function MetricsTiles({ data }: { data: Metrics }) {
  return (
    <div className="grid grid-cols-4 gap-3 mb-6">
      {TILES.map((t) => (
        <div key={t.key} className="tile" style={{ ["--c1" as any]: t.c1, ["--c2" as any]: t.c2, ["--c3" as any]: t.c3 }}>
          <div className="font-serif font-bold text-2xl relative">{data[t.key] ?? 0}</div>
          <div className="text-[9.5px] uppercase tracking-wide opacity-90 mt-1 relative">{t.label}</div>
        </div>
      ))}
    </div>
  );
}