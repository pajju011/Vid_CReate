import React, { useEffect, useState } from 'react';
import { Settings, ShieldCheck, CheckCircle2, AlertCircle, Cpu, Key, HelpCircle } from 'lucide-react';
import { ProvidersStatusResponse } from '../types';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [providersStatus, setProvidersStatus] = useState<ProvidersStatusResponse | null>(null);
  const [settingsSummary, setSettingsSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const [pData, sData] = await Promise.all([
          api.getProvidersStatus(),
          api.getSettings(),
        ]);
        setProvidersStatus(pData);
        setSettingsSummary(sData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchInfo();
  }, []);

  return (
    <div className="py-6 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
          <Settings className="w-6 h-6 text-indigo-400" />
          AI Providers &amp; Engine Configuration
        </h1>
        <p className="text-xs text-gray-400 mt-1">
          ClipForge supports pluggable production AI providers and local zero-cost deterministic engines.
        </p>
      </div>

      {/* Demo Mode Notice */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-teal-900/20 to-transparent border border-emerald-500/20 rounded-2xl p-6">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Local Development Engine Active</h3>
            <p className="text-xs text-gray-300 mt-1 leading-relaxed">
              ClipForge includes built-in local FFmpeg synthesis, smart face &amp; subject tracking,
              ASS subtitle compilation, and scene detection that run completely offline without requiring paid API keys.
            </p>
          </div>
        </div>
      </div>

      {/* Provider Slots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* LLM Slot */}
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">1. LLM Creative Planner</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                providersStatus?.llm.is_real_api
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
              }`}
            >
              {providersStatus?.llm.is_real_api ? 'Live API Connected' : 'Local Planner Active'}
            </span>
          </div>
          <p className="text-xs text-gray-300 font-medium">{providersStatus?.llm.model_info}</p>
          <div className="text-[11px] text-gray-500 font-mono">
            Provider: {providersStatus?.llm.configured_provider}
          </div>
        </div>

        {/* Video Slot */}
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">2. Video Generator</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                providersStatus?.video.is_real_api
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
              }`}
            >
              {providersStatus?.video.is_real_api ? 'Luma / Runway API' : 'Local FFmpeg Synthesizer'}
            </span>
          </div>
          <p className="text-xs text-gray-300 font-medium">{providersStatus?.video.model_info}</p>
          <div className="text-[11px] text-gray-500 font-mono">
            Provider: {providersStatus?.video.configured_provider}
          </div>
        </div>

        {/* Audio Slot */}
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">3. Audio &amp; Voiceover</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                providersStatus?.audio.is_real_api
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
              }`}
            >
              {providersStatus?.audio.is_real_api ? 'ElevenLabs / OpenAI' : 'Local Tone Synth'}
            </span>
          </div>
          <p className="text-xs text-gray-300 font-medium">{providersStatus?.audio.model_info}</p>
          <div className="text-[11px] text-gray-500 font-mono">
            Provider: {providersStatus?.audio.configured_provider}
          </div>
        </div>

        {/* Transcription Slot */}
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">4. Transcription Provider</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                providersStatus?.transcription.is_real_api
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
              }`}
            >
              {providersStatus?.transcription.is_real_api ? 'OpenAI Whisper-1' : 'Local Timestamp Engine'}
            </span>
          </div>
          <p className="text-xs text-gray-300 font-medium">{providersStatus?.transcription.model_info}</p>
          <div className="text-[11px] text-gray-500 font-mono">
            Provider: {providersStatus?.transcription.configured_provider}
          </div>
        </div>
      </div>

      {/* How to configure API keys */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 sm:p-8 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Key className="w-4 h-4 text-amber-400" />
          Configuring Production API Keys
        </h3>
        <p className="text-xs text-gray-300 leading-relaxed">
          To switch any provider from local mode to real cloud generation, create or edit the <code className="bg-gray-800 px-1.5 py-0.5 rounded text-amber-300">.env</code> file in the project root:
        </p>

        <pre className="bg-[#0b0f17] border border-gray-800 rounded-xl p-4 text-xs font-mono text-gray-300 overflow-x-auto">
{`# Google Gemini LLM
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key_here

# Luma Dream Machine Video Generation
VIDEO_PROVIDER=luma
VIDEO_API_KEY=your_luma_api_key_here

# ElevenLabs Speech Synthesis
AUDIO_PROVIDER=elevenlabs
AUDIO_API_KEY=your_elevenlabs_api_key_here

# OpenAI Whisper Transcription
TRANSCRIPTION_PROVIDER=whisper
TRANSCRIPTION_API_KEY=your_openai_api_key_here`}
        </pre>
      </div>
    </div>
  );
};

