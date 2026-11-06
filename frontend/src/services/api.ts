import {
  Project, ProjectDetail, VideoAsset, Clip, Job,
  ProductionPlan, PromptPlanningRequest, ProvidersStatusResponse,
  PrivacyStatus, TransferAuditLog
} from '../types';

const API_BASE = '/api';

export const api = {
  // Projects
  async listProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error('Failed to load projects');
    return res.json();
  },

  async createProject(data: { name: string; project_type: string; platform: string }): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create project');
    return res.json();
  },

  async getProject(projectId: string): Promise<ProjectDetail> {
    const res = await fetch(`${API_BASE}/projects/${projectId}`);
    if (!res.ok) throw new Error('Failed to fetch project details');
    return res.json();
  },

  async deleteProject(projectId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/projects/${projectId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete project');
  },

  // Uploads
  async uploadVideo(file: File, projectId?: string): Promise<VideoAsset> {
    const formData = new FormData();
    formData.append('file', file);
    if (projectId) formData.append('project_id', projectId);

    const res = await fetch(`${API_BASE}/uploads`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  // Prompt-to-Video
  async generateStoryboard(payload: PromptPlanningRequest): Promise<ProductionPlan> {
    const res = await fetch(`${API_BASE}/generation/storyboard`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Planning failed' }));
      throw new Error(err.detail || 'Planning failed');
    }
    return res.json();
  },

  async triggerPromptToVideo(payload: PromptPlanningRequest): Promise<Job> {
    const res = await fetch(`${API_BASE}/generation/video`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Generation failed' }));
      throw new Error(err.detail || 'Generation failed');
    }
    return res.json();
  },

  // Jobs
  async getJob(jobId: string): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) throw new Error('Failed to fetch job status');
    return res.json();
  },

  async cancelJob(jobId: string): Promise<void> {
    await fetch(`${API_BASE}/generation/${jobId}/cancel`, { method: 'POST' });
  },

  async pauseJob(jobId: string): Promise<Job> {
    const res = await fetch(`${API_BASE}/generation/${jobId}/pause`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to pause job');
    return res.json();
  },

  async resumeJob(jobId: string): Promise<Job> {
    const res = await fetch(`${API_BASE}/generation/${jobId}/resume`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to resume job');
    return res.json();
  },

  // Video-to-Shorts
  async analyzeVideo(assetId: string, targetDuration: number = 30): Promise<Job> {
    const res = await fetch(`${API_BASE}/videos/${assetId}/analyze?target_clip_duration=${targetDuration}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to start video analysis');
    return res.json();
  },

  async getVideoAnalysis(assetId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/videos/${assetId}/analysis`);
    if (!res.ok) throw new Error('Failed to load video analysis');
    return res.json();
  },

  async listProjectClips(projectId: string): Promise<Clip[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/clips`);
    if (!res.ok) throw new Error('Failed to load clips');
    return res.json();
  },

  async updateClip(clipId: string, data: Partial<Clip>): Promise<Clip> {
    const res = await fetch(`${API_BASE}/clips/${clipId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update clip');
    return res.json();
  },

  async renderClip(clipId: string): Promise<Job> {
    const res = await fetch(`${API_BASE}/clips/${clipId}/render`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to start clip rendering');
    return res.json();
  },

  // System & Providers
  async getProvidersStatus(): Promise<ProvidersStatusResponse> {
    const res = await fetch(`${API_BASE}/providers`);
    if (!res.ok) throw new Error('Failed to fetch provider status');
    return res.json();
  },

  async getSettings(): Promise<any> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  // External Storage Management
  async getStorageStats(): Promise<{
    media_storage_path: string;
    temp_media_path: string;
    draft_storage_enabled: boolean;
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent_used: number;
    rendered_videos_count: number;
    uploads_count: number;
    drafts_count: number;
    is_outside_project: boolean;
  }> {
    const res = await fetch(`${API_BASE}/storage/stats`);
    if (!res.ok) throw new Error('Failed to fetch storage stats');
    return res.json();
  },

  async deleteAsset(assetId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/assets/${assetId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete asset from external storage');
  },

  async cleanupTempStorage(): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/storage/cleanup`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to clean up temp storage');
    return res.json();
  },

  // Privacy Gateway & Model Routing
  async getPrivacyStatus(): Promise<PrivacyStatus> {
    const res = await fetch(`${API_BASE}/privacy/status`);
    if (!res.ok) throw new Error('Failed to fetch privacy status');
    return res.json();
  },

  async updatePrivacySettings(data: {
    privacy_mode?: string;
    allow_cloud_transfers?: boolean;
    allowlist?: string[];
  }): Promise<PrivacyStatus> {
    const res = await fetch(`${API_BASE}/privacy/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update privacy settings');
    return res.json();
  },

  async getTransferAuditLogs(limit: number = 50): Promise<TransferAuditLog[]> {
    const res = await fetch(`${API_BASE}/privacy/audit-logs?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    return res.json();
  },

  async clearTransferAuditLogs(): Promise<void> {
    const res = await fetch(`${API_BASE}/privacy/audit-logs/clear`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to clear audit logs');
  }
};

