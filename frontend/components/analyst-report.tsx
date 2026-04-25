import type { ClipReport } from "@/lib/types";

export function AnalystReport({ report }: { report: ClipReport }) {
  return (
    <section className="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900/70 p-5">
      <h3 className="font-serif text-2xl text-neutral-100">LLM Analyst Report</h3>

      <article>
        <p className="mb-1 text-xs uppercase tracking-[0.14em] text-neutral-400">Behavioral Summary</p>
        <p className="text-sm leading-relaxed text-neutral-200">{report.behavioral_summary}</p>
      </article>

      <article>
        <p className="mb-1 text-xs uppercase tracking-[0.14em] text-neutral-400">Comparative Profile</p>
        <p className="text-sm leading-relaxed text-neutral-200">{report.comparative_profile}</p>
      </article>

      <article>
        <p className="mb-1 text-xs uppercase tracking-[0.14em] text-neutral-400">Qualifications</p>
        <p className="text-sm leading-relaxed text-neutral-300">{report.qualifications}</p>
      </article>
    </section>
  );
}
