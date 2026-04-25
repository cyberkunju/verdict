"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Clip } from "@/lib/types";

interface CalibrationVisualsProps {
  clips: Clip[];
}

type Point = {
  clip: string;
  deception: number;
  outcome: number;
};

function toOutcomeValue(value: Clip["ground_truth"]): number {
  if (value === "false") return 1;
  if (value === "sincere") return 0;
  return 0.5;
}

export function CalibrationVisuals({ clips }: CalibrationVisualsProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const points: Point[] = clips.map((clip) => ({
    clip: clip.clip_id,
    deception: clip.scores.deception,
    outcome: toOutcomeValue(clip.ground_truth),
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
      <section className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
        <h3 className="mb-3 font-serif text-xl text-neutral-100">Calibration Scatter</h3>
        <div className="h-72">
          {mounted ? (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid stroke="#2d2d2d" strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="deception"
                  name="Deception"
                  domain={[0, 100]}
                  stroke="#a3a3a3"
                />
                <YAxis
                  type="number"
                  dataKey="outcome"
                  name="Outcome"
                  domain={[0, 1]}
                  ticks={[0, 0.5, 1]}
                  stroke="#a3a3a3"
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={{ background: "#171717", border: "1px solid #404040", borderRadius: 8 }}
                />
                <Scatter data={points} fill="#ef4444" />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full w-full" />
          )}
        </div>
      </section>

      <section className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
        <h3 className="mb-3 font-serif text-xl text-neutral-100">Included Clips</h3>
        <ul className="space-y-2 text-sm text-neutral-300">
          {clips.map((clip) => (
            <li key={clip.clip_id} className="rounded border border-neutral-800 bg-neutral-950/70 p-2">
              <p className="font-medium text-neutral-200">{clip.subject}</p>
              <p className="text-xs text-neutral-400">{clip.ground_truth_source}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
