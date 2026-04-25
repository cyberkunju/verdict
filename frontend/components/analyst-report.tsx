import { BrainCircuit } from "lucide-react";
import type { ClipReport } from "@/lib/types";

export function AnalystReport({ report }: { report: ClipReport }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <header className="mb-5 flex items-center gap-3 border-b border-slate-100 pb-4">
        <div className="rounded-full bg-slate-100 p-2">
          <BrainCircuit className="h-5 w-5 text-slate-700" aria-hidden />
        </div>
        <div>
          <h3 className="font-serif text-xl font-medium text-slate-900">LLM Analyst Synthesis</h3>
          <p className="text-xs text-slate-500">
            GPT-4o cautious behavioral report, grounded in extracted signal numbers.
          </p>
        </div>
      </header>

      <div className="space-y-5">
        <article>
          <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
            Behavioral Summary
          </p>
          <p className="text-sm leading-relaxed text-slate-700">{report.behavioral_summary}</p>
        </article>

        <article>
          <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
            Comparative Profile
          </p>
          <p className="text-sm leading-relaxed text-slate-700">{report.comparative_profile}</p>
        </article>

        <article className="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
            Qualifications
          </p>
          <p className="text-sm leading-relaxed text-slate-600">{report.qualifications}</p>
        </article>
      </div>
    </section>
  );
}
