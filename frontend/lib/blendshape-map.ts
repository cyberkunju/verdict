/**
 * MediaPipe FaceLandmarker emits 52 ARKit-style face blendshapes per frame.
 *
 * These are essentially numeric AU equivalents — Apple chose blendshape names
 * that line up almost 1:1 with FACS Action Units (e.g. "mouthFrownLeft" is AU15).
 *
 * This module groups them into two views the analyzer needs:
 *   - Compact AU intensities (the same names we use elsewhere in the project)
 *   - Six basic emotions (Ekman) inferred via simple weighted blend
 *
 * The emotion model is a very small heuristic — it runs every frame and is
 * intended for visualization. It is NOT a trained classifier. Use the
 * dominant emotion as a soft cue; treat absolute scores as relative.
 */

export interface NamedScore {
  categoryName: string;
  score: number;
}

const AU_GROUPS: Record<string, string[]> = {
  AU1_innerBrowRaise: ["browInnerUp"],
  AU2_outerBrowRaise: ["browOuterUpLeft", "browOuterUpRight"],
  AU4_browLower: ["browDownLeft", "browDownRight"],
  AU6_cheekRaiser: ["cheekSquintLeft", "cheekSquintRight"],
  AU7_lidTightener: ["eyeSquintLeft", "eyeSquintRight"],
  AU9_noseWrinkler: ["noseSneerLeft", "noseSneerRight"],
  AU12_lipCornerPull: ["mouthSmileLeft", "mouthSmileRight"],
  AU14_dimpler: ["mouthDimpleLeft", "mouthDimpleRight"],
  AU15_lipCornerDepressor: ["mouthFrownLeft", "mouthFrownRight"],
  AU17_chinRaiser: ["mouthShrugUpper"],
  AU20_lipStretcher: ["mouthStretchLeft", "mouthStretchRight"],
  AU24_lipPressor: ["mouthPressLeft", "mouthPressRight"],
  AU26_jawDrop: ["jawOpen"],
  AU45_blink: ["eyeBlinkLeft", "eyeBlinkRight"],
};

export type Aus = Record<keyof typeof AU_GROUPS, number>;

export function blendshapesToAUs(shapes: NamedScore[]): Aus {
  const map = new Map(shapes.map((s) => [s.categoryName, s.score]));
  const out = {} as Aus;
  for (const [au, blends] of Object.entries(AU_GROUPS)) {
    let sum = 0;
    let n = 0;
    for (const b of blends) {
      const v = map.get(b);
      if (typeof v === "number") {
        sum += v;
        n += 1;
      }
    }
    out[au as keyof Aus] = n === 0 ? 0 : sum / n;
  }
  return out;
}

export interface Emotions {
  joy: number;
  anger: number;
  sadness: number;
  fear: number;
  surprise: number;
  disgust: number;
  neutral: number;
}

const clip01 = (x: number): number => Math.max(0, Math.min(1, x));

export function emotionsFromBlendshapes(shapes: NamedScore[]): Emotions {
  const m = new Map(shapes.map((s) => [s.categoryName, s.score]));
  const get = (k: string): number => m.get(k) ?? 0;
  const avg = (...keys: string[]): number =>
    keys.reduce((s, k) => s + get(k), 0) / keys.length;

  const joy = clip01(
    avg("mouthSmileLeft", "mouthSmileRight") * 0.65 +
      avg("cheekSquintLeft", "cheekSquintRight") * 0.35,
  );

  const anger = clip01(
    avg("browDownLeft", "browDownRight") * 0.4 +
      avg("eyeSquintLeft", "eyeSquintRight") * 0.3 +
      avg("mouthPressLeft", "mouthPressRight") * 0.3,
  );

  const sadness = clip01(
    avg("mouthFrownLeft", "mouthFrownRight") * 0.55 + get("browInnerUp") * 0.45,
  );

  const fear = clip01(
    get("browInnerUp") * 0.3 +
      avg("eyeWideLeft", "eyeWideRight") * 0.4 +
      avg("mouthStretchLeft", "mouthStretchRight") * 0.3,
  );

  const surprise = clip01(
    (get("browInnerUp") + avg("browOuterUpLeft", "browOuterUpRight")) * 0.5 * 0.55 +
      get("jawOpen") * 0.45,
  );

  const disgust = clip01(
    avg("noseSneerLeft", "noseSneerRight") * 0.55 + get("mouthShrugUpper") * 0.45,
  );

  const total = joy + anger + sadness + fear + surprise + disgust;
  const neutral = clip01(1 - total);
  return { joy, anger, sadness, fear, surprise, disgust, neutral };
}

export function dominantEmotion(e: Emotions): keyof Emotions {
  let best: keyof Emotions = "neutral";
  let bestVal = -Infinity;
  for (const k of Object.keys(e) as (keyof Emotions)[]) {
    if (e[k] > bestVal) {
      bestVal = e[k];
      best = k;
    }
  }
  return best;
}
