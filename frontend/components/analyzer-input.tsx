"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Search, ArrowRight, Upload, Video } from "lucide-react";

export function AnalyzerInput() {
  const [url, setUrl] = useState("");
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    // Route to the analysis page with the URL
    router.push(`/analyze?url=${encodeURIComponent(url)}`);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // In a real app, this would upload the file or create a local blob URL
      // For the demo, we route to analysis with the filename
      router.push(`/analyze?mode=upload&file=${encodeURIComponent(file.name)}`);
    }
  };

  const handleWebcam = () => {
    // Live webcam analyzer is its own route with the realtime pipeline
    router.push("/live");
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="relative w-full max-w-3xl mx-auto mt-10"
    >
      <form onSubmit={handleSubmit} className="relative flex items-center w-full rounded-full border border-slate-200 bg-white shadow-xl shadow-slate-200/50 p-2 overflow-hidden focus-within:ring-2 focus-within:ring-slate-400 focus-within:border-transparent transition-all">
        <Search className="absolute left-6 text-slate-400 h-5 w-5" />
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
          disabled={!url.trim()}
          className="absolute right-2 top-2 bottom-2 flex items-center gap-2 rounded-full bg-slate-900 px-6 font-medium text-white transition-all hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Analyze <ArrowRight className="h-4 w-4" />
        </button>
      </form>
      
      <div className="flex items-center justify-center gap-4 mt-6">
        <div className="h-px w-12 bg-slate-200"></div>
        <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Or</span>
        <div className="h-px w-12 bg-slate-200"></div>
      </div>

      <div className="flex items-center justify-center gap-4 mt-4">
        <button 
          onClick={() => fileInputRef.current?.click()}
          type="button"
          className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition-all hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm"
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
