"use client";

import { useEffect, useRef } from "react";

/* ────────────────────────────────────────────────────────────
 * Sparkline — fixed-width SVG line of recent values [0, max].
 * ──────────────────────────────────────────────────────────── */

export function Sparkline({
  data,
  height = 40,
  stroke = "#0f172a",
  fill = "none",
  ariaLabel,
}: {
  data: number[];
  height?: number;
  stroke?: string;
  fill?: string;
  ariaLabel?: string;
}) {
  const width = 200;
  if (data.length === 0) {
    return (
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" aria-label={ariaLabel}>
        <line x1="0" y1={height / 2} x2={width} y2={height / 2} stroke="#e2e8f0" strokeDasharray="3 3" />
      </svg>
    );
  }
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = Math.max(1e-6, max - min);
  const stepX = data.length > 1 ? width / (data.length - 1) : width;
  const points = data
    .map((v, i) => {
      const x = i * stepX;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" aria-label={ariaLabel}>
      <polyline points={points} fill={fill} stroke={stroke} strokeWidth={1.5} strokeLinejoin="round" />
    </svg>
  );
}

/* ────────────────────────────────────────────────────────────
 * VitalCard — labeled card with big value, sub-label, sparkline.
 * ──────────────────────────────────────────────────────────── */

export function VitalCard({
  label,
  value,
  unit,
  hint,
  history,
  accent = "slate",
  status,
}: {
  label: string;
  value: string | number;
  unit?: string;
  hint?: string;
  history?: number[];
  accent?: "slate" | "red" | "blue" | "amber" | "emerald" | "violet";
  status?: "ok" | "warming" | "off";
}) {
  const colors: Record<NonNullable<typeof accent>, { stroke: string; chip: string; text: string }> = {
    slate: { stroke: "#0f172a", chip: "bg-slate-100 text-slate-600", text: "text-slate-900" },
    red: { stroke: "#ef4444", chip: "bg-red-50 text-red-600", text: "text-red-700" },
    blue: { stroke: "#3b82f6", chip: "bg-blue-50 text-blue-600", text: "text-blue-700" },
    amber: { stroke: "#f59e0b", chip: "bg-amber-50 text-amber-700", text: "text-amber-700" },
    emerald: { stroke: "#10b981", chip: "bg-emerald-50 text-emerald-700", text: "text-emerald-700" },
    violet: { stroke: "#8b5cf6", chip: "bg-violet-50 text-violet-700", text: "text-violet-700" },
  };
  const c = colors[accent];
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <header className="mb-1 flex items-center justify-between">
        <p className={`text-[10px] font-bold uppercase tracking-[0.16em] ${c.chip} rounded-full px-2 py-0.5`}>
          {label}
        </p>
        {status && (
          <span
            className={`text-[10px] font-medium ${
              status === "ok"
                ? "text-emerald-600"
                : status === "warming"
                  ? "text-amber-600"
                  : "text-slate-400"
            }`}
          >
            {status === "ok" ? "● live" : status === "warming" ? "○ stabilizing" : "—"}
          </span>
        )}
      </header>
      <p className={`mt-1 font-serif text-3xl font-medium tabular-nums ${c.text}`}>
        {value}
        {unit && <span className="ml-1 text-base text-slate-400">{unit}</span>}
      </p>
      {hint && <p className="mt-0.5 text-[11px] text-slate-500">{hint}</p>}
      {history && (
        <div className="mt-2 h-10">
          <Sparkline data={history} stroke={c.stroke} ariaLabel={`${label} sparkline`} />
        </div>
      )}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
 * BarRow — labeled progress bar (used for AUs and emotions).
 * ──────────────────────────────────────────────────────────── */

export function BarRow({
  label,
  value,
  max = 1,
  color = "slate",
}: {
  label: string;
  value: number;
  max?: number;
  color?: "slate" | "red" | "blue" | "emerald" | "amber" | "violet" | "rose";
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const fill: Record<typeof color, string> = {
    slate: "bg-slate-700",
    red: "bg-red-500",
    blue: "bg-blue-500",
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
    violet: "bg-violet-500",
    rose: "bg-rose-500",
  } as const;
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 shrink-0 text-[11px] font-medium text-slate-600">{label}</span>
      <div className="relative h-2 flex-1 rounded-full bg-slate-100 overflow-hidden">
        <div
          className={`h-full rounded-full transition-[width] duration-300 ${fill[color]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 shrink-0 text-right text-[11px] tabular-nums text-slate-500">
        {pct.toFixed(0)}
      </span>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
 * TruthGauge — radial oracle dial driven by composite score.
 *
 * Renders an SVG arc from -120deg to +120deg. Needle position is
 * driven by `value` in [0, 100]. Color smoothly blends from
 * emerald (low arousal/sincere) through amber (mixed) to red
 * (high arousal). Animated by canvas requestAnimationFrame for
 * smoothness without re-rendering React tree.
 * ──────────────────────────────────────────────────────────── */

export function TruthGauge({
  value,
  label = "Composite signal",
}: {
  value: number; // 0-100
  label?: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animatedValueRef = useRef(value);

  useEffect(() => {
    let mounted = true;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio ?? 1;
    const size = 220;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    const draw = (val: number) => {
      ctx.clearRect(0, 0, size, size);
      const cx = size / 2;
      const cy = size / 2 + 16;
      const radius = 84;
      const start = Math.PI * 0.85;
      const end = Math.PI * 2.15;

      // Background arc
      ctx.beginPath();
      ctx.arc(cx, cy, radius, start, end);
      ctx.lineWidth = 14;
      ctx.strokeStyle = "#e2e8f0";
      ctx.lineCap = "round";
      ctx.stroke();

      // Foreground arc with value-based color
      const t = Math.max(0, Math.min(1, val / 100));
      const angle = start + (end - start) * t;
      const grad = ctx.createLinearGradient(cx - radius, cy, cx + radius, cy);
      grad.addColorStop(0, "#10b981"); // emerald
      grad.addColorStop(0.5, "#f59e0b"); // amber
      grad.addColorStop(1, "#ef4444"); // red
      ctx.beginPath();
      ctx.arc(cx, cy, radius, start, angle);
      ctx.lineWidth = 14;
      ctx.strokeStyle = grad;
      ctx.lineCap = "round";
      ctx.stroke();

      // Center value text
      ctx.fillStyle = "#0f172a";
      ctx.font = "600 38px Playfair Display, serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(val.toFixed(0), cx, cy - 4);

      ctx.fillStyle = "#64748b";
      ctx.font = "500 11px Inter, sans-serif";
      ctx.fillText(label.toUpperCase(), cx, cy + 28);
    };

    let rafId = 0;
    const tick = () => {
      if (!mounted) return;
      animatedValueRef.current = animatedValueRef.current + (value - animatedValueRef.current) * 0.12;
      draw(animatedValueRef.current);
      rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
    return () => {
      mounted = false;
      cancelAnimationFrame(rafId);
    };
  }, [value, label]);

  return <canvas ref={canvasRef} aria-label={`${label} gauge: ${value.toFixed(0)} of 100`} />;
}
