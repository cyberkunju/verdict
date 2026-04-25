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

type Timeline = Clip["signals"]["timeline"];

const tooltipStyle = {
  background: "white",
  border: "1px solid #e2e8f0",
  borderRadius: 12,
  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
};

const tooltipLabelStyle = { color: "#0f172a", fontWeight: 600 };
const legendStyle = { fontSize: 12, color: "#475569" };

function ChartFrame({
  title,
  caption,
  children,
}: {
  title: string;
  caption: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-3 flex items-baseline justify-between gap-2">
        <h3 className="font-serif text-lg font-medium text-slate-900">{title}</h3>
        <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-400">{caption}</p>
      </header>
      <div className="h-64">{children}</div>
    </div>
  );
}

function PhysiologicalChart({ data }: { data: Timeline }) {
  return (
    <ChartFrame title="Physiological Signal" caption="HR + F0 vs time">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="#f1f5f9" strokeDasharray="3 3" />
          <XAxis
            dataKey="t"
            stroke="#94a3b8"
            tickFormatter={(v) => `${v}s`}
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            yAxisId="hr"
            stroke="#ef4444"
            domain={["auto", "auto"]}
            fontSize={12}
            width={40}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            yAxisId="f0"
            orientation="right"
            stroke="#3b82f6"
            domain={["auto", "auto"]}
            fontSize={12}
            width={40}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelStyle={tooltipLabelStyle}
            labelFormatter={(v) => `${v}s`}
            formatter={(value, name) => {
              const num = typeof value === "number" ? value : Number(value);
              const unit = name === "HR" ? "bpm" : "Hz";
              return [`${num.toFixed(1)} ${unit}`, String(name)];
            }}
          />
          <Legend wrapperStyle={legendStyle} />
          <Line
            yAxisId="hr"
            type="monotone"
            dataKey="hr"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
            name="HR"
          />
          <Line
            yAxisId="f0"
            type="monotone"
            dataKey="f0"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="F0"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function CompositeChart({ data }: { data: Timeline }) {
  return (
    <ChartFrame title="Composite Indicator" caption="Deception + AU15">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="#f1f5f9" strokeDasharray="3 3" />
          <XAxis
            dataKey="t"
            stroke="#94a3b8"
            tickFormatter={(v) => `${v}s`}
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            yAxisId="dec"
            stroke="#8b5cf6"
            domain={[0, 100]}
            fontSize={12}
            width={40}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            yAxisId="au"
            orientation="right"
            stroke="#f59e0b"
            domain={[0, 5]}
            fontSize={12}
            width={40}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelStyle={tooltipLabelStyle}
            labelFormatter={(v) => `${v}s`}
            formatter={(value, name) => {
              const num = typeof value === "number" ? value : Number(value);
              if (name === "AU15") return [num.toFixed(2), "AU15 lip corner"];
              return [num.toFixed(0), "Deception index"];
            }}
          />
          <Legend wrapperStyle={legendStyle} />
          <Line
            yAxisId="dec"
            type="monotone"
            dataKey="deception"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={false}
            name="Deception"
          />
          <Line
            yAxisId="au"
            type="monotone"
            dataKey="au15"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            name="AU15"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

export function SignalChart({ timeline }: { timeline: Timeline }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <section className="grid gap-4 lg:grid-cols-2">
        <div className="h-72 rounded-2xl border border-slate-200 bg-white" />
        <div className="h-72 rounded-2xl border border-slate-200 bg-white" />
      </section>
    );
  }

  return (
    <section
      className="grid gap-4 lg:grid-cols-2"
      aria-label="Signal timeline charts: physiological and composite indicator"
    >
      <PhysiologicalChart data={timeline} />
      <CompositeChart data={timeline} />
    </section>
  );
}
