/**
 * Lightweight pure-JS voice feature extraction.
 *
 *   - F0 (fundamental frequency) via normalized squared-difference autocorrelation.
 *     Cheaper than YIN proper but accurate enough for visualization. Returns null
 *     when the buffer is silent or unvoiced.
 *
 *   - RMS energy and dB level.
 *
 *   - Cycle-to-cycle jitter, computed over a rolling F0 history maintained by the caller.
 *     Returned as percent.
 *
 * All buffers are float32 in [-1, 1], typically from AnalyserNode.getFloatTimeDomainData.
 */

export interface PitchOptions {
  minF?: number;
  maxF?: number;
  /** Minimum RMS to be considered voiced; below this we return null. */
  voicedRmsThreshold?: number;
}

const DEFAULTS: Required<PitchOptions> = {
  minF: 75,
  maxF: 400,
  voicedRmsThreshold: 0.012,
};

export function rms(buffer: ArrayLike<number>): number {
  let s = 0;
  for (let i = 0; i < buffer.length; i++) s += buffer[i] * buffer[i];
  return Math.sqrt(s / buffer.length);
}

export function rmsToDb(value: number): number {
  if (value <= 1e-8) return -80;
  return Math.max(-80, 20 * Math.log10(value));
}

/**
 * Estimate fundamental frequency in Hz. Returns null when buffer is silent or unvoiced.
 */
export function detectPitch(
  buffer: ArrayLike<number>,
  sampleRate: number,
  options: PitchOptions = {},
): number | null {
  const { minF, maxF, voicedRmsThreshold } = { ...DEFAULTS, ...options };
  const energy = rms(buffer);
  if (energy < voicedRmsThreshold) return null;

  const minLag = Math.max(2, Math.floor(sampleRate / maxF));
  const maxLag = Math.min(buffer.length - 1, Math.floor(sampleRate / minF));
  if (maxLag <= minLag) return null;

  // Normalized squared-difference function, similar to YIN step 2 but unsmoothed.
  let bestLag = 0;
  let bestScore = Infinity;
  let cumulative = 0;

  for (let lag = minLag; lag <= maxLag; lag++) {
    let diff = 0;
    for (let i = 0; i < buffer.length - lag; i++) {
      const d = buffer[i] - buffer[i + lag];
      diff += d * d;
    }
    cumulative += diff;
    if (cumulative === 0) continue;
    const cmnd = diff * (lag - minLag + 1) / cumulative;
    if (cmnd < bestScore) {
      bestScore = cmnd;
      bestLag = lag;
    }
  }

  if (bestLag === 0 || bestScore > 0.4) return null; // threshold from YIN paper-ish
  // Parabolic interpolation around the best lag for sub-sample precision
  const refined = parabolicInterp(buffer, bestLag);
  return sampleRate / refined;
}

function parabolicInterp(buffer: ArrayLike<number>, lag: number): number {
  // Compute SDF at lag-1, lag, lag+1 and fit a parabola
  if (lag <= 1 || lag >= buffer.length - 2) return lag;
  const at = (k: number) => {
    let s = 0;
    for (let i = 0; i < buffer.length - k; i++) {
      const d = buffer[i] - buffer[i + k];
      s += d * d;
    }
    return s;
  };
  const a = at(lag - 1);
  const b = at(lag);
  const c = at(lag + 1);
  const denom = a - 2 * b + c;
  if (Math.abs(denom) < 1e-9) return lag;
  return lag + 0.5 * (a - c) / denom;
}

/**
 * Compute relative cycle-to-cycle jitter (percent) from a list of recent F0 samples in Hz.
 *
 * Definition (after Lieberman): mean of |T_i - T_{i+1}| / mean(T) * 100 where T_i = 1/F0_i.
 */
export function jitterPercent(f0History: number[]): number {
  if (f0History.length < 2) return 0;
  const periods = f0History.filter((f) => f > 0).map((f) => 1 / f);
  if (periods.length < 2) return 0;
  let sumDiff = 0;
  for (let i = 1; i < periods.length; i++) {
    sumDiff += Math.abs(periods[i] - periods[i - 1]);
  }
  const meanDiff = sumDiff / (periods.length - 1);
  const meanPeriod = periods.reduce((s, x) => s + x, 0) / periods.length;
  if (meanPeriod < 1e-9) return 0;
  return Math.min(20, (meanDiff / meanPeriod) * 100);
}
