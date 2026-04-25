export type GroundTruth = "true" | "false" | "sincere";
export type SignalQualityFlag = "real" | "fallback" | "manual";

export interface ClipSignals {
  hr_baseline_bpm: number;
  hr_peak_bpm: number;
  hr_delta_bpm: number;
  hrv_rmssd_ms: number;
  au15_max_intensity: number;
  au14_max_intensity: number;
  au6_present: boolean;
  au24_max_intensity: number;
  f0_baseline_hz: number;
  f0_peak_hz: number;
  f0_delta_hz: number;
  jitter_percent: number;
  shimmer_db: number;
  speech_rate_wpm: number;
  hedging_count: number;
  pronoun_drop_rate: number;
  transcript: string;
  timeline: Array<{
    t: number;
    hr: number;
    f0: number;
    au15: number;
    deception: number;
  }>;
}

export interface ClipScores {
  deception: number;
  sincerity: number;
  stress: number;
  confidence: number;
}

export interface ClipReport {
  behavioral_summary: string;
  comparative_profile: string;
  qualifications: string;
}

export interface SignalQuality {
  rppg: SignalQualityFlag;
  facial_au: SignalQualityFlag;
  voice: SignalQualityFlag;
  transcript: SignalQualityFlag;
}

export interface Clip {
  schema_version: "1.0";
  clip_id: string;
  subject: string;
  statement: string;
  year: number;
  context: string;
  ground_truth: GroundTruth;
  ground_truth_source: string;
  video_url: string;
  video_start_seconds: number;
  video_end_seconds: number;
  thumbnail_url: string;
  signals: ClipSignals;
  scores: ClipScores;
  llm_report: ClipReport;
  similar_clips: string[];
  signal_quality: SignalQuality;
  text_prior?: TextPriorInference;
}

export interface SimilarArchiveMatch {
  clip_id: string;
  subject: string;
  statement: string;
  ground_truth: GroundTruth;
  similarity: number;
  scores: ClipScores;
}

export interface TextPriorInference {
  model_name: string;
  statement_used: string;
  statement_source: string;
  probability_resolved_false: number | null;
  label: "likely_false" | "uncertain" | "likely_true" | "unavailable";
  confidence: number | null;
}

export interface LiveAnalysisPayload {
  subject: string;
  statement: string;
  year: number | null;
  context: string;
  video_url: string;
  video_start_seconds: number;
  video_end_seconds: number;
  thumbnail_url: string;
  signals: ClipSignals;
  scores: ClipScores;
  llm_report: ClipReport;
  signal_quality: SignalQuality;
  similar_archive_matches: SimilarArchiveMatch[];
  text_prior?: TextPriorInference | null;
}

export interface AnalyzeAcceptedResponse {
  job_id: string;
  status: string;
  status_url: string;
  result_url: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  input_type: string;
  request: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  result_id?: string | null;
  error?: string | null;
}

export interface AnalysisResultResponse {
  result_id: string;
  job_id: string;
  status: "completed";
  payload: LiveAnalysisPayload;
}
