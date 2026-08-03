"use client";

type Job = {
  id: string;
  company: string;
  title: string;
  location: string;
  link: string;
  relevance_score?: number;
  relevance_reason?: string;
};

type JobCardProps = {
  job: Job;
  pending: boolean;
  onMarkApplied: (jobId: string) => void;
};

export default function JobCard({ job, pending, onMarkApplied }: JobCardProps) {
  return (
    <div style={{ borderBottom: "2px solid var(--color-line)", padding: "10px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p className="font-semibold text-sm" style={{ color: "var(--color-ink)", margin: 0 }}>
            {job.company}
          </p>
          <p className="text-sm" style={{ color: "var(--color-ink)", margin: 0 }}>
            {job.title}
          </p>
          <p className="text-xs" style={{ color: "var(--color-ink-soft)", margin: "8px 0 0" }}>
            location: {job.location}<br />
            score: {job.relevance_score ?? "?"}
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end", flexShrink: 0 }}>
          <a href={job.link} target="_blank" rel="noopener noreferrer">
            <button
              className="font-pixel"
              style={{
                fontSize: 7,
                width: 96,
                background: "var(--color-oa)",
                color: "#fff",
                border: "3px solid var(--color-oa-d)",
                padding: "6px 8px",
                cursor: "pointer",
              }}
            >
              APPLY HERE
            </button>
          </a>
          <button
            onClick={() => onMarkApplied(job.id)}
            disabled={pending}
            className="font-pixel"
            style={{
              fontSize: 7,
              width: 96,
              background: "var(--color-not-applied)",
              color: "#fff",
              border: "3px solid var(--color-not-applied-d)",
              padding: "6px 8px",
              cursor: pending ? "default" : "pointer",
              opacity: pending ? 0.6 : 1,
            }}
          >
            {pending ? "..." : "MARK APPLIED"}
          </button>
        </div>
      </div>
    </div>
  );
}