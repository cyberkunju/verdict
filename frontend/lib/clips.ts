import mock from "./mock-clips";
import realData from "../public/data/all_clips.json";
import type { Clip } from "./types";

export const USE_MOCK = true;

const real = (Array.isArray(realData) ? realData : []) as Clip[];
const source: Clip[] = USE_MOCK || real.length === 0 ? mock : real;

export function getAllClips(): Clip[] {
  return source;
}

export function getClip(id: string): Clip | undefined {
  return source.find((clip) => clip.clip_id === id);
}
