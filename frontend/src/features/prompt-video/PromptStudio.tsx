import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, Video, Mic, Music, Layers, Palette, Subtitles, Play,
  Sliders, Wand2, Loader2, ArrowRight
} from 'lucide-react';
import { PromptPlanningRequest, StructuredScenePlan } from '../../types';
import { StoryboardEditor } from './StoryboardEditor';
import { JobProgressModal } from '../../components/common/JobProgressModal';
import { api } from '../../services/api';

const INSPIRATION_PROMPTS = [
  'Create a 30-second cinematic Instagram Reel about an AI-powered fitness product with energetic visuals and strong CTA.',
  'Create a fast-paced YouTube Short unveiling an ultra-sleek mechanical keyboard with macro lighting and tactile sound.',
  'Create a 15-second viral hook explaining why traditional spreadsheets are dead for modern finance teams.',
  'Create a luxurious travel reel capturing a cyber-aesthetic evening in Tokyo with neon reflections and upbeat synth.'
];

export const PromptStudio: React.FC = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState(INSPIRATION_PROMPTS[0]);
  const [platform, setPlatform] = useState('instagram_reels');
  const [duration, setDuration] = useState(30);
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [visualStyle, setVisualStyle] = useState('cinematic');
  const [voiceoverEnabled, setVoiceoverEnabled] = useState(true);
  const [voiceSelection, setVoiceSelection] = useState('energetic_male');
  const [captionStyle, setCaptionStyle] = useState('bold_yellow');
  const [bgMusic, setBgMusic] = useState('upbeat_synth');
  const [numScenes, setNumScenes] = useState(4);
  const [videoEngine, setVideoEngine] = useState('omni');

  const [storyboard, setStoryboard] = useState<StructuredScenePlan[] | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isJobModalOpen, setIsJobModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateStoryboard = async () => {
    setIsPlanning(true);
    setError(null);
    try {
      const plan = await api.generateStoryboard({
        prompt,
        target_platform: platform,
        duration_seconds: duration,
        aspect_ratio: aspectRatio,
        visual_style: visualStyle,
        voiceover_enabled: voiceoverEnabled,
        voice_selection: voiceSelection,
        caption_style: captionStyle,
        background_music: bgMusic,
        language: 'en',
        num_scenes: numScenes,
        quality: 'high',
        video_engine: videoEngine,
      });
      setStoryboard(plan.scenes);
    } catch (err: any) {
      setError(err.message || 'Failed to generate storyboard');
    } finally {
      setIsPlanning(false);
    }
  };

  const handleTriggerRender = async () => {
    setError(null);
    try {
      const payload: PromptPlanningRequest = {
        prompt,
        target_platform: platform,
        duration_seconds: duration,
        aspect_ratio: aspectRatio,
        visual_style: visualStyle,
        voiceover_enabled: voiceoverEnabled,
        voice_selection: voiceSelection,
        caption_style: captionStyle,
        background_music: bgMusic,
        language: 'en',
        num_scenes: storyboard ? storyboard.length : numScenes,
        quality: 'high',
        video_engine: videoEngine,
      };
      const job = await api.triggerPromptToVideo(payload);
      setActiveJobId(job.id);
      setIsJobModalOpen(true);
    } catch (err: any) {
      setError(err.message || 'Failed to start video generation');
    }
  };

  const handleJobSuccess = (completedJob: any) => {
    // Navigate to project detail page
    setTimeout(() => {
      navigate(`/project/${completedJob.project_id}`);
    }, 1200);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-indigo-900/40 via-purple-900/20 to-transparent border border-indigo-500/20 rounded-2xl p-6 sm:p-8 relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-3">
            <Wand2 className="w-3.5 h-3.5" />
            Workflow A: Generative Prompt-to-Video
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Turn Any Idea Into a High-Converting Short
          </h2>
          <p className="mt-2 text-sm text-gray-300 leading-relaxed">
            ClipForge plans scenes, generates video clips, composes audio &amp; narration, styles subtitles,
            and renders a vertical 9:16 MP4 ready for Reels and Shorts.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Main Form */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        {/* Prompt Input */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-semibold text-gray-200 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Creative Concept Prompt
            </label>
            <span className="text-xs text-gray-500 font-mono">{prompt.length} chars</span>
          </div>
          <textarea
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full text-sm bg-[#0b0f17] border border-gray-800 rounded-xl p-4 text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-all"
            placeholder="Describe your video idea, product, visual hook, or story in detail..."
          />

          {/* Quick inspiration pills */}
          <div className="mt-3 flex flex-wrap gap-2 items-center">
            <span className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold">Try:</span>
            {INSPIRATION_PROMPTS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setPrompt(p)}
                className="text-xs px-2.5 py-1 rounded-full bg-gray-800/80 hover:bg-gray-700 text-gray-300 border border-gray-700/60 transition-colors truncate max-w-[260px]"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Configuration Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 pt-4 border-t border-gray-800/80">
          {/* Video Engine Selection */}
          <div>
            <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              Motion Engine
            </label>
            <select
              value={videoEngine}
              onChange={(e) => setVideoEngine(e.target.value)}
              className="w-full text-xs bg-[#0b0f17] border border-cyan-800/60 rounded-lg p-2.5 text-cyan-200 focus:border-cyan-400 focus:outline-none"
            >
              <option value="omni">OmniForge (3D Depth Parallax)</option>
              <option value="pexels">Authentic 4K Video (Pexels)</option>
              <option value="veo">Google Veo 2 (Generative AI)</option>
            </select>
          </div>

          {/* Target Platform */}
          <div>
            <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
              <Video className="w-3.5 h-3.5 text-indigo-400" />
              Platform &amp; Format
            </label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="instagram_reels">Instagram Reels (9:16)</option>
              <option value="youtube_shorts">YouTube Shorts (9:16)</option>
              <option value="tiktok">TikTok (9:16)</option>
            </select>
          </div>

          {/* Duration Slider */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-emerald-400" />
                Target Duration
              </label>
              <span className="text-xs font-mono font-bold text-indigo-400">{duration}s</span>
            </div>
            <input
              type="range"
              min="10"
              max="60"
              step="5"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex justify-between text-[10px] text-gray-500 mt-1 font-mono">
              <span>10s</span>
              <span>30s (Ideal)</span>
              <span>60s</span>
            </div>
          </div>

          {/* Visual Style */}
          <div>
            <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
              <Palette className="w-3.5 h-3.5 text-purple-400" />
              Visual Aesthetic
            </label>
            <select
              value={visualStyle}
              onChange={(e) => setVisualStyle(e.target.value)}
              className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="cinematic">Cinematic 4K Dramatic</option>
              <option value="commercial">Dynamic Tech Commercial</option>
              <option value="anime">Anime High Energy</option>
              <option value="3d_render">Hyper-realistic 3D Render</option>
            </select>
          </div>

          {/* Number of Scenes */}
          <div>
            <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              Scene Count
            </label>
            <select
              value={numScenes}
              onChange={(e) => setNumScenes(parseInt(e.target.value))}
              className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value={3}>3 Scenes (Paced)</option>
              <option value={4}>4 Scenes (Balanced)</option>
              <option value={5}>5 Scenes (Fast-cut)</option>
              <option value={6}>6 Scenes (High Energy)</option>
            </select>
          </div>
        </div>

        {/* Audio & Caption Customization Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-4 border-t border-gray-800/80">
          {/* Voiceover Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                <Mic className="w-3.5 h-3.5 text-indigo-400" />
                AI Voiceover
              </label>
              <input
                type="checkbox"
                checked={voiceoverEnabled}
                onChange={(e) => setVoiceoverEnabled(e.target.checked)}
                className="rounded accent-indigo-500 cursor-pointer"
              />
            </div>
            <select
              disabled={!voiceoverEnabled}
              value={voiceSelection}
              onChange={(e) => setVoiceSelection(e.target.value)}
              className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-indigo-500 focus:outline-none disabled:opacity-40"
            >
              <option value="energetic_male">Energetic Male (Viral Hook)</option>
              <option value="friendly_female">Friendly Female (Narrator)</option>
              <option value="deep_narrator">Deep Cinematic Male</option>
            </select>
          </div>

          {/* Caption Theme */}
          <div>
            <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
              <Subtitles className="w-3.5 h-3.5 text-yellow-400" />
              Burned Subtitle Style
            </label>
            <select
              value={captionStyle}
              onChange={(e) => setCaptionStyle(e.target.value)}
              className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="bold_yellow">Bold Yellow (MrBeast Style)</option>
              <option value="clean_minimal">Clean Minimal White</option>
              <option value="creator_box">Creator Box (Dark Backdrop)</option>
              <option value="cinematic">Cinematic Soft Ivory</option>
            </select>
          </div>

          {/* Background Music */}
          <div>
            <label className="text-xs font-semibold text-gray-300 mb-2 block flex items-center gap-1.5">
              <Music className="w-3.5 h-3.5 text-rose-400" />
              Background Soundtrack
            </label>
            <select
              value={bgMusic}
              onChange={(e) => setBgMusic(e.target.value)}
              className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="upbeat_synth">Upbeat Electro Synth</option>
              <option value="ambient_chill">Ambient Chill Wave</option>
              <option value="energetic_trap">Energetic Trap Beat</option>
              <option value="none">None (No Background Music)</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-gray-800">
          <button
            type="button"
            onClick={handleGenerateStoryboard}
            disabled={isPlanning || !prompt.trim()}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-colors disabled:opacity-50"
          >
            {isPlanning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>AI Director Planning...</span>
              </>
            ) : (
              <>
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>Generate Storyboard First</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleTriggerRender}
            disabled={!prompt.trim()}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 via-indigo-500 to-emerald-500 hover:from-indigo-500 hover:to-emerald-400 text-white shadow-lg shadow-indigo-600/30 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Generate &amp; Render Full Video</span>
          </button>
        </div>
      </div>

      {/* Storyboard Editor Section (Rendered when generated) */}
      {storyboard && (
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
          <StoryboardEditor
            scenes={storyboard}
            onUpdateScene={(idx, updated) => {
              const copy = [...storyboard];
              copy[idx] = { ...copy[idx], ...updated };
              setStoryboard(copy);
            }}
            onDeleteScene={(idx) => {
              setStoryboard(storyboard.filter((_, i) => i !== idx));
            }}
            onAddScene={() => {
              setStoryboard([
                ...storyboard,
                {
                  scene_number: storyboard.length + 1,
                  duration_seconds: 5.0,
                  purpose: 'feature',
                  visual_prompt: 'High resolution product demonstration with smooth lighting',
                  camera_movement: 'slow_push_in',
                  narration: 'Experience next level performance.',
                  caption: 'NEXT LEVEL PERFORMANCE',
                  transition: 'fade',
                },
              ]);
            }}
          />

          <div className="flex justify-end pt-4 border-t border-gray-800">
            <button
              type="button"
              onClick={handleTriggerRender}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all"
            >
              <span>Render Approved Storyboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Job Progress Modal */}
      <JobProgressModal
        jobId={activeJobId}
        isOpen={isJobModalOpen}
        onClose={() => setIsJobModalOpen(false)}
        onSuccess={handleJobSuccess}
      />
    </div>
  );
};
