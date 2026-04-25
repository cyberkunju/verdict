"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Clip } from "@/lib/types";

export function SignalChart({ timeline }: { timeline: Clip["signals"]["timeline"] }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="h-80 rounded-xl border border-neutral-800 bg-neutral-900/70 p-4" />;
  }

  return (
    <div className="h-80 rounded-xl border border-neutral-800 bg-neutral-900/70 p-4">
      <h3 className="mb-4 font-serif text-xl text-neutral-100">Signal Timeline</h3>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={timeline}>
          <CartesianGrid stroke="#2d2d2d" strokeDasharray="3 3" />
          <XAxis dataKey="t" stroke="#a3a3a3" />
          <YAxis stroke="#a3a3a3" />
          <Tooltip
            contentStyle={{ background: "#171717", border: "1px solid #404040", borderRadius: 8 }}
            labelStyle={{ color: "#f5f5f5" }}
          />
          <Legend />
          <Line type="monotone" dataKey="hr" stroke="#ef4444" strokeWidth={2} dot={false} name="HR" />
          <Line type="monotone" dataKey="f0" stroke="#60a5fa" strokeWidth={2} dot={false} name="F0" />
          <Line type="monotone" dataKey="au15" stroke="#f59e0b" strokeWidth={2} dot={false} name="AU15" />
          <Line
            type="monotone"
            dataKey="deception"
            stroke="#a855f7"
            strokeWidth={2}
            dot={false}
            name="Deception"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
