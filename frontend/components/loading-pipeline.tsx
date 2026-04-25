"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, CircleDashed, Loader2 } from "lucide-react";

const STAGES = [
  "Verifying video integrity (Deepfake Gate)...",
  "Extracting rPPG facial pulse data...",
  "Running OpenFace 2.0 Action Units...",
  "Analyzing vocal pitch and jitter...",
  "Generating Whisper transcript...",
  "Computing personal baseline deltas...",
  "LLM synthesizing behavioral profile..."
];

export function LoadingPipeline({ onComplete }: { onComplete: () => void }) {
  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    if (currentStage >= STAGES.length) {
      setTimeout(onComplete, 800);
      return;
    }

    // Fake variable processing times for realism
    const delay = Math.random() * 800 + 600;
    const timer = setTimeout(() => {
      setCurrentStage((prev) => prev + 1);
    }, delay);

    return () => clearTimeout(timer);
  }, [currentStage, onComplete]);

  return (
    <div className="mx-auto max-w-2xl py-12">
      <div className="mb-10 text-center">
        <h2 className="font-serif text-3xl text-slate-900 mb-2">Analyzing Subject</h2>
        <p className="text-slate-500">Extracting 7-layer physiological signals. Please wait.</p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-6">
          {STAGES.map((stage, idx) => {
            const isCompleted = currentStage > idx;
            const isCurrent = currentStage === idx;
            const isPending = currentStage < idx;

            return (
              <motion.div 
                key={stage}
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
                    {stage}
                  </p>
                  {isCurrent && (
                    <motion.div 
                      layoutId="active-bar"
                      className="mt-2 h-1 w-full overflow-hidden rounded-full bg-slate-100"
                    >
                      <motion.div 
                        initial={{ x: "-100%" }}
                        animate={{ x: "0%" }}
                        transition={{ duration: 1, ease: "linear", repeat: Infinity }}
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
