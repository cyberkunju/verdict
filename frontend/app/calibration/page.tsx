import { CalibrationVisuals } from "@/components/calibration-visuals";
import { getAllClips } from "@/lib/clips";
import type { Clip } from "@/lib/types";

type Verdict = "false" | "true" | "sincere";

/**
 * Three-class predictor that mirrors the demo's narrative:
 *   - High deception (>=65) → predict "false" (denial likely false)
 *   - High sincerity   (>=65) → predict "sincere" (whistleblower path)
 *   - otherwise → predict "true" (no strong signal in either direction)
 *
 * Tuned conservatively: 65 keeps us off the 50-something noise floor.
 */
function predict(clip: Clip): Verdict {
  if (clip.scores.deception >= 65) return "false";
  if (clip.scores.sincerity >= 65) return "sincere";
  return "true";
}

function computeAgreement(clips: Clip[]): number {
  if (clips.length === 0) return 0;
  const correct = clips.filter((clip) => predict(clip) === clip.ground_truth).length;
  return Math.round((correct / clips.length) * 100);
}

interface MatrixCell {
  predicted: Verdict;
  actual: Verdict;
  count: number;
  clips: string[];
}

function buildMatrix(clips: Clip[]): MatrixCell[] {
  const verdicts: Verdict[] = ["false", "true", "sincere"];
  const cells: MatrixCell[] = [];
  for (const predicted of verdicts) {
    for (const actual of verdicts) {
      const matched = clips.filter((c) => predict(c) === predicted && c.ground_truth === actual);
      cells.push({
        predicted,
        actual,
        count: matched.length,
        clips: matched.map((c) => c.subject),
      });
    }
  }
  return cells;
}

const verdictChip: Record<Verdict, string> = {
  false: "bg-red-50 text-red-700 border-red-200",
  true: "bg-emerald-50 text-emerald-700 border-emerald-200",
  sincere: "bg-blue-50 text-blue-700 border-blue-200",
};

const verdictLabel: Record<Verdict, string> = {
  false: "False denial",
  true: "True / unverdicted",
  sincere: "Sincere whistleblower",
};

export default function CalibrationPage() {
  const clips = getAllClips();
  const accuracy = computeAgreement(clips);
  const matrix = buildMatrix(clips);

  const verdicts: Verdict[] = ["false", "true", "sincere"];
  const correct = matrix.filter((c) => c.predicted === c.actual).reduce((s, c) => s + c.count, 0);
  const incorrect = clips.length - correct;

  return (
    <div className="space-y-8">
      <header className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500">
          Prototype Calibration
        </p>
        <h1 className="mt-2 font-serif text-5xl font-medium text-slate-900">
          {accuracy}% <span className="text-slate-400">agreement</span>
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-600">
          {correct} of {clips.length} clips align the predicted three-class verdict (false / true / sincere) with the
          recorded historical outcome. {incorrect} disagree. With a sample of six, this is a sanity check, not a
          benchmark.
        </p>
      </header>

      <CalibrationVisuals clips={clips} />

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <header className="mb-4">
          <h3 className="font-serif text-xl font-medium text-slate-900">Confusion Matrix (3-class)</h3>
          <p className="mt-1 text-sm text-slate-500">
            Rows are model predictions, columns are recorded outcomes. The diagonal is correct.
          </p>
        </header>

        <div className="overflow-x-auto">
          <table className="w-full border-separate border-spacing-1 text-sm">
            <thead>
              <tr>
                <th className="text-left text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">
                  Predicted ↓ / Actual →
                </th>
                {verdicts.map((v) => (
                  <th key={v} className="px-2 py-1 text-center">
                    <span
                      className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${verdictChip[v]}`}
                    >
                      {verdictLabel[v]}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {verdicts.map((predicted) => (
                <tr key={predicted}>
                  <th
                    scope="row"
                    className="text-left align-top whitespace-nowrap px-2 py-2"
                  >
                    <span
                      className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${verdictChip[predicted]}`}
                    >
                      {verdictLabel[predicted]}
                    </span>
                  </th>
                  {verdicts.map((actual) => {
                    const cell = matrix.find(
                      (c) => c.predicted === predicted && c.actual === actual,
                    );
                    const count = cell?.count ?? 0;
                    const isDiagonal = predicted === actual;
                    const isHit = count > 0;
                    const tone = isDiagonal && isHit
                      ? "border-emerald-200 bg-emerald-50"
                      : !isDiagonal && isHit
                      ? "border-red-200 bg-red-50"
                      : "border-slate-100 bg-slate-50";
                    const numberTone = isDiagonal && isHit
                      ? "text-emerald-700"
                      : !isDiagonal && isHit
                      ? "text-red-700"
                      : "text-slate-400";
                    return (
                      <td key={actual} className="align-top">
                        <div className={`min-h-[80px] rounded-xl border p-3 ${tone}`}>
                          <p className={`text-2xl font-bold ${numberTone}`}>{count}</p>
                          {cell?.clips.length ? (
                            <ul className="mt-1 space-y-0.5 text-[11px] text-slate-600">
                              {cell.clips.map((s) => (
                                <li key={s}>{s}</li>
                              ))}
                            </ul>
                          ) : null}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm italic leading-relaxed text-slate-600">
        Not a truth determination. A physiological signal report calibrated against public records. Six-clip pilot —
        treat agreement percentages as a smoke test, not a benchmark.
      </p>
    </div>
  );
}
