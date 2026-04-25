"use client";
import type { Clip } from "@/lib/types";
import { ClipCard } from "./clip-card";
import { motion } from "framer-motion";

export function ArchiveGrid({ clips }: { clips: Clip[] }) {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <motion.div 
      variants={container}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-50px" }}
      className="grid gap-6 md:grid-cols-2 xl:grid-cols-3"
    >
      {clips.map((clip) => (
        <ClipCard key={clip.clip_id} clip={clip} />
      ))}
    </motion.div>
  );
}
