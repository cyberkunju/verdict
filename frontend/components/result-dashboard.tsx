"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";
import { AnalystReport } from "@/components/analyst-report";
import { GroundTruthPanel } from "@/components/ground-truth-panel";
import { ScoreCard } from "@/components/score-card";
import { SignalChart } from "@/components/signal-chart";
import { SignalQualityBadges } from "@/components/signal-quality-badge";
import { getAllClips } from "@/lib/clips";
import type { Clip } from "@/lib/types";

function youtubeId(url: string): string | null {
  const m = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
  return m?.[1] ?? null;
}

function findClipByUrl(url: string, clips: Clip[]): Clip | null {
  const id = youtubeId(url);
  if (!id) return null;
  return clips.find((c) => c.video_url.includes(id)) ?? null;
}

function pickFallback(clips: Clip[]): Clip {
  // SBF is the most photogenic demo case (HD video + dramatic signal pattern).
  return clips.find((c) => c.clip_id === "sbf_2022") ?? clips[0];
}

function fmt(n: number, digits = 1): string {
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

export function ResultDashboard({ url }: { url: string }) {
  const clips = getAllClips();
  const matched = findClipByUrl(url, clips);
  const clip = matched ?? pickFallback(clips);
  const embedId = youtubeId(clip.video_url);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      {/* Match status banner */}
      {matched ? (
        <div
          role="status"
          className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4"
        >
          <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-600" aria-hidden />
          <div>
            <p className="font-semibold text-emerald-900">Matched to archive entry</p>
            <p className="mt-0.5 text-sm text-emerald-800">
              This URL is in the locked dataset (<span className="font-mono">{clip.clip_id}</span>). All numbers below
              are real backend output: rPPG via multi-ROI POS, voice via Praat, transcript via Whisper, and a cautious
              GPT-4o synthesis.
            </p>
          </div>
        </div>
      ) : (
        <div
          role="status"
          className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4"
        >
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" aria-hidden />
          <div>
            <p className="font-semibold text-amber-900">No archive match — preview mode</p>
            <p className="mt-0.5 text-sm text-amber-800">
              Live signal extraction needs the Python backend running. For this preview we are showing the closest
              comparable case from the locked archive: <strong>{clip.subject}</strong> ({clip.year}). Submit a URL from
              the archive to see exact match data.
            </p>
          </div>
        </div>
      )}

      {/* Top row: video + scores */}
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          <div className="aspect-video w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-900 shadow-sm">
            {embedId ? (
              <iframe
                className="h-full w-full"
                src={`https://www.youtube.com/embed/${embedId}?start=${Math.floor(
                  clip.video_start_seconds,
                )}&end=${Math.ceil(clip.video_end_seconds)}&rel=0`}
                title={`${clip.subject} clip`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-slate-500">
                Processed Video
              </div>
            )}
          </div>

          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Statement</p>
            <p className="mt-2 font-serif text-2xl text-slate-900">&ldquo;{clip.statement}&rdquo;</p>
            <p className="mt-2 text-sm text-slate-600">
              {clip.subject} · {clip.year}
            </p>
            <p className="mt-3 text-xs leading-relaxed text-slate-500">{clip.context}</p>
          </article>

          <article className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-2">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Heart Rate</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {fmt(clip.signals.hr_baseline_bpm)} → {fmt(clip.signals.hr_peak_bpm)} bpm
                <span className="ml-2 text-xs text-slate-500">(Δ {fmt(clip.signals.hr_delta_bpm)})</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Voice F0</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {fmt(clip.signals.f0_baseline_hz, 0)} → {fmt(clip.signals.f0_peak_hz, 0)} Hz
                <span className="ml-2 text-xs text-slate-500">(Δ {fmt(clip.signals.f0_delta_hz, 0)})</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Facial AUs</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                AU15 {fmt(clip.signals.au15_max_intensity, 1)} · AU14{" "}
                {fmt(clip.signals.au14_max_intensity, 1)} · AU24{" "}
                {fmt(clip.signals.au24_max_intensity, 1)}
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Language</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {clip.signals.hedging_count} hedges · {fmt(clip.signals.pronoun_drop_rate, 2)} pronoun-drop ·{" "}
                {fmt(clip.signals.speech_rate_wpm, 0)} wpm
              </p>
            </div>
          </article>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <ScoreCard
              label="Deception"
              value={clip.scores.deception}
              accent="red"
              hint={`HR Δ ${fmt(clip.signals.hr_delta_bpm, 0)} bpm`}
            />
            <ScoreCard
              label="Sincerity"
              value={clip.scores.sincerity}
              accent="blue"
              hint={`${clip.signals.hedging_count} hedges`}
            />
            <ScoreCard
              label="Stress"
              value={clip.scores.stress}
              accent="amber"
              hint={`${fmt(clip.signals.jitter_percent, 1)}% jitter`}
            />
            <ScoreCard
              label="Confidence"
              value={clip.scores.confidence}
              accent="green"
              hint={`${fmt(clip.signals.speech_rate_wpm, 0)} wpm`}
            />
          </div>
          <SignalQualityBadges quality={clip.signal_quality} />
        </div>
      </div>

      {/* Charts */}
      <SignalChart timeline={clip.signals.timeline} />

      {/* Ground truth context */}
      <GroundTruthPanel clip={clip} />

      {/* LLM analyst (real GPT-4o output) */}
      <AnalystReport report={clip.llm_report} />

      {/* CTA */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Want more depth?</p>
          <p className="mt-1 font-serif text-lg text-slate-900">
            Open the full archive entry for {clip.subject}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Includes raw signal lineage, transcript, and an extended analyst comparison profile.
          </p>
        </div>
        <Link
          href={`/archive/${clip.clip_id}`}
          className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
        >
          See archive entry <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </motion.div>
  );
}
