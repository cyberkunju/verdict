"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, CheckCircle2, Zap } from "lucide-react";

import { AnalystReport } from "@/components/analyst-report";
import { GroundTruthPanel } from "@/components/ground-truth-panel";
import { ScoreCard } from "@/components/score-card";
import { SignalChart } from "@/components/signal-chart";
import { SignalQualityBadges } from "@/components/signal-quality-badge";
import { getAllClips } from "@/lib/clips";
import type { Clip, LiveAnalysisPayload, TextPriorInference } from "@/lib/types";

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
  return clips.find((c) => c.clip_id === "sbf_2022") ?? clips[0];
}

function fmt(n: number, digits = 1): string {
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

function TextPriorPanel({ textPrior }: { textPrior?: TextPriorInference | null }) {
  if (!textPrior) return null;
  const p = textPrior.probability_resolved_false;
  const chipClass =
    textPrior.label === "likely_false"
      ? "border-red-200 bg-red-50 text-red-700"
      : textPrior.label === "likely_true"
        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
        : textPrior.label === "uncertain"
          ? "border-amber-200 bg-amber-50 text-amber-700"
          : "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Text Prior Model</p>
        <span className={`rounded-full border px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${chipClass}`}>
          {textPrior.label.replace("_", " ")}
        </span>
      </div>
      <p className="text-sm text-slate-700">
        <strong>{textPrior.model_name}</strong>
        {p !== null ? (
          <>
            {" "}→ P(resolved false): <strong>{(p * 100).toFixed(1)}%</strong>
            {textPrior.confidence !== null ? ` · confidence ${textPrior.confidence}%` : ""}
          </>
        ) : (
          <> unavailable</>
        )}
      </p>
      <p className="mt-3 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500">Selected statement</p>
      <p className="mt-1 text-sm leading-relaxed text-slate-700">“{textPrior.statement_used}”</p>
      <p className="mt-2 text-xs text-slate-500">Source: {textPrior.statement_source}</p>
    </section>
  );
}

export function ResultDashboard({ url, livePayload }: { url: string; livePayload?: LiveAnalysisPayload }) {
  const clips = getAllClips();
  const matched = findClipByUrl(url, clips);
  const isLive = !!livePayload;
  const archiveClip = matched ?? pickFallback(clips);
  const view = livePayload ?? archiveClip;

  const embedId = youtubeId(isLive ? view.video_url || url : archiveClip.video_url);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      {isLive ? (
        <div role="status" className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
          <Zap className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-600" aria-hidden />
          <div>
            <p className="font-semibold text-emerald-900">Live analysis — statement-selected text prior included</p>
            <p className="mt-0.5 text-sm text-emerald-800">
              Pipeline path: transcript extraction → key statement selection → VerdictTextPrior-v1 inference → multimodal score fusion.
            </p>
          </div>
        </div>
      ) : matched ? (
        <div role="status" className="flex items-start gap-3 rounded-2xl border border-blue-200 bg-blue-50 p-4">
          <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-blue-600" aria-hidden />
          <div>
            <p className="font-semibold text-blue-900">Matched to archive entry</p>
            <p className="mt-0.5 text-sm text-blue-800">
              This URL is in the locked dataset (<span className="font-mono">{archiveClip.clip_id}</span>).
            </p>
          </div>
        </div>
      ) : (
        <div role="status" className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" aria-hidden />
          <div>
            <p className="font-semibold text-amber-900">No archive match — preview mode</p>
            <p className="mt-0.5 text-sm text-amber-800">
              Backend is offline or unreachable. Showing the closest comparable archive case: <strong>{archiveClip.subject}</strong> ({archiveClip.year}).
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          <div className="aspect-video w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-900 shadow-sm">
            {embedId ? (
              <iframe
                className="h-full w-full"
                src={`https://www.youtube.com/embed/${embedId}?start=${Math.floor(view.video_start_seconds)}&end=${Math.ceil(view.video_end_seconds)}&rel=0`}
                title={`${view.subject} clip`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-slate-500">Processed Video</div>
            )}
          </div>

          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Statement</p>
            <p className="mt-2 font-serif text-2xl text-slate-900">&ldquo;{view.statement}&rdquo;</p>
            <p className="mt-2 text-sm text-slate-600">
              {view.subject}
              {view.year ? ` · ${view.year}` : ""}
            </p>
            <p className="mt-3 text-xs leading-relaxed text-slate-500">{view.context}</p>
          </article>

          <article className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-2">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Heart Rate</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {fmt(view.signals.hr_baseline_bpm)} → {fmt(view.signals.hr_peak_bpm)} bpm
                <span className="ml-2 text-xs text-slate-500">(Δ {fmt(view.signals.hr_delta_bpm)})</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Voice F0</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {fmt(view.signals.f0_baseline_hz, 0)} → {fmt(view.signals.f0_peak_hz, 0)} Hz
                <span className="ml-2 text-xs text-slate-500">(Δ {fmt(view.signals.f0_delta_hz, 0)})</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Facial AUs</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                AU15 {fmt(view.signals.au15_max_intensity, 1)} · AU14 {fmt(view.signals.au14_max_intensity, 1)} · AU24 {fmt(view.signals.au24_max_intensity, 1)}
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Language</p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {view.signals.hedging_count} hedges · {fmt(view.signals.pronoun_drop_rate, 2)} pronoun-drop · {fmt(view.signals.speech_rate_wpm, 0)} wpm
              </p>
            </div>
          </article>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <ScoreCard label="Deception" value={view.scores.deception} accent="red" hint={`HR Δ ${fmt(view.signals.hr_delta_bpm, 0)} bpm`} />
            <ScoreCard label="Sincerity" value={view.scores.sincerity} accent="blue" hint={`${view.signals.hedging_count} hedges`} />
            <ScoreCard label="Stress" value={view.scores.stress} accent="amber" hint={`${fmt(view.signals.jitter_percent, 1)}% jitter`} />
            <ScoreCard label="Confidence" value={view.scores.confidence} accent="green" hint={`${fmt(view.signals.speech_rate_wpm, 0)} wpm`} />
          </div>
          <SignalQualityBadges quality={view.signal_quality} />
          {isLive ? <TextPriorPanel textPrior={livePayload?.text_prior} /> : null}
        </div>
      </div>

      <SignalChart timeline={view.signals.timeline} />

      {!isLive ? <GroundTruthPanel clip={archiveClip} /> : null}

      <AnalystReport report={view.llm_report} />

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Want more depth?</p>
          <p className="mt-1 font-serif text-lg text-slate-900">Open the full archive for resolved-case comparisons</p>
          <p className="mt-1 text-sm text-slate-500">Includes raw signal lineage, transcript, and extended analyst comparison profile.</p>
        </div>
        <Link href="/archive" className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800">
          See archive <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </motion.div>
  );
}
