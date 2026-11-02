import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/layout/Navbar';
import { Dashboard } from './pages/Dashboard';
import { CreateVideo } from './pages/CreateVideo';
import { ProjectDetailPage } from './pages/ProjectDetail';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0b0f17] text-gray-100 flex flex-col font-sans">
        <Navbar demoMode={true} />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/create" element={<CreateVideo />} />
            <Route path="/project/:projectId" element={<ProjectDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
        <footer className="border-t border-gray-800/80 py-6 text-center text-xs text-gray-500">
          ClipForge AI — Professional Video Automation Platform &bull; Instagram Reels &amp; YouTube Shorts
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;

