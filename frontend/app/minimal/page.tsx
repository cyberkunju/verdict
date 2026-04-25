import { ScoreCard } from "@/components/score-card";
import { getAllClips } from "@/lib/clips";

function toEmbed(url: string, start: number, end: number): string {
  const idFromWatch = url.match(/[?&]v=([a-zA-Z0-9_-]{6,})/)?.[1];
  const idFromShort = url.match(/youtu\.be\/([a-zA-Z0-9_-]{6,})/)?.[1];
  const id = idFromWatch ?? idFromShort ?? "";
  return id ? `https://www.youtube.com/embed/${id}?start=${start}&end=${end}&rel=0` : "";
}

export default function MinimalPage() {
  const clip = getAllClips()[0];
  const embed = toEmbed(clip.video_url, clip.video_start_seconds, clip.video_end_seconds);

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <header className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-5">
        <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Minimal Viewer</p>
        <h1 className="mt-2 font-serif text-3xl text-neutral-100">{clip.subject}</h1>
        <p className="mt-2 text-neutral-300">“{clip.statement}”</p>
      </header>

      <section className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/70">
        {embed ? (
          <iframe
            className="aspect-video w-full"
            src={embed}
            title={`${clip.subject} video`}
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

      <section className="grid gap-3 sm:grid-cols-2">
        <article className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
          <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Summary</p>
          <p className="mt-2 text-sm leading-relaxed text-neutral-200">{clip.llm_report.behavioral_summary}</p>
        </article>

        <article className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
          <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Something Else · Key Signals</p>
          <ul className="mt-2 space-y-1 text-sm text-neutral-300">
            <li>HR Δ: {clip.signals.hr_delta_bpm} bpm</li>
            <li>F0 Δ: {clip.signals.f0_delta_hz} Hz</li>
            <li>AU15 max: {clip.signals.au15_max_intensity}</li>
            <li>Hedging count: {clip.signals.hedging_count}</li>
          </ul>
        </article>
      </section>
    </div>
  );
}
