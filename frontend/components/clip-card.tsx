import Link from "next/link";
import type { Clip } from "@/lib/types";

function GroundTruthBadge({ value }: { value: Clip["ground_truth"] }) {
  const style =
    value === "false"
      ? "border-red-500/40 bg-red-950/40 text-red-300"
      : value === "sincere"
        ? "border-blue-500/40 bg-blue-950/40 text-blue-300"
        : "border-emerald-500/40 bg-emerald-950/40 text-emerald-300";

  return (
    <span className={`rounded-full border px-2 py-1 text-xs uppercase tracking-wider ${style}`}>
      {value}
    </span>
  );
}

export function ClipCard({ clip }: { clip: Clip }) {
  return (
    <article className="group overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/70 transition hover:border-neutral-600">
      <Link href={`/archive/${clip.clip_id}`} className="block">
        <div className="h-40 w-full bg-cover bg-center" style={{ backgroundImage: `url(${clip.thumbnail_url})` }} />
        <div className="space-y-3 p-4">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm text-neutral-400">{clip.subject}</p>
            <p className="text-xs uppercase tracking-wider text-neutral-500">{clip.year}</p>
          </div>

          <p className="line-clamp-2 font-serif text-lg text-neutral-100">“{clip.statement}”</p>

          <div className="flex items-center justify-between gap-2">
            <GroundTruthBadge value={clip.ground_truth} />
            <p className="text-xs text-neutral-400">ID: {clip.clip_id}</p>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs text-neutral-300">
            <div className="rounded border border-red-500/30 bg-red-950/25 p-2">
              <p className="uppercase tracking-wider text-red-300">Deception</p>
              <p className="mt-1 text-xl font-semibold">{clip.scores.deception}</p>
            </div>
            <div className="rounded border border-blue-500/30 bg-blue-950/25 p-2">
              <p className="uppercase tracking-wider text-blue-300">Sincerity</p>
              <p className="mt-1 text-xl font-semibold">{clip.scores.sincerity}</p>
            </div>
          </div>
        </div>
      </Link>
    </article>
  );
}
