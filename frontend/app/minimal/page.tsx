import Link from "next/link";
import { ScoreCard } from "@/components/score-card";
import { SignalQualityBadges } from "@/components/signal-quality-badge";
import { getAllClips } from "@/lib/clips";

function toEmbed(url: string, start: number, end: number): string {
  const idFromWatch = url.match(/[?&]v=([a-zA-Z0-9_-]{6,})/)?.[1];
  const idFromShort = url.match(/youtu\.be\/([a-zA-Z0-9_-]{6,})/)?.[1];
  const id = idFromWatch ?? idFromShort ?? "";
  return id ? `https://www.youtube.com/embed/${id}?start=${Math.floor(start)}&end=${Math.ceil(end)}&rel=0` : "";
}

export default function MinimalPage() {
  const clips = getAllClips();
  const clip = clips[0];
  const embed = toEmbed(clip.video_url, clip.video_start_seconds, clip.video_end_seconds);
  const correctSet = clips.filter(
    (c) => (c.scores.deception >= 65 && c.ground_truth === "false") || (c.scores.sincerity >= 65 && c.ground_truth === "sincere"),
  );
  const agreement = Math.round((correctSet.length / Math.max(clips.length, 1)) * 100);

  return (
    <div className="mx-auto max-w-6xl space-y-8 pb-10">
      <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">VERDICT · Analyzer</p>
        <h1 className="mt-3 max-w-3xl font-serif text-4xl font-medium leading-tight text-slate-900 sm:text-5xl">
          Fast, minimal analysis flow for public statements
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-slate-600 sm:text-base">
          Submit a video segment, inspect the result, and compare signals against resolved historical outcomes.
          The interface is intentionally reduced to <strong>upload → analyze → review</strong>.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/archive"
            className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          >
            Browse Archive
          </Link>
          <Link
            href="/calibration"
            className="rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition hover:border-blue-300"
          >
            View Calibration
          </Link>
          <Link
            href="/"
            className="rounded-full border border-slate-200 bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
          >
            Try the new analyzer →
          </Link>
        </div>
      </header>

      <section className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-serif text-2xl font-medium text-slate-900">1. Upload or paste source</h2>
          <p className="mt-2 text-sm text-slate-500">
            UI-only intake. Submit-handler is wired in the new analyzer flow on the home page.
          </p>

          <form className="mt-5 space-y-4" action="#" method="post">
            <div>
              <label
                htmlFor="video-url"
                className="mb-2 block text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500"
              >
                YouTube URL
              </label>
              <input
                id="video-url"
                name="video-url"
                defaultValue={clip.video_url}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <label
                  htmlFor="start"
                  className="mb-2 block text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500"
                >
                  Start (s)
                </label>
                <input
                  id="start"
                  name="start"
                  defaultValue={clip.video_start_seconds}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
                />
              </div>
              <div>
                <label
                  htmlFor="end"
                  className="mb-2 block text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500"
                >
                  End (s)
                </label>
                <input
                  id="end"
                  name="end"
                  defaultValue={clip.video_end_seconds}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
                />
              </div>
              <div>
                <label
                  htmlFor="clip-id"
                  className="mb-2 block text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500"
                >
                  Reference ID
                </label>
                <input
                  id="clip-id"
                  name="clip-id"
                  defaultValue={clip.clip_id}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
                />
              </div>
            </div>

            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
              <p className="text-sm text-slate-700">Drop .mp4 here or choose local file</p>
              <input
                type="file"
                className="mt-3 block w-full cursor-pointer text-xs text-slate-500 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-white hover:file:bg-slate-800"
                aria-label="Upload video file"
              />
            </div>

            <button
              type="button"
              className="min-h-11 w-full rounded-full bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-400"
            >
              Analyze Segment
            </button>
          </form>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-serif text-2xl font-medium text-slate-900">2. Review result</h2>
          <p className="mt-2 text-sm text-slate-500">Sample below loaded from the locked archive dataset.</p>

          <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Statement</p>
            <p className="mt-2 font-serif text-xl text-slate-900">&ldquo;{clip.statement}&rdquo;</p>
            <p className="mt-2 text-sm text-slate-600">
              {clip.subject} · {clip.year}
            </p>
          </div>

          <div className="mt-4">
            <SignalQualityBadges quality={clip.signal_quality} />
          </div>

          <p className="mt-4 text-sm leading-relaxed text-slate-700">{clip.llm_report.behavioral_summary}</p>
        </article>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-900 shadow-sm">
        {embed ? (
          <iframe
            className="aspect-video w-full"
            src={embed}
            title={`${clip.subject} video`}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        ) : (
          <div className="aspect-video w-full" />
        )}
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <ScoreCard label="Deception" value={clip.scores.deception} accent="red" />
        <ScoreCard label="Sincerity" value={clip.scores.sincerity} accent="blue" />
        <ScoreCard label="Stress" value={clip.scores.stress} accent="amber" />
        <ScoreCard label="Confidence" value={clip.scores.confidence} accent="green" />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Analyst Summary</p>
          <p className="mt-3 text-sm leading-relaxed text-slate-700">{clip.llm_report.comparative_profile}</p>
          <p className="mt-3 text-sm leading-relaxed text-slate-500">{clip.llm_report.qualifications}</p>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Calibration Context</p>
          <p className="mt-2 font-serif text-3xl font-medium text-slate-900">{agreement}% historical agreement</p>
          <ul className="mt-4 space-y-2 text-sm text-slate-600">
            <li>• False-denial references: {clips.filter((c) => c.ground_truth === "false").length} cases in current lock</li>
            <li>• Sincere reference: {clips.filter((c) => c.ground_truth === "sincere").length} whistleblower testimony</li>
            <li>• Output includes uncertainty + signal quality flags</li>
          </ul>
          <p className="mt-4 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">
            Dataset size: {clips.length} clips
          </p>
        </article>
      </section>
    </div>
  );
}
