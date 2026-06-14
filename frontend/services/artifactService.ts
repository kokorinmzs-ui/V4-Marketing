import type { Artifact } from "../types/artifact.ts";
import * as genStore from "../store/generationStore.ts";

/**
 * Mock artifact service. Returns mock artifacts after generation completes.
 */
export function getArtifacts(): Artifact[] {
  return genStore.getGenerationState().artifacts;
}

export function getDownloadUrl(artifactName: string): string {
  return `/artifacts/${artifactName}`;
}

const MOCK_ARTIFACT_PATHS: Record<string, string> = {
  "final_data.json": "artifacts/final_data.json",
  "execution_view_model.json": "artifacts/execution_view_model.json",
  "dashboard.html": "artifacts/dashboard.html",
  "client-package.zip": "artifacts/client-package.zip",
};

export function getArtifactPath(name: string): string {
  return MOCK_ARTIFACT_PATHS[name] || `artifacts/${name}`;
}
