/**
 * Marketing OS v4 — Frontend API Client
 *
 * Replaces localStorage-based project management with real backend REST API.
 * Backend must be running on the same origin or CORS must be configured.
 */

const API_BASE = window.location.origin || "http://localhost:8000";

async function api(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const err = await response.text().catch(() => "Unknown error");
    throw new Error(`API ${response.status}: ${err}`);
  }
  return response.json();
}

// ===== Projects =====
function createProject(name, brief = null) {
  const payloadBrief =
    brief || {
      project_name: name,
      industry: "general_marketing",
      business_description: name,
      products: [name],
      goals: ["Launch marketing pipeline"],
    };
  return api("/projects", {
    method: "POST",
    body: JSON.stringify({ name: name, brief: payloadBrief }),
  });
}

function listProjects() {
  return api("/projects");
}

function getProject(projectId) {
  return api(`/projects/${projectId}`);
}

function deleteProject(projectId) {
  return api(`/projects/${projectId}`, { method: "DELETE" });
}

// ===== Generation =====
function generateProject(projectId) {
  return api(`/projects/${projectId}/generate`, { method: "POST" });
}

function getGenerationStatus(projectId) {
  return api(`/projects/${projectId}/status`);
}

// ===== Artifacts =====
function listArtifacts(projectId) {
  return api(`/projects/${projectId}/artifacts`);
}

function getArtifactDownloadUrl(projectId, artifactName) {
  return `${API_BASE}/projects/${projectId}/download/${encodeURIComponent(artifactName)}`;
}

window.createProject = createProject;
window.listProjects = listProjects;
window.getProject = getProject;
window.deleteProject = deleteProject;
window.generateProject = generateProject;
window.getGenerationStatus = getGenerationStatus;
window.listArtifacts = listArtifacts;
window.getArtifactDownloadUrl = getArtifactDownloadUrl;
