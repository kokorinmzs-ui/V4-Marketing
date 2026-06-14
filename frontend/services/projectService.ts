import type { Project, Brief } from "../store/projectStore.ts";
import * as store from "../store/projectStore.ts";

/**
 * Mock project service. In Sprint 15, replace with real API calls.
 */
export function listProjects(): Project[] {
  return store.getProjects();
}

export function getProjectById(id: string): Project | null {
  return store.getProject(id);
}

export function createNewProject(name: string): Project {
  return store.createProject(name);
}

export function saveBrief(projectId: string, brief: Brief): Project | null {
  return store.updateBrief(projectId, brief);
}

export function updateProjectStatus(
  projectId: string,
  status: Project["status"],
): Project | null {
  return store.setProjectStatus(projectId, status);
}
