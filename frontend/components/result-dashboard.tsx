"use client";

import { motion } from "framer-motion";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { AlertTriangle, Activity, BrainCircuit } from "lucide-react";

// Mock data for the synchronized timeline
const chartData = Array.from({ length: 40 }).map((_, i) => ({
  time: `${Math.floor(i / 10)}:${(i % 10) * 6}0`,
  heartRate: 75 + Math.random() * 40 + (i > 15 && i < 25 ? 35 : 0), // Spike in the middle
  stress: 40 + Math.random() * 20 + (i > 15 && i < 25 ? 40 : 0),
}));

export function ResultDashboard({ url }: { url: string }) {
  // Try to extract YouTube ID for iframe, or show generic video player
  const videoIdMatch = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
  const videoId = videoIdMatch ? videoIdMatch[1] : null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-8"
    >
      <div className="flex flex-col md:flex-row gap-6">
        {/* Left Column: Video & Chart */}
        <div className="flex-1 space-y-6">
          <div className="aspect-video w-full overflow-hidden rounded-2xl bg-slate-900 shadow-lg border border-slate-200">
            {videoId ? (
              <iframe
                className="w-full h-full"
                src={`https://www.youtube.com/embed/${videoId}?autoplay=0&controls=1`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-500">
                Processed Video
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="mb-6 font-serif text-xl font-medium text-slate-900">Synchronized Signal Timeline</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorHr" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorStress" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#cbd5e1" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#cbd5e1" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Area type="monotone" dataKey="heartRate" name="Heart Rate (rPPG)" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorHr)" />
                  <Area type="monotone" dataKey="stress" name="Stress Index" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorStress)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right Column: Scores & Report */}
        <div className="w-full md:w-[380px] space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-2xl border border-red-100 bg-red-50 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <p className="text-xs font-bold uppercase tracking-wider text-red-600/80">Deception</p>
              </div>
              <p className="text-4xl font-bold text-red-700">84</p>
            </div>
            <div className="rounded-2xl border border-blue-100 bg-blue-50 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="h-4 w-4 text-blue-500" />
                <p className="text-xs font-bold uppercase tracking-wider text-blue-600/80">Sincerity</p>
              </div>
              <p className="text-4xl font-bold text-blue-700">22</p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-100">
              <div className="rounded-full bg-slate-100 p-2">
                <BrainCircuit className="h-5 w-5 text-slate-700" />
              </div>
              <div>
                <h3 className="font-serif text-lg font-medium text-slate-900">LLM Analyst Synthesis</h3>
                <p className="text-xs text-slate-500">Auto-generated behavioral report</p>
              </div>
            </div>
            <div className="prose prose-sm prose-slate text-slate-600 leading-relaxed">
              <p>
                During the target statement, the subject&apos;s heart rate rose <strong>31 bpm</strong> above their personal baseline. We observed a sustained <strong>AU14 (Contempt)</strong> micro-expression and a complete absence of the Duchenne smile marker (AU6).
              </p>
              <p>
                Linguistic analysis indicates a sharp increase in distancing language and pronoun dropping compared to their baseline. The vocal pitch (F0) shifted +1.2σ concurrently with the heart rate spike.
              </p>
              <p className="text-[10px] mt-4 text-slate-400 bg-slate-50 p-3 rounded-lg border border-slate-100">
                <strong>Disclaimer:</strong> This is a physiological signal report, not a truthfulness determination. 
              </p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
