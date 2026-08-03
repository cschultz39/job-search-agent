"use client";

import { useState } from "react";
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
    const [pendingId, setPendingId] = useState<string | null>(null);
  
    async function handleMarkApplied(jobId: string) {
      setPendingId(jobId);
      try {
        await markApplied(jobId);
        setJobs((prev) => prev.filter((j) => j.id !== jobId));
      } catch (err) {
        console.error(err);
      } finally {
        setPendingId(null);
      }
    }

    async function handleMarkNotInterested(jobId: string) {
      setPendingId(jobId);
      try {
        await markNotInterested(jobId);
        setJobs((prev) => prev.filter((j) => j.id !== jobId));
      } catch (err) {
        console.error(err);
      } finally {
        setPendingId(null);
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
          pending={pendingId === job.id}
          onMarkApplied={handleMarkApplied}
          onMarkNotInterested={handleMarkNotInterested}
        />
        ))}
      </div>
  );
}