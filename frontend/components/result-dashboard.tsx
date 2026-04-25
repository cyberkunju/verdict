"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ExternalLink } from "lucide-react";

import { AnalystReport } from "@/components/analyst-report";
import { ScoreCard } from "@/components/score-card";
import { SignalChart } from "@/components/signal-chart";
import { SignalQualityBadges } from "@/components/signal-quality-badge";
import type { LiveAnalysisPayload } from "@/lib/types";

function getVideoEmbed(url: string, start: number, end: number): string | null {
  const videoIdMatch = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
  if (!videoIdMatch) return null;
  return `https://www.youtube.com/embed/${videoIdMatch[1]}?start=${Math.floor(start)}&end=${Math.ceil(end)}&rel=0`;
}

function fmt(n: number, digits = 1): string {
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

export function ResultDashboard({ payload }: { payload: LiveAnalysisPayload }) {
  const embed = getVideoEmbed(payload.video_url, payload.video_start_seconds, payload.video_end_seconds);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4" role="status">
        <p className="font-semibold text-blue-900">Live analyzer result</p>
        <p className="mt-1 text-sm text-blue-800">
          This report was generated from the backend job pipeline and calibrated against the historical archive.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          <div className="aspect-video w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-900 shadow-sm">
            {embed ? (
              <iframe
                className="h-full w-full"
                src={embed}
                title={`${payload.subject} clip`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-slate-500">Processed Video</div>
            )}
          </div>

          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Statement</p>
            <p className="mt-2 font-serif text-2xl text-slate-900">&ldquo;{payload.statement}&rdquo;</p>
            <p className="mt-2 text-sm text-slate-600">
              {payload.subject}
              {payload.year ? ` · ${payload.year}` : ""}
            </p>
            <p className="mt-3 text-xs leading-relaxed text-slate-500">{payload.context}</p>
          </article>

          <article className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-2">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Heart Rate</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {fmt(payload.signals.hr_baseline_bpm)} → {fmt(payload.signals.hr_peak_bpm)} bpm
                <span className="ml-2 text-xs text-slate-500">(Δ {fmt(payload.signals.hr_delta_bpm)})</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Voice F0</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {fmt(payload.signals.f0_baseline_hz, 0)} → {fmt(payload.signals.f0_peak_hz, 0)} Hz
                <span className="ml-2 text-xs text-slate-500">(Δ {fmt(payload.signals.f0_delta_hz, 0)})</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Facial AUs</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                AU15 {fmt(payload.signals.au15_max_intensity, 1)} · AU14 {fmt(payload.signals.au14_max_intensity, 1)} · AU24 {fmt(payload.signals.au24_max_intensity, 1)}
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Language</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {payload.signals.hedging_count} hedges · {fmt(payload.signals.pronoun_drop_rate, 2)} pronoun-drop · {fmt(payload.signals.speech_rate_wpm, 0)} wpm
              </p>
            </div>
          </article>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <ScoreCard
              label="Deception"
              value={payload.scores.deception}
              accent="red"
              hint={`HR Δ ${fmt(payload.signals.hr_delta_bpm, 0)} bpm`}
            />
            <ScoreCard
              label="Sincerity"
              value={payload.scores.sincerity}
              accent="blue"
              hint={`${payload.signals.hedging_count} hedges`}
            />
            <ScoreCard
              label="Stress"
              value={payload.scores.stress}
              accent="amber"
              hint={`${fmt(payload.signals.jitter_percent, 1)}% jitter`}
            />
            <ScoreCard
              label="Confidence"
              value={payload.scores.confidence}
              accent="green"
              hint={`${fmt(payload.signals.speech_rate_wpm, 0)} wpm`}
            />
          </div>

          <SignalQualityBadges quality={payload.signal_quality} />

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-serif text-lg font-medium text-slate-900">Closest archive matches</h3>
              <Link href="/archive" className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-800">
                Archive <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
            <div className="space-y-3">
              {payload.similar_archive_matches.map((match) => (
                <div key={match.clip_id} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-slate-900">{match.subject}</p>
                      <p className="text-xs text-slate-500">{match.clip_id} · {match.ground_truth}</p>
                    </div>
                    <span className="rounded-full bg-white px-2 py-1 text-xs font-medium text-slate-600">
                      sim {match.similarity.toFixed(2)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{match.statement}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <SignalChart timeline={payload.signals.timeline} />

      <AnalystReport report={payload.llm_report} />

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Want more depth?</p>
          <p className="mt-1 font-serif text-lg text-slate-900">Open the historical archive and compare against resolved cases</p>
          <p className="mt-1 text-sm text-slate-500">
            Archive pages include locked-case context, signal lineage, and full calibration framing.
          </p>
        </div>
        <Link
          href="/archive"
          className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
        >
          See archive <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </motion.div>
  );
}
