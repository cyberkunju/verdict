interface ScoreCardProps {
  label: string;
  value: number;
  accent: "red" | "blue" | "amber" | "green";
}

const accentClasses: Record<ScoreCardProps["accent"], string> = {
  red: "text-red-400 border-red-500/30 bg-red-950/30",
  blue: "text-blue-300 border-blue-500/30 bg-blue-950/30",
  amber: "text-amber-300 border-amber-500/30 bg-amber-950/30",
  green: "text-emerald-300 border-emerald-500/30 bg-emerald-950/30",
};

export function ScoreCard({ label, value, accent }: ScoreCardProps) {
  return (
    <article className={`rounded-xl border p-4 ${accentClasses[accent]}`}>
      <p className="text-xs uppercase tracking-[0.12em] opacity-80">{label}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
    </article>
  );
}
