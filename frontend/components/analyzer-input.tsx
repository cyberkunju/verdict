"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Loader2, Search, Upload, Video } from "lucide-react";

import type { AnalyzeAcceptedResponse } from "@/lib/types";

export function AnalyzerInput() {
  const [url, setUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    router.push(`/analyze?url=${encodeURIComponent(url)}`);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/analyze/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      const accepted = (await res.json()) as AnalyzeAcceptedResponse;
      router.push(`/analyze?job=${encodeURIComponent(accepted.job_id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsSubmitting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleWebcam = () => {
    router.push("/live");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="relative mx-auto mt-10 w-full max-w-3xl"
    >
      <form
        onSubmit={handleSubmit}
        className="relative flex w-full items-center overflow-hidden rounded-full border border-slate-200 bg-white p-2 shadow-xl shadow-slate-200/50 transition-all focus-within:border-transparent focus-within:ring-2 focus-within:ring-slate-400"
      >
        <Search className="absolute left-6 h-5 w-5 text-slate-400" />
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste any YouTube URL or video link..."
          className="w-full bg-transparent py-4 pl-14 pr-32 text-lg text-slate-900 placeholder:text-slate-400 focus:outline-none"
          required
        />
        <button
          type="submit"
          disabled={!url.trim() || isSubmitting}
          className="absolute bottom-2 right-2 top-2 flex items-center gap-2 rounded-full bg-slate-900 px-6 font-medium text-white transition-all hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              Analyze <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </form>

      <div className="mt-6 flex items-center justify-center gap-4">
        <div className="h-px w-12 bg-slate-200" />
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Or</span>
        <div className="h-px w-12 bg-slate-200" />
      </div>

      <div className="mt-4 flex items-center justify-center gap-4">
        <button
          onClick={() => fileInputRef.current?.click()}
          type="button"
          disabled={isSubmitting}
          className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition-all hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Upload className="h-4 w-4 text-slate-500" />
          Upload Video
        </button>
        <button
          onClick={handleWebcam}
          type="button"
          className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition-all hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm"
        >
          <Video className="h-4 w-4 text-slate-500" />
          Use Webcam
        </button>
      </div>

      <p className="mt-4 text-center text-xs text-slate-500">
        Video URL and upload modes both run through the same backend pipeline and include VerdictTextPrior-v1 statement scoring.
      </p>

      {error ? <p className="mt-3 text-center text-sm text-red-600">{error}</p> : null}

      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="video/*"
        onChange={handleFileUpload}
      />
    </motion.div>
  );
}
