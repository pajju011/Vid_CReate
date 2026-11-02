import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Download, RefreshCw, Film, CheckCircle2, AlertTriangle,
  Clock, HardDrive, Maximize, Scissors, Sparkles, Layers, Video
} from 'lucide-react';
import { ProjectDetail, VideoAsset } from '../types';
import { api } from '../services/api';
import { VideoPlayer } from '../components/common/VideoPlayer';

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProject = async () => {
    if (!projectId) return;
    try {
      const data = await api.getProject(projectId);
      setProject(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load project details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProject();
  }, [projectId]);

  if (loading) {
    return (
      <div className="py-20 text-center text-gray-400 text-sm">
        Loading project workspace...
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="py-20 text-center space-y-4">
        <p className="text-rose-400 text-sm">{error || 'Project not found'}</p>
        <Link to="/" className="text-xs font-semibold text-indigo-400 hover:underline">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  // Find the primary rendered video asset
  const finalAsset = project.assets.find(
    (a) => a.asset_type === 'rendered_final' || a.asset_type === 'rendered_short'
  );

  const qcReport = finalAsset?.metadata_json?.qc_report;

  return (
    <div className="py-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-gray-800">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="p-2 rounded-xl bg-gray-900 border border-gray-800 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
                  project.project_type === 'prompt_to_video'
                    ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
                    : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                }`}
              >
                {project.project_type.replace(/_/g, ' ')}
              </span>
              <span className="text-xs font-semibold text-emerald-400">● {project.status}</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-white mt-1">{project.name}</h1>
          </div>
        </div>

        {finalAsset && (
          <a
            href={finalAsset.download_url}
            download
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-lg shadow-emerald-600/25 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Download Final MP4</span>
          </a>
        )}
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Video Preview Player & Technical Specs */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-[#111827] border border-gray-800 rounded-3xl p-6 shadow-2xl">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Film className="w-4 h-4 text-indigo-400" />
              Vertical 9:16 Preview Player
            </h3>

            {finalAsset ? (
              <VideoPlayer
                src={finalAsset.download_url || ''}
                aspectRatio="9:16"
                title={project.name}
                downloadUrl={finalAsset.download_url}
              />
            ) : (
              <div className="aspect-[9/16] max-w-[320px] mx-auto rounded-2xl bg-[#0b0f17] border border-gray-800 flex flex-col items-center justify-center p-6 text-center">
                <Video className="w-12 h-12 text-gray-700 mb-2" />
                <p className="text-xs font-semibold text-gray-400">Rendering in progress</p>
                <p className="text-[11px] text-gray-500 mt-1">Final video preview will appear here upon completion.</p>
              </div>
            )}
          </div>

          {/* Technical Quality Control Card */}
          {qcReport && (
            <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-3 shadow-xl">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-gray-200 uppercase tracking-wider flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Technical QC Verification
                </h4>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                    qcReport.status === 'passed'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {qcReport.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2">
                <div className="bg-[#0b0f17] p-2.5 rounded-lg border border-gray-800/80">
                  <span className="text-[10px] text-gray-500 block">Resolution</span>
                  <span className="font-mono font-bold text-gray-200">
                    {qcReport.metrics?.width}x{qcReport.metrics?.height} (9:16)
                  </span>
                </div>
                <div className="bg-[#0b0f17] p-2.5 rounded-lg border border-gray-800/80">
                  <span className="text-[10px] text-gray-500 block">Audio Stream</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {qcReport.metrics?.has_audio ? 'Verified AAC' : 'None'}
                  </span>
                </div>
                <div className="bg-[#0b0f17] p-2.5 rounded-lg border border-gray-800/80">
                  <span className="text-[10px] text-gray-500 block">Duration</span>
                  <span className="font-mono font-bold text-gray-200">
                    {qcReport.metrics?.duration?.toFixed(1)}s
                  </span>
                </div>
                <div className="bg-[#0b0f17] p-2.5 rounded-lg border border-gray-800/80">
                  <span className="text-[10px] text-gray-500 block">Codec</span>
                  <span className="font-mono font-bold text-gray-200">H.264 / AAC</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Scenes or Clips Timeline */}
        <div className="lg:col-span-7 space-y-6">
          {project.scenes.length > 0 && (
            <div className="bg-[#111827] border border-gray-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                Production Storyboard Scenes ({project.scenes.length})
              </h3>

              <div className="space-y-3">
                {project.scenes.map((scene) => (
                  <div
                    key={scene.id}
                    className="bg-[#0b0f17] border border-gray-800 rounded-xl p-4 space-y-2 hover:border-gray-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-xs">
                          {scene.scene_number}
                        </span>
                        <span className="text-xs font-semibold text-gray-300">
                          Scene #{scene.scene_number} ({scene.duration}s)
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-emerald-400 capitalize">
                        ● {scene.status}
                      </span>
                    </div>

                    <p className="text-xs text-gray-300 leading-relaxed">
                      <strong>Prompt:</strong> {scene.prompt}
                    </p>

                    {scene.caption && (
                      <div className="text-xs text-yellow-300 font-bold uppercase tracking-wider bg-black/40 px-2 py-1 rounded inline-block">
                        Subtitle: {scene.caption}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {project.clips.length > 0 && (
            <div className="bg-[#111827] border border-gray-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Scissors className="w-5 h-5 text-emerald-400" />
                Generated Shorts ({project.clips.length})
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {project.clips.map((clip, i) => (
                  <div
                    key={clip.id}
                    className="bg-[#0b0f17] border border-gray-800 rounded-xl p-4 space-y-3 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-gray-400">Clip #{i + 1}</span>
                        <span className="text-[11px] font-bold text-emerald-400 font-mono">
                          {Math.round(clip.score * 100)}% Viral Fit
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-white">{clip.title}</h4>
                      {clip.hook && (
                        <p className="text-xs text-amber-300 font-medium mt-1">"{clip.hook}"</p>
                      )}
                      <div className="text-[11px] text-gray-500 font-mono mt-2">
                        {clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s ({clip.duration}s)
                      </div>
                    </div>

                    <div className="pt-3 border-t border-gray-800 flex justify-end">
                      {clip.download_url && (
                        <a
                          href={clip.download_url}
                          download
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download Short</span>
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

