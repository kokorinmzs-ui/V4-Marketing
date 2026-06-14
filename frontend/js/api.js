/**
 * Marketing OS v4 — Frontend API Client
 *
 * Safe JSON-first REST client for the static HTML frontend.
 */

const DEFAULT_API_BASE = "http://localhost:8000";
const API_BASE =
  window.location.protocol === "file:"
    ? DEFAULT_API_BASE
    : window.location.origin || DEFAULT_API_BASE;

function buildUrl(path) {
  return `${API_BASE}${path}`;
}

function tryParseJson(text) {
  if (!text) {
    return null;
  }

  const trimmed = text.trim();
  if (!trimmed) {
    return null;
  }

  if (
    trimmed.startsWith("{") ||
    trimmed.startsWith("[") ||
    trimmed === "null" ||
    trimmed === "true" ||
    trimmed === "false" ||
    /^-?\d+(\.\d+)?$/.test(trimmed)
  ) {
    return JSON.parse(trimmed);
  }

  return text;
}

async function request(path, options = {}) {
  const response = await fetch(buildUrl(path), {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  const rawBody = await response.text().catch(() => "");
  const parsedBody = (() => {
    try {
      return tryParseJson(rawBody);
    } catch (error) {
      return { __parse_error__: error.message, raw: rawBody };
    }
  })();

  if (!response.ok) {
    const detail =
      parsedBody && typeof parsedBody === "object" && parsedBody.detail
        ? parsedBody.detail
        : rawBody || response.statusText || "Unknown error";
    throw new Error(`API ${response.status} ${response.statusText}: ${detail}`);
  }

  return parsedBody;
}

function createProject(name, brief = null) {
  const payloadBrief =
    brief || {
      project_name: name,
      industry: "general_marketing",
      business_description: name,
      products: [name],
      goals: ["Launch marketing pipeline"],
    };

  return request("/projects", {
    method: "POST",
    body: JSON.stringify({ name, brief: payloadBrief }),
  });
}

function listProjects() {
  return request("/projects");
}

function getProject(projectId) {
  return request(`/projects/${projectId}`);
}

function deleteProject(projectId) {
  return request(`/projects/${projectId}`, { method: "DELETE" });
}

function getBrief(projectId) {
  return request(`/projects/${projectId}/brief`);
}

function updateBrief(projectId, brief) {
  return request(`/projects/${projectId}/brief`, {
    method: "PUT",
    body: JSON.stringify(brief),
  });
}

function generateProject(projectId) {
  return request(`/projects/${projectId}/generate`, { method: "POST" });
}

function getGenerationStatus(projectId) {
  return request(`/projects/${projectId}/status`);
}

function getReview(projectId) {
  return request(`/projects/${projectId}/review`);
}

function approveReview(projectId) {
  return request(`/projects/${projectId}/review/approve`, { method: "POST" });
}

function rejectReview(projectId) {
  return request(`/projects/${projectId}/review/reject`, { method: "POST" });
}

function listArtifacts(projectId) {
  return request(`/projects/${projectId}/artifacts`);
}

function getArtifactDownloadUrl(projectId, artifactName) {
  return `${API_BASE}/projects/${projectId}/download/${encodeURIComponent(
    artifactName,
  )}`;
}

function smartNav(routePath, filePath) {
  const target = window.location.protocol === "file:" ? filePath : routePath;
  window.location.href = target;
  return false;
}

window.createProject = createProject;
window.listProjects = listProjects;
window.getProject = getProject;
window.deleteProject = deleteProject;
window.getBrief = getBrief;
window.updateBrief = updateBrief;
window.generateProject = generateProject;
window.getGenerationStatus = getGenerationStatus;
window.getReview = getReview;
window.approveReview = approveReview;
window.rejectReview = rejectReview;
window.listArtifacts = listArtifacts;
window.getArtifactDownloadUrl = getArtifactDownloadUrl;
window.smartNav = smartNav;
