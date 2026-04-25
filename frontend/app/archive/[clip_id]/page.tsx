import { notFound } from "next/navigation";
import { AnalystReport } from "@/components/analyst-report";
import { ScoreCard } from "@/components/score-card";
import { SignalChart } from "@/components/signal-chart";
import { getClip } from "@/lib/clips";

function getYouTubeEmbed(url: string, start: number, end: number): string {
  const id = (() => {
    const long = url.match(/[?&]v=([a-zA-Z0-9_-]{6,})/);
    if (long?.[1]) return long[1];
    const short = url.match(/youtu\.be\/([a-zA-Z0-9_-]{6,})/);
    if (short?.[1]) return short[1];
    return "";
  })();

  if (!id) return "";
  return `https://www.youtube.com/embed/${id}?start=${start}&end=${end}&rel=0`;
}

export default function ClipDetailPage({ params }: { params: { clip_id: string } }) {
  const clip = getClip(params.clip_id);
  if (!clip) return notFound();

  const embed = getYouTubeEmbed(clip.video_url, clip.video_start_seconds, clip.video_end_seconds);

  return (
    <div className="space-y-6">
      <header className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-5">
        <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">{clip.year}</p>
        <h1 className="mt-2 font-serif text-4xl text-neutral-100">{clip.subject}</h1>
        <p className="mt-4 max-w-3xl text-xl text-neutral-200">“{clip.statement}”</p>
        <p className="mt-3 text-sm text-neutral-400">{clip.context}</p>
      </header>

      <section className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/70">
        {embed ? (
          <iframe
            className="aspect-video w-full"
            src={embed}
            title={`${clip.subject} clip`}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        ) : (
          <div className="aspect-video w-full bg-neutral-950" />
        )}
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <ScoreCard label="Deception" value={clip.scores.deception} accent="red" />
        <ScoreCard label="Sincerity" value={clip.scores.sincerity} accent="blue" />
        <ScoreCard label="Stress" value={clip.scores.stress} accent="amber" />
        <ScoreCard label="Confidence" value={clip.scores.confidence} accent="green" />
      </section>

      <section className="grid gap-3 rounded-xl border border-neutral-800 bg-neutral-900/70 p-4 md:grid-cols-2 lg:grid-cols-4">
        <article>
          <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Heart Rate</p>
          <p className="mt-1 text-sm text-neutral-200">
            {clip.signals.hr_baseline_bpm} → {clip.signals.hr_peak_bpm} bpm
          </p>
        </article>
        <article>
          <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Voice F0</p>
          <p className="mt-1 text-sm text-neutral-200">
            {clip.signals.f0_baseline_hz} → {clip.signals.f0_peak_hz} Hz
          </p>
        </article>
        <article>
          <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Facial AUs</p>
          <p className="mt-1 text-sm text-neutral-200">
            AU15 {clip.signals.au15_max_intensity} · AU14 {clip.signals.au14_max_intensity} · AU24{" "}
            {clip.signals.au24_max_intensity}
          </p>
        </article>
        <article>
          <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Language</p>
          <p className="mt-1 text-sm text-neutral-200">
            Hedges {clip.signals.hedging_count} · Pronoun drop {clip.signals.pronoun_drop_rate}
          </p>
        </article>
      </section>

      <SignalChart timeline={clip.signals.timeline} />

      <section className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
        <h3 className="mb-3 font-serif text-xl text-neutral-100">Transcript</h3>
        <p className="leading-relaxed text-neutral-300">{clip.signals.transcript}</p>
      </section>

      <AnalystReport report={clip.llm_report} />
    </div>
  );
}
