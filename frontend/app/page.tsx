import Link from "next/link";
import { ArchiveGrid } from "@/components/archive-grid";
import { getAllClips } from "@/lib/clips";

export default function HomePage() {
  const clips = getAllClips();

  return (
    <div className="space-y-12">
      <section className="rounded-2xl border border-neutral-800 bg-gradient-to-b from-neutral-900 to-neutral-950 p-8 shadow-[0_0_60px_-20px_rgba(220,38,38,0.45)] sm:p-10">
        <p className="mb-3 text-xs uppercase tracking-[0.2em] text-neutral-400">Physiological Archive</p>
        <h1 className="max-w-4xl font-serif text-4xl leading-tight text-neutral-50 sm:text-5xl">
          Every lie has a body. Every body has a pulse.
        </h1>
        <p className="mt-6 max-w-3xl text-sm text-neutral-300 sm:text-base">
          VERDICT is a public physiological archive of historical denials, calibrated against
          outcomes history already resolved.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/archive"
            className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-500"
          >
            Explore Archive
          </Link>
          <Link
            href="/calibration"
            className="rounded-md border border-neutral-700 bg-neutral-900 px-4 py-2 text-sm font-medium text-neutral-200 transition hover:border-neutral-500"
          >
            View Calibration
          </Link>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-serif text-2xl text-neutral-100">Archive Preview</h2>
          <span className="text-xs uppercase tracking-[0.16em] text-neutral-500">6 Clips</span>
        </div>
        <ArchiveGrid clips={clips.slice(0, 6)} />
      </section>

      <section id="method" className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
        <h3 className="mb-4 font-serif text-2xl text-neutral-100">Method</h3>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {[
            ["rPPG", "Heart-rate shift from facial color micro-variation over time."],
            ["Facial AUs", "AU15, AU14, AU6, and AU24 intensity extracted per frame."],
            ["Voice", "Pitch dynamics, jitter, shimmer, and speech-rate signatures."],
            ["Linguistic + LLM", "Hedging, pronoun usage, and constrained analyst narrative."],
          ].map(([title, copy]) => (
            <article key={title} className="rounded-xl border border-neutral-800 bg-neutral-950/80 p-4">
              <h4 className="mb-2 text-sm font-semibold text-neutral-100">{title}</h4>
              <p className="text-sm text-neutral-400">{copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
        <h3 className="mb-3 font-serif text-2xl text-neutral-100">Roadmap</h3>
        <div className="flex flex-wrap gap-2">
          {[
            "Baseline Engine",
            "Deepfake Gate",
            "Temporal Replay",
          ].map((item) => (
            <span
              key={item}
              className="rounded-full border border-neutral-700 bg-neutral-950 px-3 py-1 text-xs text-neutral-300"
            >
              {item} · Coming
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}
