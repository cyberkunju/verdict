/**
 * Composite scoring for the live webcam analyzer.
 *
 * Takes a snapshot of currently-extracted signals and returns four 0-100 scores
 * that mirror the archive schema: deception, sincerity, stress, confidence.
 *
 * The weighted blend is intentionally simple and transparent. Every term is
 * rooted in published correlates of arousal or affect, but the weights here
 * are heuristic — this is a visualization model, not a trained classifier.
 */
import type { Clip } from "@/lib/types";
import type { Aus, Emotions } from "@/lib/blendshape-map";

export interface LiveSignals {
  /** Most recent rPPG bpm estimate, or null while warming up. */
  hrBpm: number | null;
  /** Resting baseline established during the calibration window. */
  hrBaselineBpm: number | null;
  /** Most recent voiced F0 in Hz, or null when silent. */
  f0Hz: number | null;
  f0BaselineHz: number | null;
  /** Voice jitter as a percent (0-20). */
  jitterPercent: number;
  /** RMS audio energy in [0, 1]. */
  rmsEnergy: number;
  aus: Aus;
  emotions: Emotions;
  /** Number of hedge words detected in the live transcript. */
  hedgeCount: number;
  /** Estimated speech rate in words per minute. */
  speechRateWpm: number;
}

export interface LiveScores {
  deception: number;
  sincerity: number;
  stress: number;
  confidence: number;
}

const nmap = (x: number, lo: number, hi: number): number =>
  Math.max(0, Math.min(1, (x - lo) / (hi - lo)));

export function computeLiveScores(s: LiveSignals): LiveScores {
  const hrDelta = s.hrBpm != null && s.hrBaselineBpm != null ? s.hrBpm - s.hrBaselineBpm : 0;
  const f0Delta = s.f0Hz != null && s.f0BaselineHz != null ? Math.abs(s.f0Hz - s.f0BaselineHz) : 0;

  const deception = clamp01(
    0.30 * nmap(hrDelta, 0, 25) +
      0.20 * nmap(f0Delta, 0, 50) +
      0.20 * (s.aus.AU15_lipCornerDepressor ?? 0) +
      0.15 * (s.aus.AU14_dimpler ?? 0) +
      0.15 * nmap(s.jitterPercent, 0, 5),
  );

  const sincerity = clamp01(
    0.30 * (s.aus.AU12_lipCornerPull ?? 0) +
      0.20 * (s.aus.AU6_cheekRaiser ?? 0) +
      0.20 * (1 - (s.aus.AU24_lipPressor ?? 0)) +
      0.15 * (1 - nmap(hrDelta, 0, 25)) +
      0.15 * (1 - nmap(s.hedgeCount, 0, 5)),
  );

  const stress = clamp01(
    0.40 * nmap(s.jitterPercent, 0, 5) +
      0.30 * nmap(hrDelta, 0, 25) +
      0.20 * (s.aus.AU7_lidTightener ?? 0) +
      0.10 * (s.aus.AU24_lipPressor ?? 0),
  );

  const confidence = clamp01(
    0.40 * nmap(s.speechRateWpm, 100, 200) +
      0.30 * (1 - nmap(s.hedgeCount, 0, 5)) +
      0.20 * (1 - (s.emotions.fear ?? 0)) +
      0.10 * (1 - nmap(s.jitterPercent, 0, 5)),
  );

  return {
    deception: Math.round(deception * 100),
    sincerity: Math.round(sincerity * 100),
    stress: Math.round(stress * 100),
    confidence: Math.round(confidence * 100),
  };
}

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

/**
 * Find the archive clip whose 4-D score profile is closest to the live profile.
 * Useful as a "your signal pattern most resembles X" demo flourish — purely
 * comparative, never a truthfulness claim.
 */
export function findClosestArchive(
  live: LiveScores,
  archive: Clip[],
): { clip: Clip; distance: number } | null {
  if (archive.length === 0) return null;
  let best = archive[0];
  let bestD = scoreDistance(live, best.scores);
  for (let i = 1; i < archive.length; i++) {
    const d = scoreDistance(live, archive[i].scores);
    if (d < bestD) {
      bestD = d;
      best = archive[i];
    }
  }
  return { clip: best, distance: bestD };
}

function scoreDistance(a: LiveScores, b: { deception: number; sincerity: number; stress: number; confidence: number }): number {
  return Math.sqrt(
    (a.deception - b.deception) ** 2 +
      (a.sincerity - b.sincerity) ** 2 +
      (a.stress - b.stress) ** 2 +
      (a.confidence - b.confidence) ** 2,
  );
}

/**
 * Hedge-word detector for the live transcript.
 * Cheap regex match; case-insensitive whole-word.
 */
const HEDGE_PATTERN =
  /\b(maybe|possibly|perhaps|sort of|kind of|i guess|i think|probably|i mean|you know|like|honestly|actually|to be fair|i suppose|might|could be)\b/gi;

export function countHedges(transcript: string): number {
  if (!transcript) return 0;
  const matches = transcript.match(HEDGE_PATTERN);
  return matches ? matches.length : 0;
}

/**
 * Speech rate in words per minute, computed across a transcript window
 * spanning `durationSeconds`. Returns 0 for short windows to avoid spikes.
 */
export function computeSpeechRateWpm(transcript: string, durationSeconds: number): number {
  if (!transcript || durationSeconds < 3) return 0;
  const words = transcript.trim().split(/\s+/).filter(Boolean);
  return Math.round((words.length / durationSeconds) * 60);
}
