export interface Project {
  id: string;
  name: string;
  project_type: 'prompt_to_video' | 'video_to_shorts';
  platform: 'instagram_reels' | 'youtube_shorts';
  status: 'draft' | 'processing' | 'ready' | 'error';
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface VideoAsset {
  id: string;
  project_id: string;
  asset_type: 'source_video' | 'rendered_short' | 'rendered_final' | 'scene_video' | 'scene_image';
  storage_path: string;
  original_filename: string;
  duration?: number;
  width?: number;
  height?: number;
  file_size_bytes?: number;
  metadata_json: Record<string, any>;
  download_url?: string;
  stream_url?: string;
  created_at: string;
}

export interface Scene {
  id: string;
  project_id: string;
  scene_number: number;
  duration: number;
  prompt: string;
  visual_description?: string;
  camera_movement?: string;
  narration?: string;
  caption?: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  asset_id?: string;
  audio_asset_id?: string;
  thumbnail_path?: string;
  created_at: string;
}

export interface Clip {
  id: string;
  project_id: string;
  source_asset_id: string;
  start_time: number;
  end_time: number;
  duration: number;
  score: number;
  title: string;
  hook?: string;
  reason?: string;
  status: 'candidate' | 'approved' | 'rendering' | 'completed' | 'failed';
  crop_mode: 'smart' | 'center' | 'blurred_background';
  caption_style: 'bold_yellow' | 'clean_minimal' | 'creator_box' | 'cinematic';
  rendered_asset_id?: string;
  download_url?: string;
  stream_url?: string;
  created_at: string;
}

export interface Job {
  id: string;
  project_id: string;
  job_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step?: string;
  error_message?: string;
  retry_count: number;
  result_data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  assets: VideoAsset[];
  scenes: Scene[];
  clips: Clip[];
  jobs: Job[];
}

export interface StructuredScenePlan {
  scene_number: number;
  duration_seconds: number;
  purpose: string;
  visual_prompt: string;
  camera_movement: string;
  narration?: string;
  caption?: string;
  transition: string;
}

export interface ProductionPlan {
  title: string;
  platform: string;
  duration_seconds: number;
  aspect_ratio: string;
  style: string;
  language: string;
  scenes: StructuredScenePlan[];
}

export interface PromptPlanningRequest {
  prompt: string;
  target_platform: string;
  duration_seconds: number;
  aspect_ratio: string;
  visual_style: string;
  voiceover_enabled: boolean;
  voice_selection: string;
  caption_style: string;
  background_music: string;
  language: string;
  num_scenes: number;
  quality: string;
}

export interface ProviderItemStatus {
  configured_provider: string;
  is_active: boolean;
  is_real_api: boolean;
  model_info: string;
}

export interface ProvidersStatusResponse {
  demo_mode: boolean;
  llm: ProviderItemStatus;
  video: ProviderItemStatus;
  audio: ProviderItemStatus;
  transcription: ProviderItemStatus;
}

