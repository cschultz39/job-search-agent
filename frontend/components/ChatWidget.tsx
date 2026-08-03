"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { sendChatMessage, markApplied, markNotInterested } from "@/lib/api";
import JobCard from "@/components/JobCard";

type Job = {
  id: string;
  company: string;
  title: string;
  location: string;
  link: string;
  relevance_score?: number;
  relevance_reason?: string;
  status?: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  jobs?: Job[];
};

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState<{ key: string; action: "applied" | "not-interested" } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res = await sendChatMessage(text, conversationHistory);
      setConversationHistory(res.conversation_history);
      setMessages((prev) => [...prev, { role: "assistant", content: res.text, jobs: res.jobs }]);
      router.refresh();
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong reaching the agent." }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleMarkApplied(msgIndex: number, jobId: string) {
    const key = `${msgIndex}_${jobId}`;
    setPendingAction({ key, action: "applied" });
    try {
      await markApplied(jobId);
      setMessages((prev) =>
        prev.map((m, i) =>
          i === msgIndex && m.jobs
            ? { ...m, jobs: m.jobs.map((j) => (j.id === jobId ? { ...j, status: "applied" } : j)) }
            : m
        )
      );
      router.refresh();
    } catch (err) {
      console.error(err);
    } finally {
      setPendingAction(null);
    }
  }

  async function handleMarkNotInterested(msgIndex: number, jobId: string) {
    const key = `${msgIndex}_${jobId}`;
    setPendingAction({ key, action: "not-interested" });
    try {
      await markNotInterested(jobId);
      setMessages((prev) =>
        prev.map((m, i) =>
          i === msgIndex && m.jobs
            ? { ...m, jobs: m.jobs.filter((j) => j.id !== jobId) }
            : m
        )
      );
      router.refresh();
    } catch (err) {
      console.error(err);
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <div style={{ position: "fixed", bottom: 12, right: 15, zIndex: 999, display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
      {open && (
        <div
          className="card"
          style={{
            width: 340,
            height: 440,
            marginBottom: 12,
            display: "flex",
            flexDirection: "column",
            padding: 0,
            overflow: "hidden",
          }}
        >
          <div
            className="font-pixel"
            style={{
              fontSize: 11,
              color: "#fff",
              background: "var(--color-heading-light)",
              padding: "10px 14px",
              borderBottom: "4px solid var(--color-heading)",
            }}
          >
            job search assistant
          </div>

          <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "12px 14px" }}>
            {messages.length === 0 && (
              <p className="text-xs" style={{ color: "var(--color-ink-soft)" }}>
                Ask about your saved jobs, or tell me to mark one applied.
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  marginBottom: 14,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: m.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <p
                  className="text-xs font-semibold"
                  style={{ color: m.role === "user" ? "var(--color-heading)" : "var(--color-technical-d)", margin: "0 0 2px" }}
                >
                  {m.role === "user" ? "you" : "agent"}
                </p>
                <div
                  className="text-sm"
                  style={{
                    background: m.role === "user" ? "var(--color-heading-light)" : "var(--color-technical)",
                    color: "#fff",
                    padding: "8px 12px",
                    maxWidth: "85%",
                    whiteSpace: "pre-wrap",
                    border: `2px solid ${m.role === "user" ? "var(--color-heading)" : "var(--color-technical-d)"}`,
                    boxShadow: `3px 3px 0 ${m.role === "user" ? "var(--color-heading)" : "var(--color-technical-d)"}`,
                  }}
                >
                  {m.content}
                </div>
                {m.jobs && m.jobs.length > 0 && (
                  <div style={{ marginTop: 8, width: "100%" }}>
                    {m.jobs
                      .filter((j) => (j.status ?? "not applied").toLowerCase() !== "applied")
                      .map((j) => (
                        <JobCard
                          key={j.id}
                          job={j}
                          pendingApplied={pendingAction?.key === `${i}_${j.id}` && pendingAction.action === "applied"}
                          pendingNotInterested={pendingAction?.key === `${i}_${j.id}` && pendingAction.action === "not-interested"}
                          onMarkApplied={(jobId) => handleMarkApplied(i, jobId)}
                          onMarkNotInterested={(jobId) => handleMarkNotInterested(i, jobId)}
                        />
                      ))}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <p className="text-xs" style={{ color: "var(--color-ink-soft)" }}>
                thinking...
              </p>
            )}
          </div>

          <div style={{ display: "flex", borderTop: "3px solid var(--color-line)", padding: 8, gap: 6 }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about your saved jobs..."
              className="text-sm"
              style={{ flex: 1, border: "2px solid var(--color-line)", padding: "6px 8px", outline: "none" }}
            />
            <button
              onClick={handleSend}
              disabled={loading}
              className="font-pixel"
              style={{
                fontSize: 8,
                background: "var(--color-heading-light)",
                color: "#fff",
                border: "3px solid var(--color-heading)",
                boxShadow: "2px 2px 0 var(--color-heading)",
                padding: "6px 10px",
                cursor: loading ? "default" : "pointer",
              }}
            >
              go
            </button>
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: 56,
          height: 56,
          borderRadius: "50%",
          background: "var(--color-heading-light)",
          color: "#fff",
          border: "4px solid var(--color-heading)",
          boxShadow: "3px 3px 0 var(--color-heading)",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {open ? (
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 4L20 20M20 4L4 20" strokeLinecap="square" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M2 2H22V16H7V18H4V20H3V16H2V2Z" strokeLinejoin="miter" />
          </svg>
        )}
      </button>
    </div>
  );
}