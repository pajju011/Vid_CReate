import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud, Scissors, Sparkles, Film, Clock, CheckCircle2,
  AlertCircle, Play, Download, Sliders, Crop, Subtitles, RefreshCw, Loader2
} from 'lucide-react';
import { VideoAsset, Clip } from '../../types';
import { api } from '../../services/api';
import { JobProgressModal } from '../../components/common/JobProgressModal';

export const ShortsStudio: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [uploadedAsset, setUploadedAsset] = useState<VideoAsset | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [clips, setClips] = useState<Clip[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isJobModalOpen, setIsJobModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Settings
  const [targetDuration, setTargetDuration] = useState(30);
  const [cropMode, setCropMode] = useState<'smart' | 'center' | 'blurred_background'>('smart');
  const [captionStyle, setCaptionStyle] = useState<'bold_yellow' | 'clean_minimal' | 'creator_box' | 'cinematic'>('bold_yellow');

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadFile(file);
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    await uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
      const asset = await api.uploadVideo(file);
      setUploadedAsset(asset);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!uploadedAsset) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const job = await api.analyzeVideo(uploadedAsset.id, targetDuration);
      setActiveJobId(job.id);
      setIsJobModalOpen(true);
    } catch (err: any) {
      setError(err.message || 'Failed to trigger video analysis');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleJobSuccess = async () => {
    if (!uploadedAsset) return;
    try {
      const projectClips = await api.listProjectClips(uploadedAsset.project_id);
      setClips(projectClips);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRenderClip = async (clipId: string) => {
    try {
      const job = await api.renderClip(clipId);
      setActiveJobId(job.id);
      setIsJobModalOpen(true);
    } catch (err: any) {
      setError(err.message || 'Failed to render short');
    }
  };

  const handleUpdateClipTime = async (clipId: string, start: number, end: number) => {
    try {
      const updated = await api.updateClip(clipId, {
        start_time: start,
        end_time: end,
        crop_mode: cropMode,
        caption_style: captionStyle,
      });
      setClips(clips.map((c) => (c.id === clipId ? updated : c)));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-teal-900/20 to-transparent border border-emerald-500/20 rounded-2xl p-6 sm:p-8 relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold mb-3">
            <Scissors className="w-3.5 h-3.5" />
            Workflow B: Long-Video to Viral Shorts
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Transform Long Videos into High-Impact Shorts
          </h2>
          <p className="mt-2 text-sm text-gray-300 leading-relaxed">
            Upload podcasts, webinars, or YouTube videos. ClipForge automatically transcribes speech,
            detects viral hooks, scores standout segments, applies smart 9:16 vertical crop, and burns stylish captions.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Upload Zone */}
      {!uploadedAsset ? (
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className="border-2 border-dashed border-gray-700 hover:border-emerald-500/50 bg-[#111827]/60 rounded-2xl p-10 text-center cursor-pointer transition-all hover:bg-gray-800/40 group"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept="video/mp4,video/quicktime,video/webm"
            className="hidden"
          />

          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform border border-emerald-500/20">
            {isUploading ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <UploadCloud className="w-8 h-8" />
            )}
          </div>

          <h3 className="text-lg font-bold text-white mb-1">
            {isUploading ? 'Validating and Uploading Video...' : 'Drag and Drop Video File Here'}
          </h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto mb-4">
            Supported formats: MP4, MOV, WebM. File is inspected securely using FFprobe.
          </p>
          <button
            type="button"
            className="px-5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
          >
            Select from Computer
          </button>
        </div>
      ) : (
        /* Uploaded Video Inspector */
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-gray-800">
            <div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h3 className="text-base font-bold text-white truncate max-w-md">
                  {uploadedAsset.original_filename}
                </h3>
              </div>
              <p className="text-xs text-gray-400 mt-1">Video successfully validated with FFprobe</p>
            </div>

            <button
              onClick={() => {
                setUploadedAsset(null);
                setClips([]);
              }}
              className="text-xs text-gray-400 hover:text-rose-400 transition-colors"
            >
              Upload Different Video
            </button>
          </div>

          {/* Metadata Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-[#0b0f17] border border-gray-800 rounded-xl p-3.5">
              <span className="text-[10px] text-gray-500 uppercase font-semibold block">Duration</span>
              <span className="text-sm font-bold text-gray-200 font-mono">
                {uploadedAsset.duration ? `${Math.round(uploadedAsset.duration)}s` : 'Unknown'}
              </span>
            </div>
            <div className="bg-[#0b0f17] border border-gray-800 rounded-xl p-3.5">
              <span className="text-[10px] text-gray-500 uppercase font-semibold block">Resolution</span>
              <span className="text-sm font-bold text-gray-200 font-mono">
                {uploadedAsset.width && uploadedAsset.height
                  ? `${uploadedAsset.width}x${uploadedAsset.height}`
                  : '1920x1080'}
              </span>
            </div>
            <div className="bg-[#0b0f17] border border-gray-800 rounded-xl p-3.5">
              <span className="text-[10px] text-gray-500 uppercase font-semibold block">Codec / Audio</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">
                {uploadedAsset.metadata_json?.has_audio ? 'Stereo Audio OK' : 'Video Only'}
              </span>
            </div>
            <div className="bg-[#0b0f17] border border-gray-800 rounded-xl p-3.5">
              <span className="text-[10px] text-gray-500 uppercase font-semibold block">File Size</span>
              <span className="text-sm font-bold text-gray-200 font-mono">
                {uploadedAsset.file_size_bytes
                  ? `${(uploadedAsset.file_size_bytes / (1024 * 1024)).toFixed(1)} MB`
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Configuration for Clip Generation */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-4 border-t border-gray-800">
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                Target Clip Length
              </label>
              <select
                value={targetDuration}
                onChange={(e) => setTargetDuration(parseInt(e.target.value))}
                className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-emerald-500 focus:outline-none"
              >
                <option value={15}>15s (Snappy Hook)</option>
                <option value={30}>30s (Optimal Shorts/Reels)</option>
                <option value={45}>45s (Extended Breakdown)</option>
                <option value={60}>60s (Full Discussion)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
                <Crop className="w-3.5 h-3.5 text-indigo-400" />
                Vertical Crop Mode
              </label>
              <select
                value={cropMode}
                onChange={(e) => setCropMode(e.target.value as any)}
                className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-emerald-500 focus:outline-none"
              >
                <option value="smart">Smart Crop (Subject Tracking)</option>
                <option value="blurred_background">Blurred Background Fill (Preserve 100%)</option>
                <option value="center">Center Crop (9:16)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
                <Subtitles className="w-3.5 h-3.5 text-amber-400" />
                Burned Caption Preset
              </label>
              <select
                value={captionStyle}
                onChange={(e) => setCaptionStyle(e.target.value as any)}
                className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-emerald-500 focus:outline-none"
              >
                <option value="bold_yellow">Bold Yellow (MrBeast Style)</option>
                <option value="clean_minimal">Clean Minimal White</option>
                <option value="creator_box">Creator Box (Translucent Dark)</option>
                <option value="cinematic">Cinematic Soft Ivory</option>
              </select>
            </div>
          </div>

          {/* Action Button */}
          <div className="pt-4 border-t border-gray-800 flex justify-end">
            <button
              onClick={handleStartAnalysis}
              disabled={isAnalyzing}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-lg shadow-emerald-600/25 transition-all"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing Audio &amp; Scenes...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Analyze Speech &amp; Find Viral Clips</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Candidate Clips List */}
      {clips.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Scissors className="w-4 h-4 text-emerald-400" />
                Detected Viral Candidate Clips ({clips.length})
              </h3>
              <p className="text-xs text-gray-400">
                Scored by opening hook curiosity, narrative completeness, and speech rhythm.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {clips.map((clip, idx) => {
              const isRendered = clip.status === 'completed' && clip.download_url;
              return (
                <div
                  key={clip.id}
                  className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-4 shadow-xl hover:border-gray-700 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {/* Top row with score badge */}
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-400">Clip #{idx + 1}</span>
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold font-mono">
                        {Math.round(clip.score * 100)}% Viral Score
                      </span>
                    </div>

                    <h4 className="font-bold text-sm text-gray-100 line-clamp-1">{clip.title}</h4>

                    {clip.hook && (
                      <div className="bg-[#0b0f17] border border-gray-800/80 rounded-lg p-2.5 text-xs text-amber-300 font-medium">
                        "{clip.hook}"
                      </div>
                    )}

                    {/* Boundary sliders */}
                    <div className="bg-[#0b0f17] border border-gray-800/80 rounded-lg p-3 space-y-2 text-xs">
                      <div className="flex justify-between text-gray-400 font-mono">
                        <span>Start: {clip.start_time.toFixed(1)}s</span>
                        <span>End: {clip.end_time.toFixed(1)}s</span>
                        <span className="text-indigo-400">({(clip.end_time - clip.start_time).toFixed(1)}s)</span>
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="range"
                          min="0"
                          max={clip.end_time - 2}
                          step="0.5"
                          value={clip.start_time}
                          onChange={(e) =>
                            handleUpdateClipTime(clip.id, parseFloat(e.target.value), clip.end_time)
                          }
                          className="w-1/2 h-1 bg-gray-700 rounded appearance-none accent-emerald-500"
                        />
                        <input
                          type="range"
                          min={clip.start_time + 2}
                          max={(uploadedAsset?.duration || 120)}
                          step="0.5"
                          value={clip.end_time}
                          onChange={(e) =>
                            handleUpdateClipTime(clip.id, clip.start_time, parseFloat(e.target.value))
                          }
                          className="w-1/2 h-1 bg-gray-700 rounded appearance-none accent-emerald-500"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Render / Download action */}
                  <div className="pt-3 border-t border-gray-800/80 flex items-center justify-between">
                    <span className="text-[11px] text-gray-400 uppercase font-semibold">9:16 Vertical</span>

                    {isRendered ? (
                      <a
                        href={clip.download_url}
                        download
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download MP4</span>
                      </a>
                    ) : (
                      <button
                        onClick={() => handleRenderClip(clip.id)}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                      >
                        <Film className="w-3.5 h-3.5" />
                        <span>Render 9:16 Short</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Progress modal */}
      <JobProgressModal
        jobId={activeJobId}
        isOpen={isJobModalOpen}
        onClose={() => setIsJobModalOpen(false)}
        onSuccess={handleJobSuccess}
      />
    </div>
  );
};

