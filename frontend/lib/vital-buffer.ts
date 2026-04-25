/**
 * Tiny rolling time-windowed buffer.
 *
 * Stores (timestamp, value) tuples and trims anything older than `windowSeconds`
 * on every push. Cheap because the trim is amortized O(1) amortized for
 * monotonic timestamps.
 */
export class VitalBuffer<T> {
  private readonly windowMs: number;
  private buf: { t: number; v: T }[] = [];

  constructor(windowSeconds: number) {
    this.windowMs = windowSeconds * 1000;
  }

  push(value: T, timestamp: number = performance.now()): void {
    this.buf.push({ t: timestamp, v: value });
    const cutoff = timestamp - this.windowMs;
    while (this.buf.length > 0 && this.buf[0].t < cutoff) {
      this.buf.shift();
    }
  }

  values(): T[] {
    return this.buf.map((x) => x.v);
  }

  entries(): { t: number; v: T }[] {
    return this.buf.slice();
  }

  size(): number {
    return this.buf.length;
  }

  clear(): void {
    this.buf = [];
  }

  /** Statistical helpers for numeric buffers. */
  static mean(values: number[]): number {
    if (values.length === 0) return 0;
    return values.reduce((s, x) => s + x, 0) / values.length;
  }

  static stdDev(values: number[]): number {
    if (values.length === 0) return 0;
    const m = VitalBuffer.mean(values);
    const v = values.reduce((s, x) => s + (x - m) ** 2, 0) / values.length;
    return Math.sqrt(v);
  }

  static peak(values: number[]): number {
    return values.length === 0 ? 0 : Math.max(...values);
  }
}
