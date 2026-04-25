"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { Clip } from "@/lib/types";

interface CalibrationVisualsProps {
  clips: Clip[];
}

type Point = {
  clip: string;
  subject: string;
  deception: number;
  sincerity: number;
  outcome: number; // 0=sincere, 0.5=true, 1=false
  ground_truth: Clip["ground_truth"];
};

function toOutcomeValue(value: Clip["ground_truth"]): number {
  if (value === "false") return 1;
  if (value === "sincere") return 0;
  return 0.5;
}

const colorFor: Record<Clip["ground_truth"], string> = {
  false: "#ef4444",
  true: "#10b981",
  sincere: "#3b82f6",
};

const tooltipStyle = {
  background: "white",
  border: "1px solid #e2e8f0",
  borderRadius: 12,
  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
};

export function CalibrationVisuals({ clips }: CalibrationVisualsProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const points: Point[] = clips.map((clip) => ({
    clip: clip.clip_id,
    subject: clip.subject,
    deception: clip.scores.deception,
    sincerity: clip.scores.sincerity,
    outcome: toOutcomeValue(clip.ground_truth),
    ground_truth: clip.ground_truth,
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <header className="mb-4">
          <h3 className="font-serif text-xl font-medium text-slate-900">Calibration Scatter</h3>
          <p className="mt-1 text-sm text-slate-500">
            Each clip plotted as composite deception score (x-axis) vs recorded outcome (y-axis: bottom = sincere, top
            = verified false). A well-calibrated model puts red points top-right, blue points bottom-left.
          </p>
        </header>
        <div className="h-72">
          {mounted ? (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
                <CartesianGrid stroke="#f1f5f9" strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="deception"
                  name="Deception"
                  domain={[0, 100]}
                  stroke="#94a3b8"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  label={{
                    value: "Composite Deception Score",
                    position: "insideBottom",
                    offset: -2,
                    fill: "#64748b",
                    fontSize: 11,
                  }}
                />
                <YAxis
                  type="number"
                  dataKey="outcome"
                  name="Outcome"
                  domain={[0, 1]}
                  ticks={[0, 0.5, 1]}
                  tickFormatter={(v) => (v === 0 ? "sincere" : v === 0.5 ? "true" : "false")}
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  width={56}
                />
                <ZAxis range={[120, 121]} />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={tooltipStyle}
                  labelStyle={{ color: "#0f172a", fontWeight: 600 }}
                  formatter={(value, name) => {
                    if (name === "Outcome") {
                      const v = typeof value === "number" ? value : Number(value);
                      const label = v === 0 ? "sincere" : v === 0.5 ? "true" : "false";
                      return [label, "Outcome"];
                    }
                    return [String(value), String(name)];
                  }}
                />
                <Scatter data={points}>
                  {points.map((p) => (
                    <Cell key={p.clip} fill={colorFor[p.ground_truth]} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full w-full" />
          )}
        </div>
        <footer className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500">
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-red-500" /> false (denial proven false)
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> true
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-blue-500" /> sincere whistleblower
          </span>
        </footer>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-serif text-xl font-medium text-slate-900">Included Clips</h3>
        <ul className="space-y-2 text-sm text-slate-600">
          {clips.map((clip) => (
            <li
              key={clip.clip_id}
              className="rounded-xl border border-slate-100 bg-slate-50 p-3"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-slate-900">{clip.subject}</p>
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: colorFor[clip.ground_truth] }}
                  aria-label={`Ground truth: ${clip.ground_truth}`}
                />
              </div>
              <p className="mt-1 text-xs text-slate-500">{clip.ground_truth_source}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
