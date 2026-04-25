"use client";
import Link from "next/link";
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

      <motion.section
        variants={item}
        className="relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-10 text-white shadow-xl"
      >
        <div className="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 -left-20 h-72 w-72 rounded-full bg-violet-500/20 blur-3xl" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] text-emerald-300 backdrop-blur">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-300" /> New · Privacy-first
            </div>
            <h3 className="mt-4 font-serif text-4xl font-medium leading-tight md:text-5xl">
              Ask your own body.
            </h3>
            <p className="mt-4 text-base leading-relaxed text-slate-300">
              The same pipeline that calibrates against the historical archive — rPPG heart rate
              from forehead color, voice pitch and jitter from your microphone, 14 facial action
              units from face geometry, composite scoring — running entirely in your browser, on
              your live camera. Nothing uploads. Nothing is stored.
            </p>
            <div className="mt-6 flex flex-wrap gap-3 text-xs">
              {[
                "rPPG · POS",
                "MediaPipe blendshapes",
                "YIN pitch",
                "Web Speech transcript",
                "MediaRecorder replay",
              ].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-white/15 bg-white/5 px-3 py-1 font-medium text-slate-200 backdrop-blur"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
          <Link
            href="/live"
            className="group relative inline-flex items-center justify-center gap-3 rounded-full bg-white px-8 py-4 text-sm font-semibold text-slate-900 shadow-lg shadow-black/30 transition hover:bg-emerald-300 hover:text-slate-950"
          >
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
            </span>
            Try Live Mode
            <span aria-hidden className="transition-transform group-hover:translate-x-0.5">
              →
            </span>
          </Link>
        </div>
      </motion.section>
    </motion.div>
  );
}
