export type ProjectStatus =
  | "draft"
  | "ready_to_generate"
  | "generating"
  | "completed"
  | "failed";

export interface Brief {
  project_name: string;
  industry: string;
  business_description: string;
  target_audience: string;
  products: string;
  channels: string;
  goals: string;
  region: string;
  budget: string;
}

export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  brief: Brief;
  createdAt: string;
  updatedAt: string;
}

// ========== In-memory Zustand-like store (browser compatible) ==========
let projects: Project[] = [];
let listeners: (() => void)[] = [];

function notify() {
  listeners.forEach((fn) => fn());
}

export function getProjects(): Project[] {
  return projects;
}

export function getProject(id: string): Project | null {
  return projects.find((p) => p.id === id) ?? null;
}

export function createProject(name: string): Project {
  const now = new Date().toISOString();
  const project: Project = {
    id: crypto.randomUUID
      ? crypto.randomUUID()
      : Date.now().toString(36) + Math.random().toString(36).slice(2),
    name,
    status: "draft",
    brief: {
      project_name: name,
      industry: "",
      business_description: "",
      target_audience: "",
      products: "",
      channels: "",
      goals: "",
      region: "",
      budget: "",
    },
    createdAt: now,
    updatedAt: now,
  };
  projects = [project, ...projects];
  notify();
  return project;
}

export function updateBrief(id: string, brief: Brief): Project | null {
  const idx = projects.findIndex((p) => p.id === id);
  if (idx === -1) return null;
  projects[idx].brief = { ...projects[idx].brief, ...brief };
  projects[idx].updatedAt = new Date().toISOString();
  notify();
  return projects[idx];
}

export function setProjectStatus(
  id: string,
  status: ProjectStatus,
): Project | null {
  const idx = projects.findIndex((p) => p.id === id);
  if (idx === -1) return null;
  projects[idx].status = status;
  projects[idx].updatedAt = new Date().toISOString();
  notify();
  return projects[idx];
}

export function deleteProject(id: string): boolean {
  const len = projects.length;
  projects = projects.filter((p) => p.id !== id);
  if (projects.length !== len) {
    notify();
    return true;
  }
  return false;
}

export function subscribe(fn: () => void): () => void {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((l) => l !== fn);
  };
}
