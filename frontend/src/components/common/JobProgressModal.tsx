import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, AlertCircle, XCircle, ArrowRight } from 'lucide-react';
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

  useEffect(() => {
    if (!isOpen || !jobId) return;

    let isMounted = true;
    let pollInterval: NodeJS.Timeout;

    const fetchStatus = async () => {
      try {
        const data = await api.getJob(jobId);
        if (!isMounted) return;
        setJob(data);

        if (data.status === 'completed') {
          clearInterval(pollInterval);
          if (onSuccess) onSuccess(data);
        } else if (data.status === 'failed' || data.status === 'cancelled') {
          clearInterval(pollInterval);
        }
      } catch (err: any) {
        if (isMounted) setError(err.message || 'Failed to poll job status');
      }
    };

    fetchStatus();
    pollInterval = setInterval(fetchStatus, 1500);

    return () => {
      isMounted = false;
      clearInterval(pollInterval);
    };
  }, [jobId, isOpen]);

  const handleCancel = async () => {
    if (!jobId) return;
    try {
      await api.cancelJob(jobId);
    } catch (err) {
      console.error(err);
    }
  };

  if (!isOpen) return null;

  const isCompleted = job?.status === 'completed';
  const isFailed = job?.status === 'failed';
  const isCancelled = job?.status === 'cancelled';
  const isRunning = job?.status === 'running' || job?.status === 'pending';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md bg-[#111827] border border-gray-800 rounded-2xl shadow-2xl overflow-hidden p-6 text-gray-100">
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2.5">
            {isRunning && <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />}
            {isCompleted && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
            {isFailed && <AlertCircle className="w-5 h-5 text-rose-500" />}
            {isCancelled && <XCircle className="w-5 h-5 text-amber-500" />}
            <h3 className="font-semibold text-base">
              {isRunning && 'AI Production In Progress'}
              {isCompleted && 'Production Complete!'}
              {isFailed && 'Production Failed'}
              {isCancelled && 'Job Cancelled'}
            </h3>
          </div>
          {(isCompleted || isFailed || isCancelled) && (
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors text-sm">
              ✕
            </button>
          )}
        </div>

        <div className="py-6 space-y-5">
          {/* Progress bar */}
          <div>
            <div className="flex justify-between text-xs font-mono text-gray-400 mb-2">
              <span>{job?.current_step || 'Initializing pipeline...'}</span>
              <span className="font-bold text-indigo-400">{job?.progress || 0}%</span>
            </div>
            <div className="w-full h-2.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  isFailed
                    ? 'bg-rose-500'
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
              <span className="font-mono text-gray-200 capitalize">{job?.job_type.replace(/_/g, ' ')}</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Job ID:</span>
              <span className="font-mono text-gray-400">{job?.id.slice(0, 12)}...</span>
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
            <button
              onClick={handleCancel}
              className="px-4 py-2 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            >
              Cancel Job
            </button>
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

