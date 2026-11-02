import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Video, Sparkles, Scissors, Settings, Film } from 'lucide-react';

interface NavbarProps {
  demoMode?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ demoMode = true }) => {
  const location = useLocation();

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: Film },
    { to: '/create', label: 'Create Studio', icon: Sparkles },
    { to: '/settings', label: 'Providers & Setup', icon: Settings },
  ];

  return (
    <header className="border-b border-gray-800 bg-[#0d121f]/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-emerald-400 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-[#0b0f17] rounded-[10px] flex items-center justify-center group-hover:bg-transparent transition-colors">
              <Video className="w-5 h-5 text-indigo-400 group-hover:text-white transition-colors" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-gray-100 to-gray-400 bg-clip-text text-transparent">
                ClipForge
              </span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-medium">
                AI
              </span>
            </div>
            <p className="text-[10px] text-gray-400 -mt-0.5">Prompt-to-Video &amp; Shorts Automation</p>
          </div>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-3">
          {demoMode && (
            <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Local Engine Ready
            </span>
          )}
          <Link
            to="/create"
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-md shadow-indigo-600/25 hover:from-indigo-500 hover:to-indigo-400 transition-all active:scale-[0.98]"
          >
            <Sparkles className="w-4 h-4" />
            <span>New Video</span>
          </Link>
        </div>
      </div>
    </header>
  );
};

