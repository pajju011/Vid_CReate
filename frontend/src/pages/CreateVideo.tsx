import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Sparkles, Scissors } from 'lucide-react';
import { PromptStudio } from '../features/prompt-video/PromptStudio';
import { ShortsStudio } from '../features/video-to-shorts/ShortsStudio';

export const CreateVideo: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') === 'shorts' ? 'shorts' : 'prompt';
  const [activeTab, setActiveTab] = useState<'prompt' | 'shorts'>(initialTab);

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'shorts' || tab === 'prompt') {
      setActiveTab(tab);
    }
  }, [searchParams]);

  const switchTab = (tab: 'prompt' | 'shorts') => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  return (
    <div className="py-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Segmented Control Tabs */}
      <div className="flex justify-center">
        <div className="inline-flex p-1.5 bg-[#111827] border border-gray-800 rounded-2xl shadow-xl">
          <button
            onClick={() => switchTab('prompt')}
            className={`flex items-center gap-2.5 px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all ${
              activeTab === 'prompt'
                ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Workflow A: Prompt to Video</span>
          </button>

          <button
            onClick={() => switchTab('shorts')}
            className={`flex items-center gap-2.5 px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all ${
              activeTab === 'shorts'
                ? 'bg-gradient-to-r from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-600/30'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Scissors className="w-4 h-4" />
            <span>Workflow B: Video to Shorts</span>
          </button>
        </div>
      </div>

      {/* Render Active Studio */}
      {activeTab === 'prompt' ? <PromptStudio /> : <ShortsStudio />}
    </div>
  );
};

