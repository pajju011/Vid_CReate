from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    project_type: str = Field(default="prompt_to_video") # prompt_to_video | video_to_shorts
    platform: str = Field(default="instagram_reels") # instagram_reels | youtube_shorts
    settings: Dict[str, Any] = Field(default_factory=dict)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class VideoAssetResponse(BaseModel):
    id: str
    project_id: str
    asset_type: str
    storage_path: str
    original_filename: str
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size_bytes: Optional[int] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    download_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SceneResponse(BaseModel):
    id: str
    project_id: str
    scene_number: int
    duration: float
    prompt: str
    visual_description: Optional[str] = None
    camera_movement: Optional[str] = "static"
    narration: Optional[str] = None
    caption: Optional[str] = None
    status: str
    asset_id: Optional[str] = None
    audio_asset_id: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ClipResponse(BaseModel):
    id: str
    project_id: str
    source_asset_id: str
    start_time: float
    end_time: float
    duration: float = 0.0
    score: float
    title: str
    hook: Optional[str] = None
    reason: Optional[str] = None
    status: str
    crop_mode: str
    caption_style: str
    rendered_asset_id: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: str
    project_id: str
    job_type: str
    status: str
    progress: int
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    result_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectResponse(ProjectBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectDetailResponse(ProjectResponse):
    assets: List[VideoAssetResponse] = Field(default_factory=list)
    scenes: List[SceneResponse] = Field(default_factory=list)
    clips: List[ClipResponse] = Field(default_factory=list)
    jobs: List[JobResponse] = Field(default_factory=list)

# --- Prompt to Video Schemas ---
class StructuredScenePlan(BaseModel):
    scene_number: int
    duration_seconds: float = Field(default=5.0, ge=1.0, le=30.0)
    purpose: str = Field(default="hook") # hook | introduction | feature | proof | call_to_action
    visual_prompt: str
    camera_movement: str = "slow_push_in"
    narration: Optional[str] = None
    caption: Optional[str] = None
    transition: str = "fade"

class ProductionPlan(BaseModel):
    title: str
    platform: str = "instagram_reels"
    duration_seconds: float = 30.0
    aspect_ratio: str = "9:16"
    style: str = "cinematic"
    language: str = "en"
    scenes: List[StructuredScenePlan]

class PromptPlanningRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    target_platform: str = "instagram_reels" # instagram_reels | youtube_shorts
    duration_seconds: float = 30.0
    aspect_ratio: str = "9:16" # 9:16 | 16:9 | 1:1
    visual_style: str = "cinematic" # cinematic | dynamic_commercial | anime | hyperrealistic | 3d_render
    voiceover_enabled: bool = True
    voice_selection: str = "energetic_male" # energetic_male | friendly_female | deep_narrator
    caption_style: str = "bold_yellow" # bold_yellow | clean_minimal | creator_box | cinematic
    background_music: str = "upbeat_synth" # upbeat_synth | ambient_chill | energetic_trap | none
    language: str = "en"
    num_scenes: int = 5
    quality: str = "standard" # standard | high

class SceneUpdateRequest(BaseModel):
    prompt: Optional[str] = None
    visual_description: Optional[str] = None
    duration: Optional[float] = None
    narration: Optional[str] = None
    caption: Optional[str] = None
    camera_movement: Optional[str] = None

class GenerateClipsRequest(BaseModel):
    target_duration: float = Field(default=30.0, ge=5.0, le=180.0)
    num_clips: int = Field(default=3, ge=1, le=10)
    crop_mode: str = "smart" # smart | center | blurred_background
    caption_style: str = "bold_yellow"

class ClipUpdateRequest(BaseModel):
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    title: Optional[str] = None
    crop_mode: Optional[str] = None
    caption_style: Optional[str] = None

class RenderProjectRequest(BaseModel):
    platform: str = "instagram_reels"
    aspect_ratio: str = "9:16"
    resolution: str = "1080x1920"
    caption_style: str = "bold_yellow"
    background_music: Optional[str] = None
