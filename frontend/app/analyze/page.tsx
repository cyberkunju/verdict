"use client";

import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { LoadingPipeline } from "@/components/loading-pipeline";
import { ResultDashboard } from "@/components/result-dashboard";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const url = searchParams?.get("url") || "";
  const [isProcessing, setIsProcessing] = useState(true);

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
      {!isProcessing && (
        <div className="mb-6">
          <Link href="/" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 transition-colors">
            <ArrowLeft className="h-4 w-4" /> Analyze another video
          </Link>
        </div>
      )}
      
      {isProcessing ? (
        <LoadingPipeline onComplete={() => setIsProcessing(false)} />
      ) : (
        <ResultDashboard url={url} />
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
