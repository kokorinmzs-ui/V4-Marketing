import type { Artifact } from "../types/artifact.ts";

export type GenerationStatus = "idle" | "generating" | "completed" | "failed";

let status: GenerationStatus = "idle";
let currentStep = 0;
let progress = 0;
let artifacts: Artifact[] = [];
let listeners: (() => void)[] = [];

function notify() {
  listeners.forEach((fn) => fn());
}

export function getGenerationState() {
  return { status, currentStep, progress, artifacts };
}

export function startGeneration() {
  status = "generating";
  currentStep = 0;
  progress = 0;
  artifacts = [];
  notify();
  simulateProgress(0);
}

export function completeGeneration(mockArtifacts: Artifact[]) {
  status = "completed";
  progress = 100;
  artifacts = mockArtifacts;
  notify();
}

export function failGeneration() {
  status = "failed";
  progress = 0;
  notify();
}

function simulateProgress(step: number) {
  if (status !== "generating") return;
  currentStep = step;
  progress = step * 25;
  notify();
  if (step < 4) {
    setTimeout(() => simulateProgress(step + 1), 300 + Math.random() * 500);
  } else {
    completeGeneration([
      {
        name: "final_data.json",
        artifactType: "json",
        sizeBytes: 120000,
        createdAt: new Date().toISOString(),
        path: "artifacts/final_data.json",
      },
      {
        name: "execution_view_model.json",
        artifactType: "json",
        sizeBytes: 100000,
        createdAt: new Date().toISOString(),
        path: "artifacts/execution_view_model.json",
      },
      {
        name: "dashboard.html",
        artifactType: "html",
        sizeBytes: 150000,
        createdAt: new Date().toISOString(),
        path: "artifacts/dashboard.html",
      },
      {
        name: "client-package.zip",
        artifactType: "zip",
        sizeBytes: 16000,
        createdAt: new Date().toISOString(),
        path: "artifacts/client-package.zip",
      },
    ]);
  }
}

export function subscribe(fn: () => void): () => void {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((l) => l !== fn);
  };
}
