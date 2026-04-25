"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { LoadingPipeline } from "@/components/loading-pipeline";
import { ResultDashboard } from "@/components/result-dashboard";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";

import type { AnalysisResultResponse, JobStatusResponse } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams?.get("job") || "";
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout> | undefined;

    async function pollJob() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, { cache: "no-store" });
        if (!response.ok) throw new Error("Unable to fetch job status.");
        const nextJob = (await response.json()) as JobStatusResponse;
        if (cancelled) return;
        setJob(nextJob);

        if (nextJob.status === "completed") {
          const resultResponse = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/result`, { cache: "no-store" });
          if (!resultResponse.ok) throw new Error("Unable to fetch analysis result.");
          const nextResult = (await resultResponse.json()) as AnalysisResultResponse;
          if (!cancelled) setResult(nextResult);
          return;
        }

        if (nextJob.status === "failed") {
          if (!cancelled) setError(nextJob.error || "Analyzer job failed.");
          return;
        }

        timeout = setTimeout(pollJob, 1800);
      } catch (pollError) {
        if (!cancelled) setError(pollError instanceof Error ? pollError.message : "Polling failed.");
      }
    }

    void pollJob();

    return () => {
      cancelled = true;
      if (timeout) clearTimeout(timeout);
    };
  }, [jobId]);

  if (!jobId) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-serif mb-4 text-slate-900">No analysis job provided</h2>
        <Link href="/" className="text-blue-500 hover:underline">Return home</Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
        <h2 className="font-serif text-2xl text-red-900">Analysis failed</h2>
        <p className="mt-3 text-sm text-red-700">{error}</p>
        <Link href="/" className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-red-800 hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to analyzer
        </Link>
      </div>
    );
  }

  return (
    <>
      {result && (
        <div className="mb-6">
          <Link href="/" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 transition-colors">
            <ArrowLeft className="h-4 w-4" /> Analyze another video
          </Link>
        </div>
      )}
      
      {result ? (
        <ResultDashboard payload={result.payload} />
      ) : (
        <>
          {job ? <LoadingPipeline status={job.status} /> : <div className="flex items-center justify-center gap-3 py-24 text-slate-500"><Loader2 className="h-5 w-5 animate-spin" /> Connecting to backend...</div>}
        </>
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
