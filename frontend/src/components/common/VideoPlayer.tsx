import React, { useRef, useState } from 'react';
import { Play, Pause, Volume2, VolumeX, Download, Maximize2 } from 'lucide-react';

interface VideoPlayerProps {
  src: string;
  poster?: string;
  aspectRatio?: '9:16' | '16:9' | '1:1';
  title?: string;
  downloadUrl?: string;
  className?: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  src,
  poster,
  aspectRatio = '9:16',
  title,
  downloadUrl,
  className = '',
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState('0:00');
  const [duration, setDuration] = useState('0:00');

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const cur = videoRef.current.currentTime;
    const dur = videoRef.current.duration || 1;
    setProgress((cur / dur) * 100);

    const curMin = Math.floor(cur / 60);
    const curSec = Math.floor(cur % 60);
    setCurrentTime(`${curMin}:${curSec < 10 ? '0' : ''}${curSec}`);
  };

  const handleLoadedMetadata = () => {
    if (!videoRef.current) return;
    const dur = videoRef.current.duration;
    const durMin = Math.floor(dur / 60);
    const durSec = Math.floor(dur % 60);
    setDuration(`${durMin}:${durSec < 10 ? '0' : ''}${durSec}`);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!videoRef.current) return;
    const seekTime = (parseFloat(e.target.value) / 100) * (videoRef.current.duration || 0);
    videoRef.current.currentTime = seekTime;
    setProgress(parseFloat(e.target.value));
  };

  const toggleFullscreen = () => {
    if (!videoRef.current) return;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      videoRef.current.requestFullscreen();
    }
  };

  const getAspectClass = () => {
    if (aspectRatio === '9:16') return 'aspect-[9/16] max-w-[340px]';
    if (aspectRatio === '1:1') return 'aspect-square max-w-[480px]';
    return 'aspect-video w-full';
  };

  return (
    <div className={`relative flex flex-col items-center mx-auto ${className}`}>
      <div className={`relative overflow-hidden rounded-2xl bg-black border border-gray-800 shadow-2xl group w-full ${getAspectClass()}`}>
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          playsInline
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={() => setIsPlaying(false)}
          onClick={togglePlay}
          className="w-full h-full object-cover cursor-pointer"
        />

        {/* Center play icon overlay when paused */}
        {!isPlaying && (
          <div
            onClick={togglePlay}
            className="absolute inset-0 bg-black/30 backdrop-blur-[2px] flex items-center justify-center cursor-pointer transition-opacity"
          >
            <div className="w-16 h-16 rounded-full bg-indigo-600/90 text-white flex items-center justify-center shadow-xl shadow-indigo-600/40 hover:scale-110 transition-transform">
              <Play className="w-8 h-8 ml-1" />
            </div>
          </div>
        )}

        {/* Bottom controls bar */}
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity">
          {/* Progress bar */}
          <input
            type="range"
            min="0"
            max="100"
            value={progress}
            onChange={handleSeek}
            className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500 mb-2"
          />

          <div className="flex items-center justify-between text-white text-xs">
            <div className="flex items-center gap-3">
              <button onClick={togglePlay} className="hover:text-indigo-400 transition-colors">
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
              <button onClick={toggleMute} className="hover:text-indigo-400 transition-colors">
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </button>
              <span className="font-mono text-[11px] text-gray-300">
                {currentTime} / {duration}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {downloadUrl && (
                <a
                  href={downloadUrl}
                  download
                  className="p-1 hover:text-indigo-400 transition-colors"
                  title="Download MP4"
                >
                  <Download className="w-4 h-4" />
                </a>
              )}
              <button onClick={toggleFullscreen} className="p-1 hover:text-indigo-400 transition-colors">
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {title && (
        <div className="mt-3 text-center">
          <p className="text-sm font-medium text-gray-200">{title}</p>
        </div>
      )}
    </div>
  );
};

