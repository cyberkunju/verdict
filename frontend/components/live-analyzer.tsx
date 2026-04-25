"use client";

/**
 * Live Webcam Analyzer
 *
 * Runs four signal pipelines in the browser, in parallel:
 *
 *   1. Face landmarks + 52 ARKit-style blendshapes via MediaPipe FaceLandmarker
 *      (loaded from CDN at runtime; WASM + 3 MB model).
 *   2. rPPG heart-rate estimate via the POS algorithm against a 60×30 px
 *      forehead ROI sampled every animation frame, FFT-scanned every second.
 *   3. Voice F0 + RMS + jitter via a MediaStream → AnalyserNode → autocorrelation
 *      pipeline running at ~60 Hz (driven by the same RAF loop).
 *   4. Live transcript via Web Speech API where available (Chrome/Edge); we
 *      degrade silently otherwise.
 *
 * All processing is in-browser. No network calls beyond the initial WASM/model
 * download. The component is a state machine with five phases:
 *
 *   idle → starting → running → recording → reviewing
 *
 * High-frequency signal values are kept in refs to avoid re-rendering React on
 * every frame; we sync them to display state at 10 Hz and recompute composite
 * scores at 1 Hz.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Camera,
  CircleStop,
  Mic,
  MicOff,
  RotateCcw,
  ShieldCheck,
  Video,
  VideoOff,
} from "lucide-react";
import type { FaceLandmarker, FaceLandmarkerResult } from "@mediapipe/tasks-vision";
import { BarRow, Sparkline, TruthGauge, VitalCard } from "@/components/live-meter";
import { LiveSummary, type LiveRecordingSummary } from "@/components/live-summary";
import {
  blendshapesToAUs,
  dominantEmotion,
  emotionsFromBlendshapes,
  type Aus,
  type Emotions,
} from "@/lib/blendshape-map";
import {
  computeLiveScores,
  computeSpeechRateWpm,
  countHedges,
  findClosestArchive,
  type LiveScores,
} from "@/lib/composite-scores";
import { detectPitch, jitterPercent, rms, rmsToDb } from "@/lib/audio-features";
import { RppgEstimator, sampleRoiRgb } from "@/lib/rppg";
import { VitalBuffer } from "@/lib/vital-buffer";
import { getAllClips } from "@/lib/clips";

type Phase = "idle" | "starting" | "running" | "recording" | "reviewing" | "error";

const ZERO_AUS: Aus = {
  AU1_innerBrowRaise: 0,
  AU2_outerBrowRaise: 0,
  AU4_browLower: 0,
  AU6_cheekRaiser: 0,
  AU7_lidTightener: 0,
  AU9_noseWrinkler: 0,
  AU12_lipCornerPull: 0,
  AU14_dimpler: 0,
  AU15_lipCornerDepressor: 0,
  AU17_chinRaiser: 0,
  AU20_lipStretcher: 0,
  AU24_lipPressor: 0,
  AU26_jawDrop: 0,
  AU45_blink: 0,
};

const ZERO_EMOTIONS: Emotions = {
  joy: 0,
  anger: 0,
  sadness: 0,
  fear: 0,
  surprise: 0,
  disgust: 0,
  neutral: 1,
};

const ZERO_SCORES: LiveScores = { deception: 0, sincerity: 0, stress: 0, confidence: 0 };

const CALIBRATION_SECONDS = 12;
const SPARK_WINDOW_SECONDS = 30;
const FOREHEAD_LANDMARKS = [10, 109, 338, 151] as const;

/** Web Speech API isn't in the default DOM lib; declare a minimal interface. */
interface SpeechRecognitionAlternative {
  readonly transcript: string;
  readonly confidence: number;
}
interface SpeechRecognitionResult {
  readonly isFinal: boolean;
  readonly length: number;
  readonly [index: number]: SpeechRecognitionAlternative;
}
interface SpeechRecognitionResultList {
  readonly length: number;
  readonly [index: number]: SpeechRecognitionResult;
}
interface SpeechRecognitionEvent {
  readonly resultIndex: number;
  readonly results: SpeechRecognitionResultList;
}
interface SpeechRecognitionErrorEvent {
  readonly error: string;
  readonly message: string;
}
type SpeechRecognitionLike = EventTarget & {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((e: SpeechRecognitionEvent) => void) | null;
  onerror: ((e: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
};

declare global {
  interface Window {
    SpeechRecognition?: { new (): SpeechRecognitionLike };
    webkitSpeechRecognition?: { new (): SpeechRecognitionLike };
  }
}

export function LiveAnalyzer() {
  /* ─── State (low-frequency UI) ─────────────────────────────── */
  const [phase, setPhase] = useState<Phase>("idle");
  const [errorInfo, setErrorInfo] = useState<{ step: string; name: string; message: string } | null>(null);
  const [hasMedia, setHasMedia] = useState({ video: false, audio: false });

  const [hrBpm, setHrBpm] = useState<number | null>(null);
  const [hrQuality, setHrQuality] = useState(0);
  const [hrBaseline, setHrBaseline] = useState<number | null>(null);
  const [f0Hz, setF0Hz] = useState<number | null>(null);
  const [f0Baseline, setF0Baseline] = useState<number | null>(null);
  const [rmsDb, setRmsDb] = useState(-80);
  const [jitterPct, setJitterPct] = useState(0);

  const [aus, setAus] = useState<Aus>(ZERO_AUS);
  const [emotions, setEmotions] = useState<Emotions>(ZERO_EMOTIONS);
  const [scores, setScores] = useState<LiveScores>(ZERO_SCORES);

  const [transcript, setTranscript] = useState("");
  const [calibProgress, setCalibProgress] = useState(0);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [summary, setSummary] = useState<LiveRecordingSummary | null>(null);

  const [hrSpark, setHrSpark] = useState<number[]>([]);
  const [f0Spark, setF0Spark] = useState<number[]>([]);
  const [decSpark, setDecSpark] = useState<number[]>([]);

  /* ─── Refs (high-frequency data) ───────────────────────────── */
  const videoRef = useRef<HTMLVideoElement>(null);
  const sampleCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const landmarkerRef = useRef<FaceLandmarker | null>(null);
  const rppgRef = useRef(new RppgEstimator());
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioBufRef = useRef<Float32Array<ArrayBuffer> | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);

  const ausRef = useRef<Aus>(ZERO_AUS);
  const emotionsRef = useRef<Emotions>(ZERO_EMOTIONS);
  const f0Ref = useRef<number | null>(null);
  const rmsRef = useRef(0);
  const f0HistoryRef = useRef<number[]>([]);
  const transcriptRef = useRef("");
  const finalTranscriptRef = useRef("");

  const calibStartRef = useRef<number | null>(null);
  const recordStartRef = useRef<number | null>(null);
  const recordSummaryAccumRef = useRef<{
    hrSamples: number[];
    f0Samples: number[];
    auSamples: Aus[];
    emotionSamples: Emotions[];
  }>({ hrSamples: [], f0Samples: [], auSamples: [], emotionSamples: [] });

  const hrBufferRef = useRef(new VitalBuffer<number>(SPARK_WINDOW_SECONDS));
  const f0BufferRef = useRef(new VitalBuffer<number>(SPARK_WINDOW_SECONDS));
  const decBufferRef = useRef(new VitalBuffer<number>(SPARK_WINDOW_SECONDS));

  const rafRef = useRef(0);
  const lowFreqTickRef = useRef(0);
  const compositeTickRef = useRef(0);
  const phaseRef = useRef<Phase>("idle");
  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  const archive = useMemo(() => getAllClips(), []);

  /* ─── 1) Open webcam + audio ────────────────────────────────── */
  const startMedia = useCallback(async () => {
    setErrorInfo(null);
    setPhase("starting");

    /** Run a labeled step; if it throws, capture step name + error type and rethrow. */
    const step = async <T,>(name: string, fn: () => Promise<T> | T): Promise<T> => {
      try {
        return await fn();
      } catch (err) {
        console.error(`[live] step "${name}" failed:`, err);
        const e = err as { name?: string; message?: string; toString?: () => string };
        const errName = e?.name ?? (err instanceof Error ? "Error" : typeof err);
        const errMsg =
          e?.message ??
          (typeof err === "string" ? err : err && typeof err === "object" ? JSON.stringify(err).slice(0, 200) : String(err));
        setErrorInfo({ step: name, name: String(errName), message: String(errMsg) });
        throw err;
      }
    };

    try {
      if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
        throw new Error("Your browser does not expose getUserMedia. Use Chrome, Edge, or Firefox.");
      }

      const stream = await step("camera + microphone", () =>
        navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } },
          audio: true,
        }),
      );
      streamRef.current = stream;
      setHasMedia({
        video: stream.getVideoTracks().length > 0,
        audio: stream.getAudioTracks().length > 0,
      });

      await step("video element", async () => {
        const video = videoRef.current;
        if (!video) throw new Error("Video element missing from DOM.");
        video.srcObject = stream;
        await video.play();
        const w = video.videoWidth || 640;
        const h = video.videoHeight || 480;
        const sampleCanvas = document.createElement("canvas");
        sampleCanvas.width = w;
        sampleCanvas.height = h;
        sampleCanvasRef.current = sampleCanvas;
        const overlay = overlayCanvasRef.current;
        if (overlay) {
          overlay.width = w;
          overlay.height = h;
        }
      });

      await step("audio pipeline", () => {
        const AudioCtx: typeof AudioContext =
          (window.AudioContext as typeof AudioContext) ||
          ((window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext);
        const ctx = new AudioCtx();
        audioCtxRef.current = ctx;
        const src = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.0;
        src.connect(analyser);
        analyserRef.current = analyser;
        audioBufRef.current = new Float32Array(analyser.fftSize);
        sourceNodeRef.current = src;
      });

      // Speech recognition is best-effort and never fatal
      const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition;
      if (SR) {
        const rec = new SR();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = "en-US";
        rec.onresult = (e: SpeechRecognitionEvent) => {
          let interim = "";
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const text = e.results[i][0].transcript;
            if (e.results[i].isFinal) {
              finalTranscriptRef.current += text + " ";
            } else {
              interim += text;
            }
          }
          transcriptRef.current = (finalTranscriptRef.current + " " + interim).trim();
        };
        rec.onend = () => {
          if (phaseRef.current === "running" || phaseRef.current === "recording") {
            try {
              rec.start();
            } catch {
              /* ignore */
            }
          }
        };
        rec.onerror = () => {
          /* swallow; transcript is best-effort */
        };
        try {
          rec.start();
          recognitionRef.current = rec;
        } catch {
          recognitionRef.current = null;
        }
      }

      await step("face model", () => loadLandmarker());
      calibStartRef.current = performance.now();
      setPhase("running");
      runLoop();
    } catch {
      // step() already populated errorInfo; just clean up
      setPhase("error");
      cleanupMedia();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ─── 2) Load MediaPipe FaceLandmarker (CDN-hosted assets) ──── */
  const loadLandmarker = useCallback(async () => {
    if (landmarkerRef.current) return;
    const { FilesetResolver, FaceLandmarker: FL } = await import("@mediapipe/tasks-vision");
    // The WASM runtime version MUST match the npm-installed JS wrapper version.
    // Pin to 0.10.34 (currently in package-lock.json). If you bump the npm pkg,
    // bump this URL too.
    const fileset = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.34/wasm",
    );
    const lm = await FL.createFromOptions(fileset, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        delegate: "GPU",
      },
      outputFaceBlendshapes: true,
      outputFacialTransformationMatrixes: false,
      runningMode: "VIDEO",
      numFaces: 1,
    });
    landmarkerRef.current = lm;
  }, []);

  /* ─── 3) Animation-frame loop: face + ROI + audio ──────────── */
  const runLoop = useCallback(() => {
    const tick = () => {
      const phaseNow = phaseRef.current;
      if (phaseNow !== "running" && phaseNow !== "recording") return;
      const video = videoRef.current;
      const sampleCanvas = sampleCanvasRef.current;
      const overlay = overlayCanvasRef.current;
      const lm = landmarkerRef.current;

      if (video && sampleCanvas && lm && video.readyState >= 2) {
        const ctx = sampleCanvas.getContext("2d", { willReadFrequently: true });
        if (ctx) {
          ctx.drawImage(video, 0, 0, sampleCanvas.width, sampleCanvas.height);

          let result: FaceLandmarkerResult | null = null;
          try {
            result = lm.detectForVideo(video, performance.now());
          } catch {
            /* mediapipe occasionally throws on resolution changes; skip frame */
          }

          if (result?.faceLandmarks?.[0]?.length && result.faceBlendshapes?.[0]) {
            const lms = result.faceLandmarks[0];

            // Forehead ROI box from 4 landmarks
            let minX = 1;
            let minY = 1;
            let maxX = 0;
            let maxY = 0;
            for (const idx of FOREHEAD_LANDMARKS) {
              const p = lms[idx];
              if (!p) continue;
              if (p.x < minX) minX = p.x;
              if (p.y < minY) minY = p.y;
              if (p.x > maxX) maxX = p.x;
              if (p.y > maxY) maxY = p.y;
            }
            const padX = (maxX - minX) * 0.1;
            const padY = (maxY - minY) * 0.4;
            const roi = {
              x: (minX + padX) * sampleCanvas.width,
              y: (minY - padY) * sampleCanvas.height,
              width: ((maxX - minX) - 2 * padX) * sampleCanvas.width,
              height: Math.max(8, padY * sampleCanvas.height),
            };
            if (roi.width > 4 && roi.height > 4) {
              try {
                const rgb = sampleRoiRgb(ctx, roi);
                rppgRef.current.push({ t: performance.now(), ...rgb });
              } catch {
                /* getImageData can fail for taint; ignore */
              }
            }

            // Update AUs and emotions (refs)
            const blendshapes = result.faceBlendshapes[0].categories.map((c) => ({
              categoryName: c.categoryName,
              score: c.score,
            }));
            ausRef.current = blendshapesToAUs(blendshapes);
            emotionsRef.current = emotionsFromBlendshapes(blendshapes);

            // Draw overlay
            if (overlay) {
              const oc = overlay.getContext("2d");
              if (oc) {
                oc.clearRect(0, 0, overlay.width, overlay.height);
                // Face mesh dots (sparse — every 6th landmark)
                oc.fillStyle = "rgba(99, 102, 241, 0.55)";
                for (let i = 0; i < lms.length; i += 6) {
                  const p = lms[i];
                  oc.beginPath();
                  oc.arc(p.x * overlay.width, p.y * overlay.height, 1, 0, Math.PI * 2);
                  oc.fill();
                }
                // Forehead ROI rectangle
                oc.strokeStyle = "rgba(16, 185, 129, 0.85)";
                oc.lineWidth = 2;
                oc.strokeRect(roi.x, roi.y, roi.width, roi.height);
                oc.fillStyle = "rgba(16, 185, 129, 0.95)";
                oc.font = "600 11px Inter, sans-serif";
                oc.fillText("rPPG ROI", roi.x, Math.max(12, roi.y - 4));
              }
            }
          } else if (overlay) {
            const oc = overlay.getContext("2d");
            oc?.clearRect(0, 0, overlay.width, overlay.height);
          }
        }
      }

      // Audio frame
      const analyser = analyserRef.current;
      const audioBuf = audioBufRef.current;
      const audioCtx = audioCtxRef.current;
      if (analyser && audioBuf && audioCtx) {
        analyser.getFloatTimeDomainData(audioBuf);
        const energy = rms(audioBuf);
        rmsRef.current = energy;
        const f0 = detectPitch(audioBuf, audioCtx.sampleRate);
        f0Ref.current = f0;
        if (f0 != null) {
          f0HistoryRef.current.push(f0);
          while (f0HistoryRef.current.length > 30) f0HistoryRef.current.shift();
        }
      }

      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  /* ─── 4) 10 Hz UI sync + 1 Hz composite calculation ────────── */
  useEffect(() => {
    if (phase !== "running" && phase !== "recording") return;

    const lowFreq = window.setInterval(() => {
      // Sync UI from refs
      setAus({ ...ausRef.current });
      setEmotions({ ...emotionsRef.current });
      setF0Hz(f0Ref.current);
      setRmsDb(rmsToDb(rmsRef.current));
      setJitterPct(jitterPercent(f0HistoryRef.current));
      setTranscript(transcriptRef.current);

      // Calibration progress
      if (calibStartRef.current != null) {
        const elapsed = (performance.now() - calibStartRef.current) / 1000;
        setCalibProgress(Math.min(1, elapsed / CALIBRATION_SECONDS));
      }
    }, 100);
    lowFreqTickRef.current = lowFreq;

    const compositeFreq = window.setInterval(() => {
      // HR estimate via rPPG
      const est = rppgRef.current.estimateBpm();
      const now = performance.now();
      if (est && est.quality > 0.05) {
        setHrBpm(est.bpm);
        setHrQuality(est.quality);
        hrBufferRef.current.push(est.bpm, now);
      }

      // F0 buffer
      if (f0Ref.current != null) {
        f0BufferRef.current.push(f0Ref.current, now);
      }

      // Calibration baselines
      const elapsed = calibStartRef.current ? (now - calibStartRef.current) / 1000 : 0;
      if (elapsed >= CALIBRATION_SECONDS) {
        if (hrBaseline == null && hrBufferRef.current.size() >= 5) {
          setHrBaseline(VitalBuffer.mean(hrBufferRef.current.values()));
        }
        if (f0Baseline == null && f0BufferRef.current.size() >= 5) {
          setF0Baseline(VitalBuffer.mean(f0BufferRef.current.values()));
        }
      }

      const transcriptDuration = recordStartRef.current
        ? (now - recordStartRef.current) / 1000
        : Math.max(0, elapsed - CALIBRATION_SECONDS);
      const liveScores = computeLiveScores({
        hrBpm,
        hrBaselineBpm: hrBaseline,
        f0Hz: f0Ref.current,
        f0BaselineHz: f0Baseline,
        jitterPercent: jitterPercent(f0HistoryRef.current),
        rmsEnergy: rmsRef.current,
        aus: ausRef.current,
        emotions: emotionsRef.current,
        hedgeCount: countHedges(transcriptRef.current),
        speechRateWpm: computeSpeechRateWpm(transcriptRef.current, transcriptDuration),
      });
      setScores(liveScores);
      decBufferRef.current.push(liveScores.deception, now);

      // Sparkline buffers
      setHrSpark(hrBufferRef.current.values());
      setF0Spark(f0BufferRef.current.values());
      setDecSpark(decBufferRef.current.values());

      // Recording accumulation
      if (phaseRef.current === "recording") {
        if (est?.bpm) recordSummaryAccumRef.current.hrSamples.push(est.bpm);
        if (f0Ref.current != null) recordSummaryAccumRef.current.f0Samples.push(f0Ref.current);
        recordSummaryAccumRef.current.auSamples.push({ ...ausRef.current });
        recordSummaryAccumRef.current.emotionSamples.push({ ...emotionsRef.current });
        if (recordStartRef.current) {
          setRecordingSeconds(Math.floor((now - recordStartRef.current) / 1000));
        }
      }
    }, 1000);
    compositeTickRef.current = compositeFreq;

    return () => {
      window.clearInterval(lowFreq);
      window.clearInterval(compositeFreq);
    };
  }, [phase, hrBpm, hrBaseline, f0Baseline]);

  /* ─── 5) Recording controls ────────────────────────────────── */
  const startRecording = useCallback(() => {
    const stream = streamRef.current;
    if (!stream) return;
    recordedChunksRef.current = [];
    recordSummaryAccumRef.current = {
      hrSamples: [],
      f0Samples: [],
      auSamples: [],
      emotionSamples: [],
    };
    finalTranscriptRef.current = "";
    transcriptRef.current = "";

    const mimeType =
      MediaRecorder.isTypeSupported("video/webm; codecs=vp9, opus")
        ? "video/webm; codecs=vp9, opus"
        : "video/webm";
    const recorder = new MediaRecorder(stream, { mimeType });
    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) recordedChunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(recordedChunksRef.current, { type: mimeType });
      const url = URL.createObjectURL(blob);
      finalizeSummaryRef.current?.(url);
    };
    recorder.start(1000);
    recorderRef.current = recorder;
    recordStartRef.current = performance.now();
    setRecordingSeconds(0);
    setPhase("recording");
  }, []);

  const stopRecording = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
  }, []);

  const finalizeSummary = useCallback(
    (recordingBlobUrl: string) => {
      const accum = recordSummaryAccumRef.current;
      const durationSeconds = recordStartRef.current
        ? (performance.now() - recordStartRef.current) / 1000
        : 0;

      const meanAUs: Aus = { ...ZERO_AUS };
      const meanEmotions: Emotions = { ...ZERO_EMOTIONS };
      const auKeys = Object.keys(ZERO_AUS) as (keyof Aus)[];
      const emoKeys = Object.keys(ZERO_EMOTIONS) as (keyof Emotions)[];
      for (const k of auKeys) {
        meanAUs[k] = accum.auSamples.length
          ? accum.auSamples.reduce((s, v) => s + v[k], 0) / accum.auSamples.length
          : 0;
      }
      for (const k of emoKeys) {
        meanEmotions[k] = accum.emotionSamples.length
          ? accum.emotionSamples.reduce((s, v) => s + v[k], 0) / accum.emotionSamples.length
          : 0;
      }
      const dom = dominantEmotion(meanEmotions);

      const hrBaselineBpm = hrBaseline ?? (accum.hrSamples.length ? accum.hrSamples[0] : null);
      const hrPeakBpm = accum.hrSamples.length ? Math.max(...accum.hrSamples) : null;
      const hrDeltaBpm =
        hrBaselineBpm != null && hrPeakBpm != null ? hrPeakBpm - hrBaselineBpm : null;
      const f0BaselineHz = f0Baseline ?? (accum.f0Samples.length ? accum.f0Samples[0] : null);
      const f0PeakHz = accum.f0Samples.length ? Math.max(...accum.f0Samples) : null;

      const hedgeCount = countHedges(transcriptRef.current);
      const speechRateWpm = computeSpeechRateWpm(transcriptRef.current, durationSeconds);
      const finalJitter = jitterPercent(f0HistoryRef.current);

      const finalScores = computeLiveScores({
        hrBpm: hrPeakBpm,
        hrBaselineBpm,
        f0Hz: f0PeakHz,
        f0BaselineHz,
        jitterPercent: finalJitter,
        rmsEnergy: rmsRef.current,
        aus: meanAUs,
        emotions: meanEmotions,
        hedgeCount,
        speechRateWpm,
      });

      const closest = findClosestArchive(finalScores, archive);

      setSummary({
        durationSeconds,
        scores: finalScores,
        hrBaselineBpm,
        hrPeakBpm,
        hrDeltaBpm,
        f0BaselineHz,
        f0PeakHz,
        jitterPercent: finalJitter,
        speechRateWpm,
        hedgeCount,
        dominantEmotion: dom,
        emotionAverages: meanEmotions,
        closestArchive: closest,
        recordingBlobUrl,
        transcript: transcriptRef.current,
      });
      setPhase("reviewing");
    },
    [archive, hrBaseline, f0Baseline],
  );

  // Keep the most recent finalizeSummary closure reachable from MediaRecorder.onstop
  // without forcing startRecording to rebuild every time finalizeSummary's deps change.
  const finalizeSummaryRef = useRef(finalizeSummary);
  useEffect(() => {
    finalizeSummaryRef.current = finalizeSummary;
  }, [finalizeSummary]);

  /* ─── Cleanup ──────────────────────────────────────────────── */
  const cleanupMedia = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    if (lowFreqTickRef.current) window.clearInterval(lowFreqTickRef.current);
    if (compositeTickRef.current) window.clearInterval(compositeTickRef.current);

    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        /* ignore */
      }
      recognitionRef.current = null;
    }

    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.disconnect();
      } catch {
        /* ignore */
      }
      sourceNodeRef.current = null;
    }
    if (audioCtxRef.current) {
      try {
        void audioCtxRef.current.close();
      } catch {
        /* ignore */
      }
      audioCtxRef.current = null;
    }

    if (landmarkerRef.current) {
      try {
        landmarkerRef.current.close();
      } catch {
        /* ignore */
      }
      landmarkerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => cleanupMedia();
  }, [cleanupMedia]);

  const reset = useCallback(() => {
    cleanupMedia();
    rppgRef.current.reset();
    hrBufferRef.current.clear();
    f0BufferRef.current.clear();
    decBufferRef.current.clear();
    f0HistoryRef.current = [];
    transcriptRef.current = "";
    finalTranscriptRef.current = "";
    setHrBpm(null);
    setHrBaseline(null);
    setF0Baseline(null);
    setF0Hz(null);
    setAus(ZERO_AUS);
    setEmotions(ZERO_EMOTIONS);
    setScores(ZERO_SCORES);
    setHrSpark([]);
    setF0Spark([]);
    setDecSpark([]);
    setSummary(null);
    setRecordingSeconds(0);
    setCalibProgress(0);
    setPhase("idle");
  }, [cleanupMedia]);

  /* ─── Render ───────────────────────────────────────────────── */

  if (phase === "reviewing" && summary) {
    return <LiveSummary summary={summary} onReset={reset} />;
  }

  const isLive = phase === "running" || phase === "recording";
  const calibComplete = calibProgress >= 1;
  const hrStatus = hrQuality > 0.18 ? "ok" : hrBpm != null ? "warming" : "off";
  const f0Status = f0Hz != null ? "ok" : "off";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Privacy banner */}
      <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
        <ShieldCheck className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-600" aria-hidden />
        <div className="text-sm text-emerald-900">
          <p className="font-semibold">Privacy-first · Nothing leaves your device.</p>
          <p className="mt-0.5 text-emerald-800">
            Webcam frames, audio, and transcript are processed in your browser only. No upload, no
            cloud calls. The MediaPipe model and WASM runtime are downloaded once from a public CDN
            and cached.
          </p>
        </div>
      </div>

      {/* Idle state */}
      {phase === "idle" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
            Realtime Webcam Mode
          </p>
          <h2 className="mt-3 font-serif text-4xl font-medium text-slate-900">
            Ask your own body
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-slate-600">
            Grant camera + microphone access and we&apos;ll extract your live heart rate from forehead
            color, voice pitch and jitter from microphone, and 14 facial action units from face
            geometry. After {CALIBRATION_SECONDS} seconds of baseline calibration, you can record a
            statement and receive a deep behavioral synthesis.
          </p>
          <button
            type="button"
            onClick={startMedia}
            className="mx-auto mt-8 inline-flex items-center gap-2 rounded-full bg-slate-900 px-7 py-3.5 text-base font-medium text-white transition hover:bg-slate-800"
          >
            <Camera className="h-5 w-5" /> Start session
          </button>
          <p className="mt-4 text-xs text-slate-500">
            Best with stable lighting, a still face, and a working microphone. Chrome and Edge
            recommended (Safari has no Web Speech support, so the live transcript will be blank).
          </p>
        </div>
      )}

      {/* Error state */}
      {phase === "error" && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-left text-sm text-red-800">
          <p className="text-center font-semibold">Could not start session</p>
          {errorInfo ? (
            <div className="mx-auto mt-4 max-w-xl space-y-2">
              <p className="text-center">
                The <span className="font-mono text-xs">{errorInfo.step}</span> step failed.
              </p>
              <pre className="overflow-auto rounded-lg border border-red-200 bg-white p-3 text-[11px] leading-relaxed text-red-900">
                <code>
                  {errorInfo.name}: {errorInfo.message}
                </code>
              </pre>
              <details className="text-[11px] text-red-700/80">
                <summary className="cursor-pointer">Common fixes</summary>
                <ul className="ml-4 mt-2 list-disc space-y-1">
                  <li>
                    Open this page directly at{" "}
                    <span className="font-mono">http://localhost:3000/live</span> in a regular
                    Chrome or Edge tab. Some embedded browsers (including IDE preview proxies)
                    block <span className="font-mono">getUserMedia</span>.
                  </li>
                  <li>
                    Check the camera + microphone padlock icon in the browser address bar and
                    confirm both are set to <strong>Allow</strong>.
                  </li>
                  <li>
                    If the failure was on <span className="font-mono">face model</span>, try a hard
                    reload to clear any cached, broken WASM. The model and WASM must come from{" "}
                    <span className="font-mono">cdn.jsdelivr.net</span> and{" "}
                    <span className="font-mono">storage.googleapis.com</span> — corporate
                    firewalls sometimes block those domains.
                  </li>
                  <li>Run the open-camera test once on another site to make sure the OS camera works (no other app is holding it).</li>
                </ul>
              </details>
            </div>
          ) : (
            <p className="mt-1 text-center">An unknown error occurred.</p>
          )}
          <div className="mt-5 text-center">
            <button
              type="button"
              onClick={() => {
                setErrorInfo(null);
                setPhase("idle");
              }}
              className="inline-flex items-center gap-2 rounded-full border border-red-300 bg-white px-5 py-2 text-sm font-medium text-red-700 transition hover:bg-red-100"
            >
              <RotateCcw className="h-4 w-4" /> Try again
            </button>
          </div>
        </div>
      )}

      {/* Active session */}
      {(phase === "starting" || isLive) && (
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          {/* Left: webcam panel */}
          <section className="space-y-4">
            <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-900 shadow-sm">
              <video
                ref={videoRef}
                className="aspect-video w-full -scale-x-100 object-cover"
                playsInline
                muted
              />
              <canvas
                ref={overlayCanvasRef}
                className="absolute inset-0 h-full w-full -scale-x-100"
                aria-hidden
              />
              <div className="absolute left-3 top-3 flex flex-wrap gap-2 text-[11px] font-semibold uppercase tracking-[0.14em]">
                <span
                  className={`flex items-center gap-1 rounded-full bg-slate-900/70 px-2.5 py-1 backdrop-blur ${
                    hasMedia.video ? "text-emerald-300" : "text-slate-300"
                  }`}
                >
                  {hasMedia.video ? <Video className="h-3 w-3" /> : <VideoOff className="h-3 w-3" />}
                  {hasMedia.video ? "video" : "no video"}
                </span>
                <span
                  className={`flex items-center gap-1 rounded-full bg-slate-900/70 px-2.5 py-1 backdrop-blur ${
                    hasMedia.audio ? "text-emerald-300" : "text-slate-300"
                  }`}
                >
                  {hasMedia.audio ? <Mic className="h-3 w-3" /> : <MicOff className="h-3 w-3" />}
                  {hasMedia.audio ? "audio" : "no audio"}
                </span>
                {phase === "recording" && (
                  <span className="flex items-center gap-1 rounded-full bg-red-600 px-2.5 py-1 text-white">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-white" /> REC{" "}
                    {recordingSeconds}s
                  </span>
                )}
              </div>
              {phase === "starting" && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/70 backdrop-blur-sm">
                  <p className="font-serif text-xl text-white">Loading face model…</p>
                </div>
              )}
            </div>

            {/* Calibration / record controls */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              {!calibComplete ? (
                <>
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                    Baseline calibration
                  </p>
                  <p className="mt-1 font-serif text-lg text-slate-900">
                    Sit still and breathe normally for {CALIBRATION_SECONDS} seconds…
                  </p>
                  <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-[width] duration-100"
                      style={{ width: `${calibProgress * 100}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    {(calibProgress * 100).toFixed(0)}% — capturing resting HR + voice baseline.
                  </p>
                </>
              ) : (
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                      {phase === "recording" ? "Recording…" : "Ready"}
                    </p>
                    <p className="mt-1 font-serif text-lg text-slate-900">
                      {phase === "recording"
                        ? `Speak naturally · ${recordingSeconds}s captured`
                        : "Start recording to capture a session for deep analysis."}
                    </p>
                    {hrBaseline != null && (
                      <p className="mt-1 text-xs text-slate-500">
                        Baseline established: HR {hrBaseline.toFixed(0)} bpm
                        {f0Baseline != null && ` · F0 ${f0Baseline.toFixed(0)} Hz`}
                      </p>
                    )}
                  </div>
                  {phase === "recording" ? (
                    <button
                      type="button"
                      onClick={stopRecording}
                      className="inline-flex items-center gap-2 rounded-full bg-red-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-red-700"
                    >
                      <CircleStop className="h-4 w-4" /> Stop & analyze
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={startRecording}
                      className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
                    >
                      <span className="h-2.5 w-2.5 rounded-full bg-red-500" /> Record
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Live transcript */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <header className="mb-2 flex items-center justify-between">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  Live Transcript
                </p>
                <p className="text-[10px] text-slate-400">
                  {countHedges(transcript)} hedges detected
                </p>
              </header>
              <p className="min-h-[3em] font-serif text-base leading-relaxed text-slate-800">
                {transcript || (
                  <span className="italic text-slate-400">
                    Web Speech API is listening… speak to populate the transcript.
                  </span>
                )}
              </p>
            </div>
          </section>

          {/* Right: signal panel */}
          <section className="space-y-4">
            {/* Truth gauge */}
            <div className="flex flex-col items-center rounded-2xl border border-slate-200 bg-gradient-to-br from-white via-slate-50 to-white p-5 shadow-sm">
              <TruthGauge value={scores.deception} label="Deception index" />
              <div className="mt-2 grid w-full grid-cols-3 gap-2 text-center text-[11px]">
                <div className="rounded-lg bg-blue-50 px-2 py-1 text-blue-700">
                  <p className="font-bold tabular-nums">{scores.sincerity}</p>
                  <p className="text-[10px] uppercase tracking-[0.12em]">sincere</p>
                </div>
                <div className="rounded-lg bg-amber-50 px-2 py-1 text-amber-700">
                  <p className="font-bold tabular-nums">{scores.stress}</p>
                  <p className="text-[10px] uppercase tracking-[0.12em]">stress</p>
                </div>
                <div className="rounded-lg bg-emerald-50 px-2 py-1 text-emerald-700">
                  <p className="font-bold tabular-nums">{scores.confidence}</p>
                  <p className="text-[10px] uppercase tracking-[0.12em]">conf</p>
                </div>
              </div>
            </div>

            {/* Vital cards */}
            <div className="grid grid-cols-2 gap-3">
              <VitalCard
                label="Heart Rate"
                value={hrBpm != null ? hrBpm.toFixed(0) : "—"}
                unit="bpm"
                hint={
                  hrBaseline != null && hrBpm != null
                    ? `Δ ${(hrBpm - hrBaseline).toFixed(0)} from baseline`
                    : "Stabilizing rPPG…"
                }
                history={hrSpark}
                accent="red"
                status={hrStatus}
              />
              <VitalCard
                label="Voice F0"
                value={f0Hz != null ? f0Hz.toFixed(0) : "—"}
                unit="Hz"
                hint={
                  f0Baseline != null && f0Hz != null
                    ? `Δ ${Math.abs(f0Hz - f0Baseline).toFixed(0)} Hz`
                    : "Speak to capture pitch"
                }
                history={f0Spark}
                accent="blue"
                status={f0Status}
              />
              <VitalCard
                label="Jitter"
                value={jitterPct.toFixed(2)}
                unit="%"
                hint="cycle-to-cycle pitch variation"
                accent="amber"
              />
              <VitalCard
                label="Audio Level"
                value={rmsDb.toFixed(0)}
                unit="dB"
                hint={rmsDb > -50 ? "voiced" : "ambient"}
                accent="emerald"
              />
            </div>

            {/* Action units */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <header className="mb-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  Facial Action Units
                </p>
              </header>
              <div className="space-y-2">
                <BarRow label="AU12 lip pull (smile)" value={aus.AU12_lipCornerPull} color="emerald" />
                <BarRow label="AU6 cheek raise" value={aus.AU6_cheekRaiser} color="emerald" />
                <BarRow label="AU15 lip depress" value={aus.AU15_lipCornerDepressor} color="rose" />
                <BarRow label="AU14 dimpler" value={aus.AU14_dimpler} color="amber" />
                <BarRow label="AU4 brow lower" value={aus.AU4_browLower} color="amber" />
                <BarRow label="AU7 lid tighten" value={aus.AU7_lidTightener} color="amber" />
                <BarRow label="AU24 lip press" value={aus.AU24_lipPressor} color="rose" />
                <BarRow label="AU45 blink" value={aus.AU45_blink} color="slate" />
              </div>
            </div>

            {/* Emotions */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <header className="mb-3 flex items-center justify-between">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  Affect Estimation
                </p>
                <p className="text-[10px] text-slate-400">heuristic blend</p>
              </header>
              <div className="space-y-2">
                <BarRow label="Joy" value={emotions.joy} color="emerald" />
                <BarRow label="Anger" value={emotions.anger} color="red" />
                <BarRow label="Sadness" value={emotions.sadness} color="blue" />
                <BarRow label="Fear" value={emotions.fear} color="violet" />
                <BarRow label="Surprise" value={emotions.surprise} color="amber" />
                <BarRow label="Disgust" value={emotions.disgust} color="rose" />
              </div>
            </div>

            {/* Deception sparkline */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <header className="mb-2 flex items-center justify-between">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  Deception index · {SPARK_WINDOW_SECONDS}s
                </p>
                <p className="font-serif text-2xl font-medium tabular-nums text-violet-700">
                  {scores.deception}
                </p>
              </header>
              <div className="h-12">
                <Sparkline data={decSpark} stroke="#8b5cf6" ariaLabel="Deception index sparkline" />
              </div>
            </div>
          </section>
        </div>
      )}
    </motion.div>
  );
}
