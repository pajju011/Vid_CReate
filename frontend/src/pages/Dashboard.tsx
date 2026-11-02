import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Film, Sparkles, Scissors, Clock, ArrowRight, Play, CheckCircle2,
  AlertCircle, Plus, Layers, Video, HardDrive, ShieldCheck
} from 'lucide-react';
import { Project } from '../types';
import { api } from '../services/api';

export const Dashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [storageStats, setStorageStats] = useState<{
    media_storage_path: string;
    temp_media_path: string;
    free_gb: number;
    total_gb: number;
  } | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [projectsData, statsData] = await Promise.allSettled([
          api.listProjects(),
          api.getStorageStats(),
        ]);
        if (projectsData.status === 'fulfilled') {
          setProjects(projectsData.value);
        }
        if (statsData.status === 'fulfilled') {
          setStorageStats(statsData.value);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-10 py-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-950 via-slate-900 to-[#0b0f17] border border-gray-800 p-8 sm:p-10 shadow-2xl">
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold border border-indigo-500/30">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            AI Video Production Automation
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Create Viral Reels &amp; Shorts in Seconds
          </h1>
          <p className="text-sm text-gray-300 leading-relaxed">
            ClipForge automates scriptwriting, scene composition, smart vertical cropping, burned subtitles,
            and FFmpeg rendering for Instagram Reels and YouTube Shorts.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              to="/create"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Create New Video</span>
            </Link>
            <Link
              to="/settings"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-gray-800/80 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-colors"
            >
              <span>View Providers</span>
            </Link>
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-indigo-600/10 to-transparent pointer-events-none" />
      </div>

      {/* External Storage Status Bar */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-4 sm:p-5 flex flex-wrap items-center justify-between gap-4 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-bold text-gray-200 uppercase tracking-wider">External Media Storage</h4>
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <ShieldCheck className="w-3 h-3" /> Project Isolated
              </span>
            </div>
            <p className="text-xs text-gray-400 font-mono mt-0.5">
              Target: <span className="text-indigo-300 font-medium">{storageStats?.media_storage_path || 'D:/AI_Video_Storage'}</span>
              {storageStats && (
                <span className="text-gray-500 ml-2">
                  ({storageStats.free_gb.toFixed(1)} GB free of {storageStats.total_gb.toFixed(1)} GB)
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/settings"
            className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors flex items-center gap-1"
          >
            Manage Storage <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          to="/create?tab=prompt"
          className="group relative bg-[#111827] border border-gray-800 hover:border-indigo-500/50 rounded-2xl p-6 transition-all shadow-xl hover:shadow-indigo-500/10"
        >
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform border border-indigo-500/20">
            <WandIcon />
          </div>
          <h3 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors flex items-center justify-between">
            <span>Workflow A: Prompt to Video</span>
            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
          </h3>
          <p className="text-xs text-gray-400 mt-2 leading-relaxed">
            Enter a creative prompt. The agent plans a structured script and storyboard, generates scene assets,
            mixes voiceover &amp; music, and renders a 9:16 vertical video.
          </p>
        </Link>

        <Link
          to="/create?tab=shorts"
          className="group relative bg-[#111827] border border-gray-800 hover:border-emerald-500/50 rounded-2xl p-6 transition-all shadow-xl hover:shadow-emerald-500/10"
        >
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform border border-emerald-500/20">
            <Scissors className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white group-hover:text-emerald-400 transition-colors flex items-center justify-between">
            <span>Workflow B: Video to Shorts / Reels</span>
            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
          </h3>
          <p className="text-xs text-gray-400 mt-2 leading-relaxed">
            Upload any existing landscape or horizontal video. ClipForge transcribes speech, detects viral hooks,
            tracks the subject for 9:16 vertical crop, and burns animated subtitles.
          </p>
        </Link>
      </div>

      {/* Recent Projects List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Film className="w-5 h-5 text-indigo-400" />
            Recent Production Projects
          </h2>
          <span className="text-xs text-gray-500 font-mono">{projects.length} Total</span>
        </div>

        {loading ? (
          <div className="h-40 flex items-center justify-center text-gray-500 text-sm">
            Loading recent projects...
          </div>
        ) : projects.length === 0 ? (
          <div className="bg-[#111827] border border-gray-800/80 rounded-2xl p-12 text-center">
            <Video className="w-10 h-10 text-gray-600 mx-auto mb-3" />
            <h3 className="text-sm font-bold text-gray-300">No projects yet</h3>
            <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
              Start by creating a video from a prompt or converting an existing horizontal video into shorts.
            </p>
            <Link
              to="/create"
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create First Video</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {projects.map((proj) => (
              <Link
                key={proj.id}
                to={`/project/${proj.id}`}
                className="group bg-[#111827] border border-gray-800 hover:border-gray-700 rounded-2xl p-5 space-y-4 transition-all shadow-lg hover:shadow-indigo-500/5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
                        proj.project_type === 'prompt_to_video'
                          ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      }`}
                    >
                      {proj.project_type === 'prompt_to_video' ? 'Prompt AI' : 'Shorts Engine'}
                    </span>
                    <span
                      className={`text-xs font-semibold capitalize ${
                        proj.status === 'ready'
                          ? 'text-emerald-400'
                          : proj.status === 'processing'
                          ? 'text-amber-400'
                          : 'text-gray-400'
                      }`}
                    >
                      ● {proj.status}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-gray-100 group-hover:text-indigo-400 transition-colors line-clamp-1">
                    {proj.name}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1 capitalize">{proj.platform.replace(/_/g, ' ')}</p>
                </div>

                <div className="pt-3 border-t border-gray-800 flex items-center justify-between text-xs text-gray-400">
                  <span className="flex items-center gap-1 font-mono text-[11px]">
                    <Clock className="w-3 h-3" />
                    {new Date(proj.created_at).toLocaleDateString()}
                  </span>
                  <span className="font-semibold text-indigo-400 group-hover:translate-x-1 transition-transform flex items-center gap-1">
                    Open <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const WandIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

