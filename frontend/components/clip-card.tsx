"use client";
import Link from "next/link";
import type { Clip } from "@/lib/types";
import { motion } from "framer-motion";

function GroundTruthBadge({ value }: { value: Clip["ground_truth"] }) {
  const style =
    value === "false"
      ? "border-red-200 bg-red-50 text-red-700"
      : value === "sincere"
        ? "border-blue-200 bg-blue-50 text-blue-700"
        : "border-emerald-200 bg-emerald-50 text-emerald-700";

  return (
    <span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${style}`}>
      {value}
    </span>
  );
}

/** Per-subject gradient background — used when thumbnail_url is empty. */
const subjectGradient: Record<string, string> = {
  nixon_1973: "from-amber-300 via-rose-400 to-red-500",
  clinton_1998: "from-sky-300 via-indigo-400 to-violet-500",
  armstrong_2005: "from-yellow-300 via-orange-400 to-amber-600",
  holmes_2018: "from-rose-300 via-pink-400 to-fuchsia-500",
  sbf_2022: "from-emerald-300 via-teal-400 to-cyan-500",
  haugen_2021: "from-blue-300 via-cyan-400 to-emerald-500",
};

function initials(subject: string): string {
  return subject
    .split(/\s+/)
    .filter(Boolean)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .slice(0, 2)
    .join("");
}

function Thumbnail({ clip }: { clip: Clip }) {
  if (clip.thumbnail_url) {
    return (
      <div
        className="h-48 w-full bg-cover bg-center transition-transform duration-500 group-hover:scale-105"
        style={{ backgroundImage: `url(${clip.thumbnail_url})` }}
        aria-hidden
      />
    );
  }
  const grad = subjectGradient[clip.clip_id] ?? "from-slate-300 via-slate-400 to-slate-600";
  return (
    <div
      className={`relative h-48 w-full overflow-hidden bg-gradient-to-br ${grad} transition-transform duration-500 group-hover:scale-105`}
      aria-hidden
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.35),transparent_55%)]" />
      <span className="absolute bottom-4 left-5 font-serif text-5xl font-bold text-white/90 drop-shadow-sm">
        {initials(clip.subject)}
      </span>
      <span className="absolute right-3 top-3 rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.14em] text-white/90 backdrop-blur">
        {clip.year}
      </span>
    </div>
  );
}

export function ClipCard({ clip }: { clip: Clip }) {
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <motion.article 
      variants={item}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="group overflow-hidden rounded-2xl border border-slate-200 bg-white transition-all hover:border-slate-300 hover:shadow-xl hover:shadow-slate-200/50"
    >
      <Link href={`/archive/${clip.clip_id}`} className="flex h-full flex-col">
        <Thumbnail clip={clip} />
        <div className="relative z-10 flex flex-1 flex-col space-y-4 bg-white p-5">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-slate-500">{clip.subject}</p>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{clip.year}</p>
          </div>

          <p className="line-clamp-2 font-serif text-xl leading-snug text-slate-900">&ldquo;{clip.statement}&rdquo;</p>

          <div className="flex items-center justify-between gap-2 pt-2">
            <GroundTruthBadge value={clip.ground_truth} />
            <p className="text-xs font-medium text-slate-400">ID: {clip.clip_id}</p>
          </div>

          <div className="mt-auto grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-xs">
            <div className="rounded-xl border border-red-100 bg-red-50/50 p-3 transition-colors group-hover:bg-red-50">
              <p className="font-semibold uppercase tracking-wider text-red-600/80">Deception</p>
              <p className="mt-1 text-2xl font-bold text-red-700">{clip.scores.deception}</p>
            </div>
            <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-3 transition-colors group-hover:bg-blue-50">
              <p className="font-semibold uppercase tracking-wider text-blue-600/80">Sincerity</p>
              <p className="mt-1 text-2xl font-bold text-blue-700">{clip.scores.sincerity}</p>
            </div>
          </div>
        </div>
      </Link>
    </motion.article>
  );
}
