import { CalibrationVisuals } from "@/components/calibration-visuals";
import { getAllClips } from "@/lib/clips";

function computeAgreement(): number {
  const clips = getAllClips();
  if (clips.length === 0) return 0;

  const correct = clips.filter((clip) => {
    const predictedFalse = clip.scores.deception >= 60;
    const expectedFalse = clip.ground_truth === "false";
    return predictedFalse === expectedFalse;
  }).length;

  return Math.round((correct / clips.length) * 100);
}

function confusionCounts() {
  const clips = getAllClips();
  let tp = 0;
  let fp = 0;
  let fn = 0;
  let tn = 0;

  clips.forEach((clip) => {
    const predictedFalse = clip.scores.deception >= 60;
    const expectedFalse = clip.ground_truth === "false";

    if (predictedFalse && expectedFalse) tp += 1;
    else if (predictedFalse && !expectedFalse) fp += 1;
    else if (!predictedFalse && expectedFalse) fn += 1;
    else tn += 1;
  });

  return { tp, fp, fn, tn };
}

export default function CalibrationPage() {
  const clips = getAllClips();
  const accuracy = computeAgreement();
  const matrix = confusionCounts();

  return (
    <div className="space-y-6">
      <header className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-6">
        <p className="text-xs uppercase tracking-[0.14em] text-neutral-400">Prototype Calibration</p>
        <h1 className="mt-2 font-serif text-4xl text-neutral-100">{accuracy}% agreement with resolved outcomes</h1>
      </header>

      <CalibrationVisuals clips={clips} />

      <section className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
        <h3 className="mb-3 font-serif text-xl text-neutral-100">Confusion Matrix</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded border border-emerald-500/40 bg-emerald-950/30 p-3 text-emerald-200">TP: {matrix.tp}</div>
          <div className="rounded border border-red-500/40 bg-red-950/30 p-3 text-red-200">FP: {matrix.fp}</div>
          <div className="rounded border border-amber-500/40 bg-amber-950/30 p-3 text-amber-200">FN: {matrix.fn}</div>
          <div className="rounded border border-blue-500/40 bg-blue-950/30 p-3 text-blue-200">TN: {matrix.tn}</div>
        </div>
      </section>

      <p className="text-sm text-neutral-400">
        Not a truth determination. A physiological signal report calibrated against public records.
      </p>
    </div>
  );
}
