import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def gen_uuid() -> str:
    return uuid.uuid4().hex

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), default="prompt_to_video") # prompt_to_video | video_to_shorts
    platform: Mapped[str] = mapped_column(String(50), default="instagram_reels") # instagram_reels | youtube_shorts
    status: Mapped[str] = mapped_column(String(50), default="draft") # draft | processing | ready | error
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    assets: Mapped[List["VideoAsset"]] = relationship("VideoAsset", back_populates="project", cascade="all, delete-orphan")
    scenes: Mapped[List["Scene"]] = relationship("Scene", back_populates="project", cascade="all, delete-orphan")
    clips: Mapped[List["Clip"]] = relationship("Clip", back_populates="project", cascade="all, delete-orphan")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="project", cascade="all, delete-orphan")

class VideoAsset(Base):
    __tablename__ = "video_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(50), default="source_video") # source_video | rendered_short | scene_video | scene_image | audio_narration | audio_music
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="assets")
    transcript: Mapped[Optional["Transcript"]] = relationship("Transcript", back_populates="asset", uselist=False, cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=5.0)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    visual_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    camera_movement: Mapped[Optional[str]] = mapped_column(String(100), default="static")
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending | generating | completed | failed
    asset_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    audio_asset_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="scenes")

class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    source_asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("video_assets.id"), index=True)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    title: Mapped[str] = mapped_column(String(255), default="Untitled Clip")
    hook: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="candidate") # candidate | approved | rendering | completed | failed
    crop_mode: Mapped[str] = mapped_column(String(50), default="smart") # smart | center | blurred_background
    caption_style: Mapped[str] = mapped_column(String(50), default="bold_yellow") # bold_yellow | clean_minimal | creator_box | cinematic
    rendered_asset_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="clips")

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False) # upload_processing | transcription | scene_detection | clip_generation | prompt_planning | scene_generation | video_render
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending | running | completed | failed | cancelled
    progress: Mapped[int] = mapped_column(Integer, default=0) # 0 to 100
    current_step: Mapped[Optional[str]] = mapped_column(String(255), default="Initialized")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    result_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="jobs")

class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("video_assets.id"), unique=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    segments_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list) # [{start, end, text, words: [{word, start, end}]}]
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    asset: Mapped["VideoAsset"] = relationship("VideoAsset", back_populates="transcript")
