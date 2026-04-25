import dynamic from "next/dynamic";

/**
 * The LiveAnalyzer touches navigator.mediaDevices, AudioContext, and dynamic
 * imports MediaPipe WASM at runtime. None of that is meaningful on the server,
 * so we render it client-only with a simple loading shell.
 */
const LiveAnalyzer = dynamic(
  () => import("@/components/live-analyzer").then((m) => m.LiveAnalyzer),
  {
    ssr: false,
    loading: () => (
      <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm">
        <p className="font-serif text-2xl font-medium text-slate-900">Loading live analyzer…</p>
        <p className="mt-2 text-sm text-slate-500">
          Bringing the in-browser face + voice + rPPG pipeline online.
        </p>
      </div>
    ),
  },
);

export const metadata = {
  title: "VERDICT · Live",
  description:
    "Real-time, in-browser physiological + behavioral analysis. Webcam stays on your device.",
};

export default function LivePage() {
  return (
    <div className="space-y-6">
      <header>
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
          Live · Webcam Mode
        </p>
        <h1 className="mt-2 font-serif text-5xl font-medium tracking-tight text-slate-900">
          Ask <span className="text-slate-500">your own body</span>.
        </h1>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-slate-600">
          The same pipeline that calibrates against the historical archive — rPPG heart rate, voice
          features, action units, composite scoring — running entirely in your browser, against your
          live camera feed.
        </p>
      </header>
      <LiveAnalyzer />
    </div>
  );
}
