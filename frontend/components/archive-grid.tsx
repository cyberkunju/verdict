import type { Clip } from "@/lib/types";
import { ClipCard } from "./clip-card";

export function ArchiveGrid({ clips }: { clips: Clip[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {clips.map((clip) => (
        <ClipCard key={clip.clip_id} clip={clip} />
      ))}
    </div>
  );
}
