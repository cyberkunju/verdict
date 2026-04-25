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
      <Link href={`/archive/${clip.clip_id}`} className="block h-full flex flex-col">
        <div className="h-48 w-full bg-cover bg-center transition-transform duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${clip.thumbnail_url})` }} />
        <div className="flex flex-col flex-1 space-y-4 p-5 bg-white relative z-10">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-slate-500">{clip.subject}</p>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{clip.year}</p>
          </div>

          <p className="line-clamp-2 font-serif text-xl leading-snug text-slate-900">“{clip.statement}”</p>

          <div className="flex items-center justify-between gap-2 pt-2">
            <GroundTruthBadge value={clip.ground_truth} />
            <p className="text-xs font-medium text-slate-400">ID: {clip.clip_id}</p>
          </div>

          <div className="mt-auto grid grid-cols-2 gap-3 text-xs pt-4 border-t border-slate-100">
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
