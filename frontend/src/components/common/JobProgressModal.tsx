import React, { useEffect, useState, useRef } from 'react';
import { Loader2, CheckCircle2, AlertCircle, XCircle, PauseCircle, PlayCircle, ArrowRight } from 'lucide-react';
import { Job } from '../../types';
import { api } from '../../services/api';

interface JobProgressModalProps {
  jobId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (job: Job) => void;
}

export const JobProgressModal: React.FC<JobProgressModalProps> = ({
  jobId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isActionPending, setIsActionPending] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!isOpen || !jobId) return;

    let isMounted = true;
    let pollInterval: NodeJS.Timeout;

    // 1. Initial REST fetch
    const fetchStatus = async () => {
      try {
        const data = await api.getJob(jobId);
        if (!isMounted) return;
        setJob(data);

        if (data.status === 'completed') {
          if (onSuccess) onSuccess(data);
        }
      } catch (err: any) {
        if (isMounted) setError(err.message || 'Failed to poll job status');
      }
    };

    fetchStatus();

    // 2. Establish WebSocket real-time connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/jobs/${jobId}`;
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (isMounted && payload.job_id === jobId) {
            setJob((prev) => ({
              ...(prev || ({} as Job)),
              status: payload.status,
              progress: payload.progress,
              current_step: payload.current_step,
              result_data: payload.result_data || prev?.result_data || {},
              checkpoint_data: payload.checkpoint_data || prev?.checkpoint_data || {},
              error_message: payload.error_message || prev?.error_message,
              updated_at: payload.updated_at || new Date().toISOString()
            }));

            if (payload.status === 'completed' && onSuccess) {
              api.getJob(jobId).then((fullJob) => {
                if (isMounted) onSuccess(fullJob);
              });
            }
          }
        } catch {
          // ignore parsing error
        }
      };

      ws.onerror = () => {
        // Fall back to polling if WebSocket fails
      };
    } catch {
      // Fall back to polling
    }

    // 3. Polling backup (runs every 2 seconds)
    pollInterval = setInterval(fetchStatus, 2000);

    return () => {
      isMounted = false;
      clearInterval(pollInterval);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [jobId, isOpen]);

  const handleCancel = async () => {
    if (!jobId || isActionPending) return;
    setIsActionPending(true);
    try {
      await api.cancelJob(jobId);
      setJob((prev) => prev ? { ...prev, status: 'cancelled', current_step: 'Cancelled by user' } : null);
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionPending(false);
    }
  };

  const handlePause = async () => {
    if (!jobId || isActionPending) return;
    setIsActionPending(true);
    try {
      const updated = await api.pauseJob(jobId);
      setJob(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionPending(false);
    }
  };

  const handleResume = async () => {
    if (!jobId || isActionPending) return;
    setIsActionPending(true);
    try {
      const updated = await api.resumeJob(jobId);
      setJob(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setIsActionPending(false);
    }
  };

  if (!isOpen) return null;

  const isCompleted = job?.status === 'completed';
  const isFailed = job?.status === 'failed';
  const isCancelled = job?.status === 'cancelled';
  const isPaused = job?.status === 'paused';
  const isRunning = job?.status === 'running' || job?.status === 'pending';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md bg-[#111827] border border-gray-800 rounded-2xl shadow-2xl overflow-hidden p-6 text-gray-100">
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2.5">
            {isRunning && <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />}
            {isPaused && <PauseCircle className="w-5 h-5 text-amber-400" />}
            {isCompleted && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
            {isFailed && <AlertCircle className="w-5 h-5 text-rose-500" />}
            {isCancelled && <XCircle className="w-5 h-5 text-gray-500" />}
            <h3 className="font-semibold text-base">
              {isRunning && 'AI Production In Progress'}
              {isPaused && 'Production Paused'}
              {isCompleted && 'Production Complete!'}
              {isFailed && 'Production Failed'}
              {isCancelled && 'Job Cancelled'}
            </h3>
          </div>
          {(isCompleted || isFailed || isCancelled || isPaused) && (
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors text-sm">
              ✕
            </button>
          )}
        </div>

        <div className="py-6 space-y-5">
          {/* Progress bar */}
          <div>
            <div className="flex justify-between text-xs font-mono text-gray-400 mb-2">
              <span className="truncate max-w-[280px]">{job?.current_step || 'Initializing pipeline...'}</span>
              <span className="font-bold text-indigo-400">{job?.progress || 0}%</span>
            </div>
            <div className="w-full h-2.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  isFailed
                    ? 'bg-rose-500'
                    : isCancelled
                    ? 'bg-gray-600'
                    : isPaused
                    ? 'bg-amber-400'
                    : isCompleted
                    ? 'bg-emerald-500'
                    : 'bg-gradient-to-r from-indigo-500 to-emerald-400'
                }`}
                style={{ width: `${job?.progress || 0}%` }}
              />
            </div>
          </div>

          {/* Detailed step information */}
          <div className="bg-[#0b0f17] border border-gray-800/80 rounded-xl p-3.5 space-y-2 text-xs">
            <div className="flex justify-between text-gray-400">
              <span>Job Type:</span>
              <span className="font-mono text-gray-200 capitalize">{job?.job_type?.replace(/_/g, ' ') || 'Generation'}</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Status:</span>
              <span className={`font-mono capitalize font-medium ${
                isCompleted ? 'text-emerald-400' : isPaused ? 'text-amber-400' : isFailed ? 'text-rose-400' : 'text-indigo-400'
              }`}>
                {job?.status}
              </span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Job ID:</span>
              <span className="font-mono text-gray-400">{job?.id?.slice(0, 12)}...</span>
            </div>
            {job?.error_message && (
              <div className="pt-2 border-t border-gray-800 text-rose-400 text-xs">
                <strong>Error:</strong> {job.error_message}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-800">
          {isRunning && (
            <>
              <button
                onClick={handlePause}
                disabled={isActionPending}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-amber-400 hover:bg-amber-400/10 transition-colors"
              >
                <PauseCircle className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
              <button
                onClick={handleCancel}
                disabled={isActionPending}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                Cancel
              </button>
            </>
          )}

          {isPaused && (
            <>
              <button
                onClick={handleResume}
                disabled={isActionPending}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
              >
                <PlayCircle className="w-3.5 h-3.5" />
                <span>Resume from Checkpoint</span>
              </button>
              <button
                onClick={handleCancel}
                disabled={isActionPending}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                Cancel
              </button>
            </>
          )}

          {(isCompleted || isFailed || isCancelled) && (
            <button
              onClick={onClose}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
            >
              <span>{isCompleted ? 'View Final Video' : 'Close'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
