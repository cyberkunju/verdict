"use client";
import { ArchiveGrid } from "@/components/archive-grid";
import { AnalyzerInput } from "@/components/analyzer-input";
import { getAllClips } from "@/lib/clips";
import { motion } from "framer-motion";

export default function HomePage() {
  const clips = getAllClips();

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-24">
      <motion.section variants={item} className="relative pt-12 pb-20 text-center">
        <p className="mb-6 text-sm font-bold uppercase tracking-[0.25em] text-slate-400">The Physiological History of Denial</p>
        <h1 className="mx-auto max-w-5xl font-serif text-5xl leading-[1.1] text-slate-900 md:text-7xl tracking-tight">
          Every lie has a body. <br className="hidden sm:block" /><span className="text-slate-500">We finally asked the body.</span>
        </h1>
        <p className="mx-auto mt-8 max-w-2xl text-lg leading-relaxed text-slate-600">
          VERDICT extracts seven layers of involuntary signals from any public video to produce a multi-dimensional behavioral profile. Calibrated against history.
        </p>

        <AnalyzerInput />
        
      </motion.section>

      <motion.section variants={item}>
        <div className="mb-6 flex items-end justify-between">
          <div>
            <h2 className="font-serif text-3xl font-medium text-slate-900">Archive Preview</h2>
            <p className="mt-1 text-sm text-slate-500">Latest processed historical statements</p>
          </div>
          <span className="hidden sm:block text-xs font-medium uppercase tracking-[0.16em] text-slate-400 bg-slate-100 px-3 py-1 rounded-full">6 Clips</span>
        </div>
        <ArchiveGrid clips={clips.slice(0, 6)} />
      </motion.section>

      <motion.section variants={item} id="method" className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h3 className="mb-6 font-serif text-3xl font-medium text-slate-900">Methodology</h3>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            ["rPPG", "Heart-rate shift from facial color micro-variation over time."],
            ["Facial AUs", "AU15, AU14, AU6, and AU24 intensity extracted per frame."],
            ["Voice", "Pitch dynamics, jitter, shimmer, and speech-rate signatures."],
            ["Linguistic + LLM", "Hedging, pronoun usage, and constrained analyst narrative."],
          ].map(([title, copy]) => (
            <motion.article 
              key={title} 
              whileHover={{ y: -5 }}
              className="rounded-2xl border border-slate-100 bg-slate-50 p-5 transition-colors hover:bg-white hover:shadow-md"
            >
              <h4 className="mb-2 text-sm font-bold text-slate-900">{title}</h4>
              <p className="text-sm leading-relaxed text-slate-600">{copy}</p>
            </motion.article>
          ))}
        </div>
      </motion.section>

      <motion.section variants={item} className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h3 className="mb-4 font-serif text-2xl font-medium text-slate-900">Roadmap</h3>
        <div className="flex flex-wrap gap-3">
          {[
            "Baseline Engine",
            "Deepfake Gate",
            "Temporal Replay",
          ].map((item) => (
            <span
              key={item}
              className="rounded-full border border-slate-200 bg-slate-50 px-4 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300"
            >
              {item} <span className="opacity-50 ml-1">· Coming</span>
            </span>
          ))}
        </div>
      </motion.section>
    </motion.div>
  );
}
