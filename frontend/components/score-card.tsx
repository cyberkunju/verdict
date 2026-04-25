import { AlertTriangle, Activity, Flame, ShieldCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface ScoreCardProps {
  label: string;
  value: number;
  accent: "red" | "blue" | "amber" | "green";
  hint?: string;
}

const accentClasses: Record<ScoreCardProps["accent"], string> = {
  red: "border-red-100 bg-red-50/60 text-red-700",
  blue: "border-blue-100 bg-blue-50/60 text-blue-700",
  amber: "border-amber-100 bg-amber-50/60 text-amber-700",
  green: "border-emerald-100 bg-emerald-50/60 text-emerald-700",
};

const accentIcon: Record<ScoreCardProps["accent"], LucideIcon> = {
  red: AlertTriangle,
  blue: Activity,
  amber: Flame,
  green: ShieldCheck,
};

const accentIconClass: Record<ScoreCardProps["accent"], string> = {
  red: "text-red-500",
  blue: "text-blue-500",
  amber: "text-amber-500",
  green: "text-emerald-500",
};

export function ScoreCard({ label, value, accent, hint }: ScoreCardProps) {
  const Icon = accentIcon[accent];
  return (
    <article className={`rounded-2xl border p-5 shadow-sm ${accentClasses[accent]}`}>
      <header className="mb-2 flex items-center gap-2">
        <Icon className={`h-4 w-4 ${accentIconClass[accent]}`} aria-hidden />
        <p className="text-xs font-bold uppercase tracking-[0.14em] opacity-80">{label}</p>
      </header>
      <p className="text-4xl font-bold">{value}</p>
      {hint && <p className="mt-1 text-[11px] opacity-70">{hint}</p>}
    </article>
  );
}
