import Link from "next/link";
import { ScoreCard } from "@/components/score-card";
import { getAllClips } from "@/lib/clips";

function toEmbed(url: string, start: number, end: number): string {
  const idFromWatch = url.match(/[?&]v=([a-zA-Z0-9_-]{6,})/)?.[1];
  const idFromShort = url.match(/youtu\.be\/([a-zA-Z0-9_-]{6,})/)?.[1];
  const id = idFromWatch ?? idFromShort ?? "";
  return id ? `https://www.youtube.com/embed/${id}?start=${start}&end=${end}&rel=0` : "";
}

function qualityClass(flag: "real" | "fallback" | "manual"): string {
  if (flag === "real") return "border-emerald-500/30 bg-emerald-950/30 text-emerald-200";
  if (flag === "fallback") return "border-amber-500/30 bg-amber-950/30 text-amber-200";
  return "border-neutral-600 bg-neutral-800 text-neutral-200";
}

export default function MinimalPage() {
  const clips = getAllClips();
  const clip = clips[0];
  const embed = toEmbed(clip.video_url, clip.video_start_seconds, clip.video_end_seconds);

  return (
    <div className="mx-auto max-w-6xl space-y-8 pb-10">
      <header className="rounded-2xl border border-neutral-800 bg-gradient-to-b from-neutral-900 to-neutral-950 p-6 sm:p-8">
        <p className="text-xs uppercase tracking-[0.16em] text-neutral-400">VERDICT · Analyzer</p>
        <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight text-neutral-50 sm:text-5xl">
          Fast, minimal analysis flow for public statements
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-neutral-300 sm:text-base">
          Submit a video segment, inspect the result, and compare signals against resolved historical
          outcomes. The interface is intentionally reduced to upload → analyze → review.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/archive"
            className="rounded-md border border-neutral-700 bg-neutral-950 px-4 py-2 text-sm text-neutral-200 transition hover:border-neutral-500"
          >
            Browse Archive
          </Link>
          <Link
            href="/calibration"
            className="rounded-md border border-red-500/40 bg-red-950/30 px-4 py-2 text-sm text-red-200 transition hover:border-red-400"
          >
            View Calibration
          </Link>
        </div>
      </header>

      <section className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <article className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-5 sm:p-6">
          <h2 className="font-serif text-2xl text-neutral-100">1) Upload or paste source</h2>
          <p className="mt-2 text-sm text-neutral-400">
            For now, UI-only intake. Analyzer backend hookup can be added to this form endpoint.
          </p>

          <form className="mt-5 space-y-4" action="#" method="post">
            <div>
              <label htmlFor="video-url" className="mb-2 block text-xs uppercase tracking-[0.12em] text-neutral-400">
                YouTube URL
              </label>
              <input
                id="video-url"
                name="video-url"
                defaultValue={clip.video_url}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 outline-none transition focus:border-red-500"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <label htmlFor="start" className="mb-2 block text-xs uppercase tracking-[0.12em] text-neutral-400">
                  Start (s)
                </label>
                <input
                  id="start"
                  name="start"
                  defaultValue={clip.video_start_seconds}
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 outline-none transition focus:border-red-500"
                />
              </div>
              <div>
                <label htmlFor="end" className="mb-2 block text-xs uppercase tracking-[0.12em] text-neutral-400">
                  End (s)
                </label>
                <input
                  id="end"
                  name="end"
                  defaultValue={clip.video_end_seconds}
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 outline-none transition focus:border-red-500"
                />
              </div>
              <div>
                <label htmlFor="clip-id" className="mb-2 block text-xs uppercase tracking-[0.12em] text-neutral-400">
                  Reference ID
                </label>
                <input
                  id="clip-id"
                  name="clip-id"
                  defaultValue={clip.clip_id}
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 outline-none transition focus:border-red-500"
                />
              </div>
            </div>

            <div className="rounded-xl border border-dashed border-neutral-700 bg-neutral-950/80 p-6 text-center">
              <p className="text-sm text-neutral-300">Drop .mp4 here or choose local file</p>
              <input
                type="file"
                className="mt-3 block w-full cursor-pointer text-xs text-neutral-400 file:mr-3 file:rounded-md file:border-0 file:bg-neutral-800 file:px-3 file:py-2 file:text-neutral-100"
                aria-label="Upload video file"
              />
            </div>

            <button
              type="button"
              className="min-h-11 w-full rounded-lg bg-red-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-400"
            >
              Analyze Segment
            </button>
          </form>
        </article>

        <article className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-5 sm:p-6">
          <h2 className="font-serif text-2xl text-neutral-100">2) Review result</h2>
          <p className="mt-2 text-sm text-neutral-400">Active sample loaded from locked archive dataset.</p>

          <div className="mt-4 space-y-3 rounded-xl border border-neutral-800 bg-neutral-950/80 p-4">
            <p className="text-xs uppercase tracking-[0.12em] text-neutral-500">Statement</p>
            <p className="font-serif text-xl text-neutral-100">“{clip.statement}”</p>
            <p className="text-sm text-neutral-400">
              {clip.subject} · {clip.year}
            </p>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-2">
            <span className={`rounded-md border px-2 py-1 text-xs ${qualityClass(clip.signal_quality.rppg)}`}>
              rPPG: {clip.signal_quality.rppg}
            </span>
            <span className={`rounded-md border px-2 py-1 text-xs ${qualityClass(clip.signal_quality.voice)}`}>
              Voice: {clip.signal_quality.voice}
            </span>
            <span className={`rounded-md border px-2 py-1 text-xs ${qualityClass(clip.signal_quality.facial_au)}`}>
              Face: {clip.signal_quality.facial_au}
            </span>
            <span className={`rounded-md border px-2 py-1 text-xs ${qualityClass(clip.signal_quality.transcript)}`}>
              Transcript: {clip.signal_quality.transcript}
            </span>
          </div>

          <p className="mt-4 text-sm leading-relaxed text-neutral-300">{clip.llm_report.behavioral_summary}</p>
        </article>
      </section>

      <section className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/70">
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

      <section className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
        <article className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-5">
          <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Analyst Summary</p>
          <p className="mt-3 text-sm leading-relaxed text-neutral-200">{clip.llm_report.comparative_profile}</p>
          <p className="mt-3 text-sm leading-relaxed text-neutral-400">{clip.llm_report.qualifications}</p>
        </article>

        <article className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-5">
          <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Calibration Context</p>
          <p className="mt-2 text-3xl font-semibold text-neutral-100">72% historical agreement</p>
          <ul className="mt-4 space-y-2 text-sm text-neutral-300">
            <li>• False-denial references: 5 cases in current lock</li>
            <li>• Sincere reference: 1 whistleblower testimony</li>
            <li>• Output includes uncertainty + signal quality flags</li>
          </ul>
          <p className="mt-4 text-xs uppercase tracking-[0.12em] text-neutral-500">Dataset size: {clips.length} clips</p>
        </article>
      </section>
    </div>
  );
}
