"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { LoadingPipeline } from "@/components/loading-pipeline";
import { ResultDashboard } from "@/components/result-dashboard";
import type { AnalysisResultResponse, JobStatusResponse, LiveAnalysisPayload } from "@/lib/types";

const POLL_MS = 2500;
const MAX_POLLS = 480;

type JobPhase =
  | "queued"
  | "downloading"
  | "trimming"
  | "extracting"
  | "scoring"
  | "synthesizing"
  | "completed"
  | "failed";

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const url = searchParams?.get("url") ?? "";
  const existingJobId = searchParams?.get("job") ?? "";

  const [resultPayload, setResultPayload] = useState<LiveAnalysisPayload | null>(null);
  const [jobStatus, setJobStatus] = useState<JobPhase>("queued");
  const [error, setError] = useState<string | null>(null);
  const [fallbackMode, setFallbackMode] = useState(false);
  const pollCount = useRef(0);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!url && !existingJobId) return;

    let cancelled = false;

    async function pollJob(jobId: string) {
      if (cancelled) return;
      if (pollCount.current >= MAX_POLLS) {
        setError("Analysis timed out. The video may be too long or the backend is overloaded.");
        return;
      }
      pollCount.current += 1;

      try {
        const res = await fetch(`/api/jobs/${jobId}`, { cache: "no-store" });
        if (!res.ok) throw new Error(`Poll failed: ${res.status}`);
        const status = (await res.json()) as JobStatusResponse;
        if (!cancelled) setJobStatus(status.status as JobPhase);

        if (status.status === "completed") {
          const resultRes = await fetch(`/api/jobs/${jobId}/result`, { cache: "no-store" });
          if (!resultRes.ok) throw new Error("Failed to fetch result");
          const result = (await resultRes.json()) as AnalysisResultResponse;
          if (!cancelled) setResultPayload(result.payload);
          return;
        }

        if (status.status === "failed") {
          if (!cancelled) setError(status.error ?? "Analysis failed in backend.");
          return;
        }

        pollTimer.current = setTimeout(() => pollJob(jobId), POLL_MS);
      } catch (err) {
        if (!cancelled) {
          console.error("Poll error:", err);
          setError("Lost connection to backend during analysis.");
        }
      }
    }

    async function startJobFromUrl() {
      try {
        const res = await fetch(`/api/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        });
        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        const accepted = (await res.json()) as { job_id: string };
        if (!cancelled) pollJob(accepted.job_id);
      } catch (err) {
        if (!cancelled) {
          console.warn("Backend unreachable, using archive fallback:", err);
          setFallbackMode(true);
        }
      }
    }

    if (existingJobId) {
      void pollJob(existingJobId);
    } else {
      void startJobFromUrl();
    }

    return () => {
      cancelled = true;
      if (pollTimer.current) clearTimeout(pollTimer.current);
    };
  }, [existingJobId, url]);

  if (!url && !existingJobId) {
    return (
      <div className="py-20 text-center">
        <h2 className="mb-4 font-serif text-2xl text-slate-900">No input provided</h2>
        <Link href="/" className="text-blue-500 hover:underline">
          Return home
        </Link>
      </div>
    );
  }

  const hasResult = !!resultPayload || fallbackMode;

  return (
    <>
      {hasResult && (
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-slate-500 transition-colors hover:text-slate-900"
          >
            <ArrowLeft className="h-4 w-4" /> Analyze another video
          </Link>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <strong>Error:</strong> {error}
          <div className="mt-2">
            <Link href="/" className="underline">
              ← Try another video
            </Link>
          </div>
        </div>
      )}

      {!hasResult && !error ? (
        <LoadingPipeline phase={jobStatus} onComplete={() => {}} />
      ) : (
        <ResultDashboard url={url || resultPayload?.video_url || ""} livePayload={resultPayload ?? undefined} />
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
