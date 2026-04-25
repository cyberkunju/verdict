import type { SignalQuality, SignalQualityFlag } from "@/lib/types";

const channelLabel: Record<keyof SignalQuality, string> = {
  rppg: "rPPG",
  facial_au: "Facial AU",
  voice: "Voice",
  transcript: "Transcript",
};

const flagStyle: Record<SignalQualityFlag, string> = {
  real: "border-emerald-200 bg-emerald-50 text-emerald-700",
  fallback: "border-amber-200 bg-amber-50 text-amber-700",
  manual: "border-blue-200 bg-blue-50 text-blue-700",
};

const flagDot: Record<SignalQualityFlag, string> = {
  real: "bg-emerald-500",
  fallback: "bg-amber-500",
  manual: "bg-blue-500",
};

const flagDescription: Record<SignalQualityFlag, string> = {
  real: "Extracted from source video by the named algorithm.",
  fallback: "Source quality insufficient; deterministic profile substituted.",
  manual: "Reviewed and corrected by a human curator.",
};

export function SignalQualityBadges({ quality }: { quality: SignalQuality }) {
  const channels = Object.entries(quality) as [keyof SignalQuality, SignalQualityFlag][];
  return (
    <section
      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      aria-labelledby="signal-lineage-heading"
    >
      <header className="mb-3 flex items-center justify-between">
        <h3
          id="signal-lineage-heading"
          className="font-serif text-sm font-medium uppercase tracking-[0.16em] text-slate-500"
        >
          Signal Lineage
        </h3>
        <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-400">
          per channel
        </span>
      </header>

      <div className="flex flex-wrap gap-2">
        {channels.map(([key, flag]) => (
          <span
            key={key}
            title={flagDescription[flag]}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${flagStyle[flag]}`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${flagDot[flag]}`} aria-hidden />
            <span>{channelLabel[key]}</span>
            <span className="opacity-70">· {flag}</span>
          </span>
        ))}
      </div>

      <p className="mt-3 text-xs leading-relaxed text-slate-500">
        Real signals come straight from the source video. Fallback channels use deterministic profiles when extraction
        was not possible (e.g. archival B&amp;W footage, missing face landmark model). Always check the lineage before
        treating a number as evidence.
      </p>
    </section>
  );
}
