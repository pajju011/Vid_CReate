import React, { useEffect, useState } from 'react';
import {
  Settings, ShieldCheck, CheckCircle2, AlertCircle, Cpu, Key, HelpCircle,
  HardDrive, Trash2, Lock, Globe, Server, Activity, ShieldAlert
} from 'lucide-react';
import { ProvidersStatusResponse, PrivacyStatus, TransferAuditLog } from '../types';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [providersStatus, setProvidersStatus] = useState<ProvidersStatusResponse | null>(null);
  const [settingsSummary, setSettingsSummary] = useState<any>(null);
  const [storageStats, setStorageStats] = useState<any>(null);
  const [privacyStatus, setPrivacyStatus] = useState<PrivacyStatus | null>(null);
  const [auditLogs, setAuditLogs] = useState<TransferAuditLog[]>([]);
  const [cleaning, setCleaning] = useState(false);
  const [cleanMessage, setCleanMessage] = useState<string | null>(null);
  const [savingPrivacy, setSavingPrivacy] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchInfo = async () => {
    try {
      const [pData, sData, stData, privData, logsData] = await Promise.all([
        api.getProvidersStatus(),
        api.getSettings(),
        api.getStorageStats().catch(() => null),
        api.getPrivacyStatus().catch(() => null),
        api.getTransferAuditLogs(20).catch(() => []),
      ]);
      setProvidersStatus(pData);
      setSettingsSummary(sData);
      setStorageStats(stData);
      setPrivacyStatus(privData);
      setAuditLogs(logsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInfo();
  }, []);

  const handleUpdatePrivacyTier = async (mode: 'strict_local' | 'private_hybrid' | 'cloud_assisted') => {
    setSavingPrivacy(true);
    try {
      const updated = await api.updatePrivacySettings({ privacy_mode: mode });
      setPrivacyStatus(updated);
      const logs = await api.getTransferAuditLogs(20);
      setAuditLogs(logs);
    } catch (err) {
      console.error(err);
    } finally {
      setSavingPrivacy(false);
    }
  };

  const handleToggleCloudSwitch = async () => {
    if (!privacyStatus) return;
    setSavingPrivacy(true);
    try {
      const updated = await api.updatePrivacySettings({
        allow_cloud_transfers: !privacyStatus.allow_cloud_transfers
      });
      setPrivacyStatus(updated);
      const logs = await api.getTransferAuditLogs(20);
      setAuditLogs(logs);
    } catch (err) {
      console.error(err);
    } finally {
      setSavingPrivacy(false);
    }
  };

  const handleClearAuditLogs = async () => {
    try {
      await api.clearTransferAuditLogs();
      setAuditLogs([]);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCleanTemp = async () => {
    setCleaning(true);
    setCleanMessage(null);
    try {
      const res = await api.cleanupTempStorage();
      setCleanMessage(res.message);
      await fetchInfo();
    } catch (err: any) {
      setCleanMessage(err.message || 'Cleanup failed');
    } finally {
      setCleaning(false);
    }
  };

  return (
    <div className="py-6 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
          <Settings className="w-6 h-6 text-indigo-400" />
          AI Providers &amp; Privacy Engine Configuration
        </h1>
        <p className="text-xs text-gray-400 mt-1">
          Configure multi-provider model routing, privacy boundaries, and external media storage.
        </p>
      </div>

      {/* Privacy-Aware Model Router & Governance Card */}
      <div className="bg-[#111827] border border-gray-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Privacy-Aware Model Gateway
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                  privacyStatus?.privacy_mode === 'strict_local'
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : privacyStatus?.privacy_mode === 'private_hybrid'
                    ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                }`}>
                  {privacyStatus?.privacy_mode?.replace('_', ' ').toUpperCase() || 'STRICT LOCAL'}
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Enforces zero-data leakage boundaries and checks each external request against the privacy policy.
              </p>
            </div>
          </div>

          {/* Cloud Kill Switch */}
          <div className="flex items-center gap-3 bg-[#0b0f17] px-4 py-2 rounded-2xl border border-gray-800">
            <span className="text-xs text-gray-300 font-medium">Cloud Transfers:</span>
            <button
              onClick={handleToggleCloudSwitch}
              disabled={savingPrivacy}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                privacyStatus?.allow_cloud_transfers ? 'bg-indigo-600' : 'bg-gray-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  privacyStatus?.allow_cloud_transfers ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-xs font-mono font-bold ${privacyStatus?.allow_cloud_transfers ? 'text-indigo-400' : 'text-gray-400'}`}>
              {privacyStatus?.allow_cloud_transfers ? 'ENABLED' : 'DISABLED'}
            </span>
          </div>
        </div>

        {/* Privacy Tier Selector */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Strict Local */}
          <button
            onClick={() => handleUpdatePrivacyTier('strict_local')}
            disabled={savingPrivacy}
            className={`p-4 rounded-2xl border text-left transition-all ${
              privacyStatus?.privacy_mode === 'strict_local'
                ? 'bg-emerald-950/30 border-emerald-500/50 shadow-lg shadow-emerald-950/50'
                : 'bg-[#0b0f17] border-gray-800/80 hover:border-gray-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                1. Strict Local
              </span>
              {privacyStatus?.privacy_mode === 'strict_local' && (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              )}
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              100% offline. Zero cloud calls. Uses Ollama local LLM, Edge-TTS, and local FFmpeg synthesis.
            </p>
          </button>

          {/* Private Hybrid */}
          <button
            onClick={() => handleUpdatePrivacyTier('private_hybrid')}
            disabled={savingPrivacy}
            className={`p-4 rounded-2xl border text-left transition-all ${
              privacyStatus?.privacy_mode === 'private_hybrid'
                ? 'bg-indigo-950/30 border-indigo-500/50 shadow-lg shadow-indigo-950/50'
                : 'bg-[#0b0f17] border-gray-800/80 hover:border-gray-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Server className="w-4 h-4 text-indigo-400" />
                2. Private Hybrid
              </span>
              {privacyStatus?.privacy_mode === 'private_hybrid' && (
                <CheckCircle2 className="w-4 h-4 text-indigo-400" />
              )}
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              Default mode. Keeps metadata &amp; storage local. Allows authorized cloud generation with vetting.
            </p>
          </button>

          {/* Cloud Assisted */}
          <button
            onClick={() => handleUpdatePrivacyTier('cloud_assisted')}
            disabled={savingPrivacy}
            className={`p-4 rounded-2xl border text-left transition-all ${
              privacyStatus?.privacy_mode === 'cloud_assisted'
                ? 'bg-amber-950/30 border-amber-500/50 shadow-lg shadow-amber-950/50'
                : 'bg-[#0b0f17] border-gray-800/80 hover:border-gray-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-amber-400" />
                3. Cloud Assisted
              </span>
              {privacyStatus?.privacy_mode === 'cloud_assisted' && (
                <CheckCircle2 className="w-4 h-4 text-amber-400" />
              )}
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              Unlocks full multi-cloud models (Google Veo, Runway, Luma, Kling, Seedance, ElevenLabs).
            </p>
          </button>
        </div>

        {/* Audit Log Table */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-300 flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              Transfer Audit History
            </span>
            {auditLogs.length > 0 && (
              <button
                onClick={handleClearAuditLogs}
                className="text-[11px] text-gray-500 hover:text-gray-300 transition-colors"
              >
                Clear History
              </button>
            )}
          </div>

          {auditLogs.length === 0 ? (
            <div className="bg-[#0b0f17] border border-gray-800/80 rounded-2xl p-4 text-center text-xs text-gray-500">
              No cloud transfer events logged yet. System running cleanly within privacy boundaries.
            </div>
          ) : (
            <div className="bg-[#0b0f17] border border-gray-800/80 rounded-2xl overflow-hidden max-h-48 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-900/60 text-gray-400 uppercase text-[10px] font-mono border-b border-gray-800">
                  <tr>
                    <th className="p-2.5">Time</th>
                    <th className="p-2.5">Provider</th>
                    <th className="p-2.5">Task</th>
                    <th className="p-2.5">Type</th>
                    <th className="p-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60 text-gray-300">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-900/30">
                      <td className="p-2.5 font-mono text-gray-500 text-[11px]">
                        {log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'now'}
                      </td>
                      <td className="p-2.5 font-bold capitalize text-white">{log.provider}</td>
                      <td className="p-2.5 text-gray-400">{log.request_type}</td>
                      <td className="p-2.5">
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          log.is_cloud ? 'bg-amber-500/10 text-amber-400' : 'bg-emerald-500/10 text-emerald-400'
                        }`}>
                          {log.is_cloud ? 'Cloud' : 'Local'}
                        </span>
                      </td>
                      <td className="p-2.5">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          log.allowed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                        }`}>
                          {log.allowed ? 'ALLOWED' : 'BLOCKED'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
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
              {providersStatus?.llm.is_real_api ? 'API Active' : 'Local Planner Active'}
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
              {providersStatus?.video.is_real_api ? 'Multi-Provider Cloud' : 'Local HD Synthesizer'}
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
              {providersStatus?.audio.is_real_api ? 'ElevenLabs / Edge-TTS' : 'Local Audio Synth'}
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
              {providersStatus?.transcription.is_real_api ? 'Whisper-1 API' : 'Local Speech Transcriber'}
            </span>
          </div>
          <p className="text-xs text-gray-300 font-medium">{providersStatus?.transcription.model_info}</p>
          <div className="text-[11px] text-gray-500 font-mono">
            Provider: {providersStatus?.transcription.configured_provider}
          </div>
        </div>
      </div>

      {/* External Storage Diagnostics Card */}
      {storageStats && (
        <div className="bg-[#111827] border border-gray-800 rounded-3xl p-6 sm:p-8 space-y-5 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <HardDrive className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  External Local Video Storage
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Active Outside Workspace
                  </span>
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  All generated media, uploads, draft clips, and temp processing files are isolated outside the project directory.
                </p>
              </div>
            </div>

            <button
              onClick={handleCleanTemp}
              disabled={cleaning}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              <span>{cleaning ? 'Purging Temp Files...' : 'Purge Stale Temp Files'}</span>
            </button>
          </div>

          {cleanMessage && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
              {cleanMessage}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="bg-[#0b0f17] p-3 rounded-xl border border-gray-800/80">
              <span className="text-[10px] text-gray-500 block uppercase font-bold">Media Storage Path</span>
              <span className="font-mono text-gray-200 text-[11px] truncate block mt-0.5" title={storageStats.media_storage_path}>
                {storageStats.media_storage_path}
              </span>
            </div>
            <div className="bg-[#0b0f17] p-3 rounded-xl border border-gray-800/80">
              <span className="text-[10px] text-gray-500 block uppercase font-bold">Temp Processing Path</span>
              <span className="font-mono text-gray-200 text-[11px] truncate block mt-0.5" title={storageStats.temp_media_path}>
                {storageStats.temp_media_path}
              </span>
            </div>
            <div className="bg-[#0b0f17] p-3 rounded-xl border border-gray-800/80">
              <span className="text-[10px] text-gray-500 block uppercase font-bold">Available Disk Space</span>
              <span className="font-mono font-bold text-emerald-400 text-sm block mt-0.5">
                {storageStats.free_gb} GB Free <span className="text-gray-500 text-xs">({storageStats.total_gb} GB Total)</span>
              </span>
            </div>
            <div className="bg-[#0b0f17] p-3 rounded-xl border border-gray-800/80">
              <span className="text-[10px] text-gray-500 block uppercase font-bold">External Media Count</span>
              <span className="font-mono font-bold text-gray-200 text-sm block mt-0.5">
                {storageStats.rendered_videos_count} Final · {storageStats.uploads_count} Uploads
              </span>
            </div>
          </div>
        </div>
      )}

      {/* How to configure API keys */}
      <div className="bg-[#111827] border border-gray-800 rounded-3xl p-6 sm:p-8 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Key className="w-4 h-4 text-amber-400" />
          Configuring Multi-Provider Production Keys
        </h3>
        <p className="text-xs text-gray-300 leading-relaxed">
          Configure external video, audio, and language generation keys in your <code className="bg-gray-800 px-1.5 py-0.5 rounded text-amber-300">.env</code> file:
        </p>

        <pre className="bg-[#0b0f17] border border-gray-800 rounded-xl p-4 text-xs font-mono text-gray-300 overflow-x-auto">
{`# Privacy Configuration (strict_local | private_hybrid | cloud_assisted)
PRIVACY_MODE=strict_local
ALLOW_CLOUD_TRANSFERS=false

# Google Veo 2 / Gemini
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key_here
VIDEO_PROVIDER=veo
VIDEO_API_KEY=your_veo_api_key_here

# Runway / Luma / Kling / Seedance / Adobe Firefly
# VIDEO_PROVIDER=runway | luma | kling | seedance | firefly
# VIDEO_API_KEY=your_video_key_here

# Local Ollama (100% Offline)
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434

# Audio & Voiceover
AUDIO_PROVIDER=edge_tts
# AUDIO_PROVIDER=elevenlabs
# AUDIO_API_KEY=your_elevenlabs_api_key_here`}
        </pre>
      </div>
    </div>
  );
};
