"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, Sparkles } from "lucide-react";
import { ScoreCard } from "@/components/score-card";
import type { Clip } from "@/lib/types";
import type { LiveScores } from "@/lib/composite-scores";
import type { Emotions } from "@/lib/blendshape-map";

export interface LiveRecordingSummary {
  durationSeconds: number;
  scores: LiveScores;
  hrBaselineBpm: number | null;
  hrPeakBpm: number | null;
  hrDeltaBpm: number | null;
  f0BaselineHz: number | null;
  f0PeakHz: number | null;
  jitterPercent: number;
  speechRateWpm: number;
  hedgeCount: number;
  dominantEmotion: keyof Emotions;
  emotionAverages: Emotions;
  closestArchive: { clip: Clip; distance: number } | null;
  recordingBlobUrl: string | null;
  transcript: string;
  /**
   * Honest reporting of which signal pipelines actually produced data during
   * recording. The summary banner uses this to decide whether to show
   * confidence numbers or a "insufficient signal" warning.
   */
  dataQuality: {
    hrSamples: number;
    f0Samples: number;
    auFrames: number;
    voicedAudioFrames: number;
    peakBlendshape: number;
    avgBrightness: number;
  };
}

function emotionLabel(e: keyof Emotions): string {
  return e.charAt(0).toUpperCase() + e.slice(1);
}

function fmt(n: number | null, digits = 0): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

export function LiveSummary({
  summary,
  onReset,
}: {
  summary: LiveRecordingSummary;
  onReset: () => void;
}) {
  const { scores, closestArchive, durationSeconds, recordingBlobUrl, dataQuality } = summary;
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = Math.floor(durationSeconds % 60);

  // Honest data-quality assessment. We trust the scores only when at least one
  // physiological / behavioral signal pipeline produced enough data.
  const insufficientReasons: string[] = [];
  if (dataQuality.hrSamples < 3) insufficientReasons.push("no heart-rate signal");
  if (dataQuality.f0Samples < 5) insufficientReasons.push("no voice pitch detected");
  if (dataQuality.peakBlendshape < 0.05) insufficientReasons.push("no facial expression activity");
  if (dataQuality.voicedAudioFrames < 5) insufficientReasons.push("microphone silent");
  const hasInsufficientData = insufficientReasons.length >= 2;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Insufficient-signal warning is louder than the headline itself */}
      {hasInsufficientData && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5">
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" aria-hidden />
          <div className="text-sm text-amber-900">
            <p className="font-semibold">Recording captured insufficient signal.</p>
            <p className="mt-1">
              The composite scores below default to formula constants because the underlying
              pipelines didn&rsquo;t produce data: <strong>{insufficientReasons.join(", ")}</strong>.
              Try again with better lighting, the camera at face height, and speaking continuously.
            </p>
            <p className="mt-1 text-[11px] text-amber-700/80">
              HR samples: {dataQuality.hrSamples} · F0 samples: {dataQuality.f0Samples} · AU frames:{" "}
              {dataQuality.auFrames} · voiced audio: {dataQuality.voicedAudioFrames} · peak
              blendshape: {(dataQuality.peakBlendshape * 100).toFixed(0)}% · avg brightness:{" "}
              {dataQuality.avgBrightness.toFixed(0)}
            </p>
          </div>
        </div>
      )}

      {/* Headline */}
      <header className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white via-slate-50 to-white p-8 shadow-sm">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-violet-500" aria-hidden />
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
            Recording Synthesis
          </p>
        </div>
        <h2 className="mt-2 font-serif text-4xl font-medium text-slate-900">
          {minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`} captured
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
          {hasInsufficientData ? (
            <>
              Below is a synthesis of whatever signals the in-browser pipeline could extract during
              your session. Treat the numbers as placeholders — the warning above explains why.
            </>
          ) : (
            <>
              Below is a deterministic synthesis of your session: rPPG-derived heart-rate dynamics,
              voice jitter and pitch shifts, action-unit averages, and the four composite scores.
              Nothing was uploaded — all numbers were computed in your browser.
            </>
          )}
        </p>
      </header>

      {/* Composite scores */}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <ScoreCard
          label="Deception"
          value={scores.deception}
          accent="red"
          hint={`HR Δ ${fmt(summary.hrDeltaBpm, 0)} bpm`}
        />
        <ScoreCard
          label="Sincerity"
          value={scores.sincerity}
          accent="blue"
          hint={`${summary.hedgeCount} hedges`}
        />
        <ScoreCard
          label="Stress"
          value={scores.stress}
          accent="amber"
          hint={`${fmt(summary.jitterPercent, 1)}% jitter`}
        />
        <ScoreCard
          label="Confidence"
          value={scores.confidence}
          accent="green"
          hint={`${fmt(summary.speechRateWpm, 0)} wpm`}
        />
      </section>

      {/* Two-column layout: signals + closest archive */}
      <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <article className="space-y-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="font-serif text-xl font-medium text-slate-900">Signal Window Summary</h3>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div>
              <dt className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Heart Rate
              </dt>
              <dd className="mt-1 font-medium text-slate-900">
                {fmt(summary.hrBaselineBpm, 0)} → {fmt(summary.hrPeakBpm, 0)} bpm
                <span className="ml-2 text-xs text-slate-500">
                  Δ {fmt(summary.hrDeltaBpm, 0)}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Voice F0
              </dt>
              <dd className="mt-1 font-medium text-slate-900">
                {fmt(summary.f0BaselineHz, 0)} → {fmt(summary.f0PeakHz, 0)} Hz
              </dd>
            </div>
            <div>
              <dt className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Voice Jitter
              </dt>
              <dd className="mt-1 font-medium text-slate-900">
                {fmt(summary.jitterPercent, 2)}%
              </dd>
            </div>
            <div>
              <dt className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Speech Rate
              </dt>
              <dd className="mt-1 font-medium text-slate-900">
                {fmt(summary.speechRateWpm, 0)} wpm
              </dd>
            </div>
            <div className="col-span-2">
              <dt className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Dominant Affect
              </dt>
              <dd className="mt-1 font-medium text-slate-900">
                {emotionLabel(summary.dominantEmotion)}{" "}
                <span className="text-xs text-slate-500">
                  ({(summary.emotionAverages[summary.dominantEmotion] * 100).toFixed(0)}% mean intensity)
                </span>
              </dd>
            </div>
            {summary.transcript && (
              <div className="col-span-2">
                <dt className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  Transcript
                </dt>
                <dd className="mt-1 max-h-32 overflow-y-auto rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">
                  {summary.transcript}
                </dd>
              </div>
            )}
          </dl>
        </article>

        {closestArchive && (
          <article className="rounded-2xl border border-slate-200 bg-gradient-to-br from-violet-50 via-white to-white p-6 shadow-sm">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-violet-700">
              Closest Archive Profile
            </p>
            <h3 className="mt-2 font-serif text-2xl font-medium text-slate-900">
              {closestArchive.clip.subject}
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              {closestArchive.clip.year} · {closestArchive.clip.ground_truth}
            </p>
            <p className="mt-3 font-serif text-base italic leading-snug text-slate-700">
              &ldquo;{closestArchive.clip.statement}&rdquo;
            </p>
            <div className="mt-4 flex items-center justify-between text-xs">
              <span className="text-slate-500">
                Score-space distance: <span className="tabular-nums">{closestArchive.distance.toFixed(1)}</span>
              </span>
              <Link
                href={`/archive/${closestArchive.clip.clip_id}`}
                className="inline-flex items-center gap-1 font-medium text-violet-700 hover:text-violet-800"
              >
                Compare <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
            <p className="mt-3 text-[11px] italic leading-relaxed text-slate-500">
              Comparative only. We are not claiming you resemble {closestArchive.clip.subject}{" "}
              behaviorally — only that your composite score profile in this window has the smallest
              4-D Euclidean distance.
            </p>
          </article>
        )}
      </section>

      {/* Recording playback */}
      {recordingBlobUrl && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-3 font-serif text-xl font-medium text-slate-900">Replay</h3>
          <video
            className="aspect-video w-full max-w-3xl rounded-xl border border-slate-200 bg-slate-900"
            src={recordingBlobUrl}
            controls
          />
          <p className="mt-2 text-xs italic text-slate-500">
            Recording lives only in this browser tab. Closing or reloading discards it.
          </p>
        </section>
      )}

      {/* Reset CTA */}
      <div className="flex flex-wrap justify-center gap-3 pt-4">
        <button
          type="button"
          onClick={onReset}
          className="rounded-full border border-slate-200 bg-white px-6 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        >
          Record again
        </button>
        <Link
          href="/archive"
          className="rounded-full bg-slate-900 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
        >
          Browse archive →
        </Link>
      </div>
    </motion.div>
  );
}
