import mock from "./mock-clips";
import realData from "../public/data/all_clips.json";
import type { Clip } from "./types";

// Round 4: real backend pipeline ships canonical signals + GPT-4o reports.
// Set to true only as a build-time fallback if `npm run sync-data` was never run.
export const USE_MOCK = false;

const real = (Array.isArray(realData) ? realData : []) as Clip[];
const source: Clip[] = USE_MOCK || real.length === 0 ? mock : real;

export function getAllClips(): Clip[] {
  return source;
}

export function getClip(id: string): Clip | undefined {
  return source.find((clip) => clip.clip_id === id);
}

/** True when the build is rendering real pipeline data (not the static mock). */
export const isRealData = !USE_MOCK && real.length > 0;
