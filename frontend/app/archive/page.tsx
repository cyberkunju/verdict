import { ArchiveGrid } from "@/components/archive-grid";
import { getAllClips } from "@/lib/clips";

export default function ArchivePage() {
  const clips = getAllClips();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-4xl text-neutral-100">Archive</h1>
        <p className="mt-2 text-neutral-400">
          Historical denials and testimony clips aligned to public-record outcomes.
        </p>
      </header>
      <ArchiveGrid clips={clips} />
    </div>
  );
}
