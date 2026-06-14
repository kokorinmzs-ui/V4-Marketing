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
