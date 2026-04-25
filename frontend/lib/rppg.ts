/**
 * Browser rPPG estimator using a simplified Plane-Orthogonal-to-Skin (POS) projection.
 *
 * Reference: Wang et al. 2017, "Algorithmic Principles of Remote PPG", IEEE TBME 64(7).
 *
 * Pipeline:
 *   1. Caller provides per-frame mean R/G/B from a face ROI (forehead).
 *   2. Maintain a rolling 8-second buffer.
 *   3. Normalize each channel by its window mean.
 *   4. Project onto two orthogonal-to-skin axes:
 *        X = R_n - G_n
 *        Y = R_n + G_n - 2 * B_n
 *      Combine: signal = X + (std(X) / std(Y)) * Y
 *   5. Detrend (subtract window mean).
 *   6. Brute-force DFT over the human-HR band (0.7-3.5 Hz, i.e. 42-210 bpm).
 *      The frequency bin with maximum spectral power is the bpm estimate.
 *
 * This is a small fraction of a full rPPG pipeline (no skin-color filtering,
 * no motion compensation, no Kalman smoothing) but it gives a usable signal
 * in a controlled webcam setting (still subject, decent lighting).
 *
 * The estimator returns null until at least 4 seconds of samples are present
 * AND the signal-to-noise ratio is plausible. The caller should treat null
 * as "stabilizing" and keep the stale value visible to avoid flicker.
 */

export interface RppgSample {
  /** Wall-clock millisecond timestamp */
  t: number;
  r: number;
  g: number;
  b: number;
}

const WINDOW_SECONDS = 8;
const MIN_SAMPLES_FOR_ESTIMATE = 60; // ~2 s of frames at 30 fps

export class RppgEstimator {
  private buf: RppgSample[] = [];

  push(sample: RppgSample): void {
    this.buf.push(sample);
    const cutoff = sample.t - WINDOW_SECONDS * 1000;
    while (this.buf.length > 0 && this.buf[0].t < cutoff) {
      this.buf.shift();
    }
  }

  bufferDurationSeconds(): number {
    if (this.buf.length < 2) return 0;
    return (this.buf[this.buf.length - 1].t - this.buf[0].t) / 1000;
  }

  isReady(): boolean {
    return this.buf.length >= MIN_SAMPLES_FOR_ESTIMATE && this.bufferDurationSeconds() >= 4;
  }

  reset(): void {
    this.buf = [];
  }

  /** Estimate heart rate in bpm. Returns null when buffer is too short. */
  estimateBpm(): { bpm: number; quality: number } | null {
    if (!this.isReady()) return null;

    const N = this.buf.length;
    const R = new Float64Array(N);
    const G = new Float64Array(N);
    const B = new Float64Array(N);
    const T = new Float64Array(N);
    const t0 = this.buf[0].t;
    let mR = 0;
    let mG = 0;
    let mB = 0;
    for (let i = 0; i < N; i++) {
      R[i] = this.buf[i].r;
      G[i] = this.buf[i].g;
      B[i] = this.buf[i].b;
      T[i] = (this.buf[i].t - t0) / 1000;
      mR += R[i];
      mG += G[i];
      mB += B[i];
    }
    mR /= N;
    mG /= N;
    mB /= N;
    if (mR < 1 || mG < 1 || mB < 1) return null;

    // POS projection (Wang 2017)
    const Xs = new Float64Array(N);
    const Ys = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      const rn = R[i] / mR;
      const gn = G[i] / mG;
      const bn = B[i] / mB;
      Xs[i] = rn - gn;
      Ys[i] = rn + gn - 2 * bn;
    }
    const sX = stdDev(Xs);
    const sY = stdDev(Ys);
    if (sY < 1e-9) return null;
    const alpha = sX / sY;
    const signal = new Float64Array(N);
    let sigMean = 0;
    for (let i = 0; i < N; i++) {
      signal[i] = Xs[i] + alpha * Ys[i];
      sigMean += signal[i];
    }
    sigMean /= N;
    for (let i = 0; i < N; i++) signal[i] -= sigMean;

    // DFT scan: 42-210 bpm at 0.04 Hz (~2.4 bpm) resolution
    let bestPower = 0;
    let bestFreq = 0;
    let totalPower = 0;
    for (let f = 0.7; f <= 3.5; f += 0.04) {
      let real = 0;
      let imag = 0;
      const omega = 2 * Math.PI * f;
      for (let i = 0; i < N; i++) {
        const phase = omega * T[i];
        real += signal[i] * Math.cos(phase);
        imag -= signal[i] * Math.sin(phase);
      }
      const power = real * real + imag * imag;
      totalPower += power;
      if (power > bestPower) {
        bestPower = power;
        bestFreq = f;
      }
    }

    if (bestPower === 0 || totalPower === 0) return null;

    // Quality: dominance of peak vs total power, in [0, 1]
    const quality = Math.max(0, Math.min(1, bestPower / totalPower * 6));
    return { bpm: bestFreq * 60, quality };
  }
}

function stdDev(arr: Float64Array): number {
  const N = arr.length;
  if (N === 0) return 0;
  let m = 0;
  for (let i = 0; i < N; i++) m += arr[i];
  m /= N;
  let v = 0;
  for (let i = 0; i < N; i++) {
    const d = arr[i] - m;
    v += d * d;
  }
  return Math.sqrt(v / N);
}

/**
 * Sample mean R/G/B from a normalized ROI (forehead) of a video frame.
 * The ROI is given as fractional coordinates [0, 1] relative to the canvas.
 */
export function sampleRoiRgb(
  ctx: CanvasRenderingContext2D,
  roi: { x: number; y: number; width: number; height: number },
): { r: number; g: number; b: number } {
  const x = Math.max(0, Math.floor(roi.x));
  const y = Math.max(0, Math.floor(roi.y));
  const w = Math.max(1, Math.floor(roi.width));
  const h = Math.max(1, Math.floor(roi.height));
  const data = ctx.getImageData(x, y, w, h).data;
  let r = 0;
  let g = 0;
  let b = 0;
  const px = data.length / 4;
  for (let i = 0; i < data.length; i += 4) {
    r += data[i];
    g += data[i + 1];
    b += data[i + 2];
  }
  return { r: r / px, g: g / px, b: b / px };
}
