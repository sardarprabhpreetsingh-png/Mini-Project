import React from 'react';
import { Mic, Activity, Sliders, Sparkles } from 'lucide-react';

export default function Navbar({ health, onOpenSettings, onSelectSample }) {
  const isOnline = health?.status === 'online';
  const hasGemini = health?.gemini_configured;

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <a href="/" className="brand-logo" onClick={(e) => { e.preventDefault(); window.location.reload(); }}>
          <div className="logo-icon-wrap">
            <Mic size={22} />
          </div>
          <div>
            <span className="brand-name">SpeakSense</span>
            <span className="brand-badge">AI COACH</span>
          </div>
        </a>

        <div className="nav-actions">
          <div className="api-status-pill" title={isOnline ? (hasGemini ? `Gemini AI (${health?.gemini_model || 'Active'}) & Whisper Ready` : "Whisper Ready (Heuristic Engine Active)") : "Backend Offline"}>
            <span className={`status-dot ${isOnline ? '' : 'offline'}`} />
            <span>
              {!isOnline
                ? 'Backend Offline'
                : hasGemini
                ? (health?.gemini_model ? `Gemini (${health.gemini_model})` : 'Gemini AI Active')
                : 'Whisper STT Ready'}
            </span>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            onClick={onOpenSettings}
            title="Configure filler words and speech targets"
          >
            <Sliders size={15} />
            <span>Filler Settings</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
