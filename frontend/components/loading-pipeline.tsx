"use client";

import { motion } from "framer-motion";
import { CheckCircle2, CircleDashed, Loader2 } from "lucide-react";

const STAGES = [
  { key: "queued", label: "Job accepted and waiting for worker..." },
  { key: "downloading", label: "Downloading and trimming video source..." },
  { key: "trimming", label: "Trimming uploaded segment window..." },
  { key: "extracting", label: "Extracting transcript, voice, face, and rPPG signals..." },
  { key: "synthesizing", label: "Building comparative profile and analyst summary..." },
  { key: "completed", label: "Final result assembled and ready to review." },
];

export function LoadingPipeline({ status }: { status: string }) {
  const currentStage = Math.max(STAGES.findIndex((stage) => stage.key === status), 0);

  return (
    <div className="mx-auto max-w-2xl py-12">
      <div className="mb-10 text-center">
        <h2 className="font-serif text-3xl text-slate-900 mb-2">Analyzing Subject</h2>
        <p className="text-slate-500">Backend status: <span className="font-medium text-slate-700">{status}</span></p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-6">
          {STAGES.map((stage, idx) => {
            const isCompleted = currentStage > idx;
            const isCurrent = currentStage === idx;
            const isPending = currentStage < idx;

            return (
              <motion.div 
                key={stage.key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: isPending ? 0.4 : 1, x: 0 }}
                className="flex items-center gap-4"
              >
                <div className="flex-shrink-0">
                  {isCompleted && <CheckCircle2 className="h-6 w-6 text-emerald-500" />}
                  {isCurrent && <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />}
                  {isPending && <CircleDashed className="h-6 w-6 text-slate-300" />}
                </div>
                <div className="flex-1">
                  <p className={`text-sm font-medium ${isCompleted ? "text-slate-900" : isCurrent ? "text-blue-700" : "text-slate-400"}`}>
                    {stage.label}
                  </p>
                  {isCurrent && (
                    <motion.div 
                      layoutId="active-bar"
                      className="mt-2 h-1 w-full overflow-hidden rounded-full bg-slate-100"
                    >
                      <motion.div 
                        initial={{ x: "-100%" }}
                        animate={{ x: "0%" }}
                        transition={{ duration: 1.2, ease: "linear", repeat: Infinity }}
                        className="h-full bg-blue-500 w-1/2 rounded-full"
                      />
                    </motion.div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
