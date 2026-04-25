"use client";

import { useSearchParams } from "next/navigation";
import { useState, useEffect, useRef, Suspense } from "react";
import { LoadingPipeline } from "@/components/loading-pipeline";
import { ResultDashboard } from "@/components/result-dashboard";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const POLL_MS = 2500;
const MAX_POLLS = 120; // 5 minutes max

type JobPhase = "queued" | "downloading" | "extracting" | "scoring" | "synthesizing" | "completed" | "failed";

interface JobStatus {
  job_id: string;
  status: JobPhase;
  error?: string;
}

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const url = searchParams?.get("url") ?? "";

  // null = still processing, string = result_id or "mock", object = inline result payload
  const [resultPayload, setResultPayload] = useState<Record<string, unknown> | null>(null);
  const [jobStatus, setJobStatus] = useState<JobPhase>("queued");
  const [error, setError] = useState<string | null>(null);
  const pollCount = useRef(0);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!url) return;

    let cancelled = false;

    async function startJob() {
      try {
        const res = await fetch(`${API_BASE}/api/analyze/url`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        });

        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        const job: { job_id: string; status: JobPhase } = await res.json();
        if (!cancelled) pollJob(job.job_id);
      } catch (err) {
        if (!cancelled) {
          console.warn("Backend unreachable, using archive fallback:", err);
          // Backend is offline — show archive/fallback immediately
          setResultPayload({ _fallback: true, url });
        }
      }
    }

    async function pollJob(jobId: string) {
      if (cancelled) return;

      // Respect max poll budget
      if (pollCount.current >= MAX_POLLS) {
        setError("Analysis timed out. The video may be too long or the backend is overloaded.");
        return;
      }
      pollCount.current += 1;

      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
        if (!res.ok) throw new Error(`Poll failed: ${res.status}`);
        const status: JobStatus = await res.json();

        if (!cancelled) setJobStatus(status.status);

        if (status.status === "completed") {
          // Fetch full result payload
          const resultRes = await fetch(`${API_BASE}/api/jobs/${jobId}/result`);
          if (!resultRes.ok) throw new Error("Failed to fetch result");
          const payload = await resultRes.json();
          if (!cancelled) setResultPayload(payload);
          return;
        }

        if (status.status === "failed") {
          if (!cancelled) setError(status.error ?? "Analysis failed in backend.");
          return;
        }

        // Still running — schedule next poll
        pollTimer.current = setTimeout(() => pollJob(jobId), POLL_MS);
      } catch (err) {
        if (!cancelled) {
          console.error("Poll error:", err);
          setError("Lost connection to backend during analysis.");
        }
      }
    }

    startJob();

    return () => {
      cancelled = true;
      if (pollTimer.current) clearTimeout(pollTimer.current);
    };
  }, [url]);

  if (!url) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-serif mb-4 text-slate-900">No URL provided</h2>
        <Link href="/" className="text-blue-500 hover:underline">Return home</Link>
      </div>
    );
  }

  return (
    <>
      {resultPayload && (
        <div className="mb-6">
          <Link href="/" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 transition-colors">
            <ArrowLeft className="h-4 w-4" /> Analyze another video
          </Link>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <strong>Error:</strong> {error}
          <div className="mt-2">
            <Link href="/" className="underline">← Try another video</Link>
          </div>
        </div>
      )}

      {!resultPayload && !error ? (
        <LoadingPipeline phase={jobStatus} onComplete={() => {}} />
      ) : (
        resultPayload && <ResultDashboard url={url} livePayload={resultPayload._fallback ? undefined : resultPayload} />
      )}
    </>
  );
}

export default function AnalyzePage() {
  return (
    <div className="w-full">
      <Suspense fallback={<div className="py-20 text-center">Loading...</div>}>
        <AnalyzeContent />
      </Suspense>
    </div>
  );
}
