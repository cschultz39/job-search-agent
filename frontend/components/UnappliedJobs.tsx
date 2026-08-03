"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { markApplied, markNotInterested } from "@/lib/api";
import JobCard from "@/components/JobCard";

type Job = {
    id: string;
    company: string;
    title: string;
    location: string;
    link: string;
    relevance_score?: number;
    relevance_reason?: string;
};

export default function UnappliedJobs({ initialJobs }: { initialJobs: Job[] }) {
  const [jobs, setJobs] = useState(initialJobs);
  const [pendingAction, setPendingAction] = useState<{ id: string; action: "applied" | "not-interested" } | null>(null);
  const router = useRouter();

  useEffect(() => {
    setJobs(initialJobs);
  }, [initialJobs]);

  async function handleMarkApplied(jobId: string) {
    setPendingAction({ id: jobId, action: "applied" });
    try {
      await markApplied(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      router.refresh();
    } catch (err) {
      console.error(err);
    } finally {
      setPendingAction(null);
    }
  }
  
  async function handleMarkNotInterested(jobId: string) {
    setPendingAction({ id: jobId, action: "not-interested" });
    try {
      await markNotInterested(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      router.refresh();
    } catch (err) {
      console.error(err);
    } finally {
      setPendingAction(null);
    }
  }
  
    if (jobs.length === 0) {
      return <p className="text-sm text-ink-soft">No unapplied jobs — nice, you're caught up!</p>;
    }

    return (
      <div>
        {jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            pendingApplied={pendingAction?.id === job.id && pendingAction.action === "applied"}
            pendingNotInterested={pendingAction?.id === job.id && pendingAction.action === "not-interested"}
            onMarkApplied={handleMarkApplied}
            onMarkNotInterested={handleMarkNotInterested}
          />
        ))}
      </div>
  );
}