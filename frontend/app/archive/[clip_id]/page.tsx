import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { AnalystReport } from "@/components/analyst-report";
import { GroundTruthPanel } from "@/components/ground-truth-panel";
import { ScoreCard } from "@/components/score-card";
import { SignalChart } from "@/components/signal-chart";
import { SignalQualityBadges } from "@/components/signal-quality-badge";
import { getAllClips, getClip } from "@/lib/clips";

function getYouTubeEmbed(url: string, start: number, end: number): string {
  const id = (() => {
    const long = url.match(/[?&]v=([a-zA-Z0-9_-]{6,})/);
    if (long?.[1]) return long[1];
    const short = url.match(/youtu\.be\/([a-zA-Z0-9_-]{6,})/);
    if (short?.[1]) return short[1];
    return "";
  })();

  if (!id) return "";
  return `https://www.youtube.com/embed/${id}?start=${Math.floor(start)}&end=${Math.ceil(end)}&rel=0`;
}

function fmt(n: number, digits = 1): string {
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

export function generateStaticParams() {
  return getAllClips().map((clip) => ({ clip_id: clip.clip_id }));
}

export default function ClipDetailPage({ params }: { params: { clip_id: string } }) {
  const clip = getClip(params.clip_id);
  if (!clip) return notFound();

  const embed = getYouTubeEmbed(clip.video_url, clip.video_start_seconds, clip.video_end_seconds);
  const hrDelta = clip.signals.hr_delta_bpm;
  const f0Delta = clip.signals.f0_delta_hz;

  return (
    <div className="space-y-8">
      {/* Back nav */}
      <Link
        href="/archive"
        className="inline-flex items-center gap-2 text-sm text-slate-500 transition-colors hover:text-slate-900"
      >
        <ArrowLeft className="h-4 w-4" /> Back to archive
      </Link>

      {/* Header */}
      <header className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-600">
            {clip.year}
          </span>
          <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">
            {clip.clip_id}
          </span>
        </div>
        <h1 className="mt-3 font-serif text-5xl font-medium text-slate-900">{clip.subject}</h1>
        <p className="mt-5 max-w-3xl font-serif text-2xl leading-snug text-slate-700">
          &ldquo;{clip.statement}&rdquo;
        </p>
        <p className="mt-3 text-sm leading-relaxed text-slate-500">{clip.context}</p>
      </header>

      {/* Ground truth */}
      <GroundTruthPanel clip={clip} />

      {/* Layout: video + scores side-by-side on desktop */}
      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-900 shadow-sm">
            {embed ? (
              <iframe
                className="aspect-video w-full"
                src={embed}
                title={`${clip.subject} clip`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div className="aspect-video w-full" />
            )}
          </div>

          {/* Signal summary chips */}
          <article className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-2">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Heart Rate
              </p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {fmt(clip.signals.hr_baseline_bpm)} → {fmt(clip.signals.hr_peak_bpm)} bpm
                <span className="ml-2 text-xs text-slate-500">(Δ {fmt(hrDelta)})</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Voice F0
              </p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {fmt(clip.signals.f0_baseline_hz, 0)} → {fmt(clip.signals.f0_peak_hz, 0)} Hz
                <span className="ml-2 text-xs text-slate-500">(Δ {fmt(f0Delta, 0)})</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Facial AUs (max)
              </p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                AU15 {fmt(clip.signals.au15_max_intensity, 1)} · AU14{" "}
                {fmt(clip.signals.au14_max_intensity, 1)} · AU24{" "}
                {fmt(clip.signals.au24_max_intensity, 1)}
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Language
              </p>
              <p className="mt-1 text-sm font-medium text-slate-900">
                {clip.signals.hedging_count} hedges · {fmt(clip.signals.pronoun_drop_rate, 2)}{" "}
                pronoun-drop · {fmt(clip.signals.speech_rate_wpm, 0)} wpm
              </p>
            </div>
          </article>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <ScoreCard
              label="Deception"
              value={clip.scores.deception}
              accent="red"
              hint={`HR Δ ${fmt(hrDelta, 0)} bpm`}
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
      </section>

      {/* Charts */}
      <SignalChart timeline={clip.signals.timeline} />

      {/* Transcript */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <header className="mb-4">
          <h3 className="font-serif text-xl font-medium text-slate-900">Transcript</h3>
          <p className="mt-1 text-xs text-slate-500">
            faster-whisper small · word-level alignment available in raw output
          </p>
        </header>
        <p className="font-serif text-lg leading-relaxed text-slate-700">
          {clip.signals.transcript || "(transcript unavailable)"}
        </p>
      </section>

      {/* LLM analyst */}
      <AnalystReport report={clip.llm_report} />
    </div>
  );
}
