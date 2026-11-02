import React from 'react';
import { StructuredScenePlan } from '../../types';
import { Clock, Eye, MessageSquare, Subtitles, Trash2, Sparkles, RefreshCw } from 'lucide-react';

interface StoryboardEditorProps {
  scenes: StructuredScenePlan[];
  onUpdateScene: (index: number, updated: Partial<StructuredScenePlan>) => void;
  onDeleteScene: (index: number) => void;
  onAddScene: () => void;
}

export const StoryboardEditor: React.FC<StoryboardEditorProps> = ({
  scenes,
  onUpdateScene,
  onDeleteScene,
  onAddScene,
}) => {
  const getPurposeBadge = (purpose: string) => {
    switch (purpose.toLowerCase()) {
      case 'hook':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'call_to_action':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'problem':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      default:
        return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-gray-100 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Storyboard &amp; Scene Breakdown
          </h3>
          <p className="text-xs text-gray-400">
            Fine-tune prompts, voiceovers, and durations for each scene before final render.
          </p>
        </div>
        <button
          type="button"
          onClick={onAddScene}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-colors"
        >
          + Add Scene
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {scenes.map((scene, idx) => (
          <div
            key={idx}
            className="bg-[#111827] border border-gray-800 rounded-xl p-4 space-y-3 relative group hover:border-gray-700 transition-colors shadow-lg"
          >
            {/* Header row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-indigo-600/30 text-indigo-400 flex items-center justify-center font-bold text-xs border border-indigo-500/30">
                  {scene.scene_number}
                </span>
                <span
                  className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${getPurposeBadge(
                    scene.purpose
                  )}`}
                >
                  {scene.purpose.replace(/_/g, ' ')}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 text-xs text-gray-400 bg-gray-900 px-2 py-1 rounded border border-gray-800">
                  <Clock className="w-3.5 h-3.5 text-gray-400" />
                  <input
                    type="number"
                    min="1"
                    max="30"
                    step="0.5"
                    value={scene.duration_seconds}
                    onChange={(e) =>
                      onUpdateScene(idx, { duration_seconds: parseFloat(e.target.value) || 1 })
                    }
                    className="w-10 bg-transparent text-gray-200 font-mono text-center focus:outline-none focus:text-white"
                  />
                  <span>s</span>
                </div>

                {scenes.length > 1 && (
                  <button
                    type="button"
                    onClick={() => onDeleteScene(idx)}
                    className="p-1 text-gray-500 hover:text-rose-400 transition-colors"
                    title="Delete Scene"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {/* Visual Prompt Input */}
            <div>
              <label className="flex items-center gap-1.5 text-xs font-medium text-gray-300 mb-1">
                <Eye className="w-3.5 h-3.5 text-indigo-400" />
                Visual Prompt
              </label>
              <textarea
                rows={2}
                value={scene.visual_prompt}
                onChange={(e) => onUpdateScene(idx, { visual_prompt: e.target.value })}
                className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg p-2.5 text-gray-200 focus:border-indigo-500 focus:outline-none"
                placeholder="Visual direction for scene generator..."
              />
            </div>

            {/* Narration voiceover input */}
            <div>
              <label className="flex items-center gap-1.5 text-xs font-medium text-gray-300 mb-1">
                <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                Voiceover Narration
              </label>
              <input
                type="text"
                value={scene.narration || ''}
                onChange={(e) => onUpdateScene(idx, { narration: e.target.value })}
                className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg px-2.5 py-1.5 text-gray-200 focus:border-indigo-500 focus:outline-none"
                placeholder="Spoken voiceover text..."
              />
            </div>

            {/* Overlay Caption Input */}
            <div>
              <label className="flex items-center gap-1.5 text-xs font-medium text-gray-300 mb-1">
                <Subtitles className="w-3.5 h-3.5 text-amber-400" />
                Burned Caption / Hook Text
              </label>
              <input
                type="text"
                value={scene.caption || ''}
                onChange={(e) => onUpdateScene(idx, { caption: e.target.value })}
                className="w-full text-xs bg-[#0b0f17] border border-gray-800 rounded-lg px-2.5 py-1.5 text-yellow-300 font-bold uppercase tracking-wider focus:border-indigo-500 focus:outline-none"
                placeholder="OVERLAY CAPTION TEXT"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

