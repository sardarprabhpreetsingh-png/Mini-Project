import React from 'react';
import { Sparkles, Gauge, MessageSquareText, ShieldAlert, ArrowDown } from 'lucide-react';

export default function Hero({ onScrollToUpload, onQuickSample }) {
  return (
    <section className="hero-section">
      <div className="hero-tag">
        <Sparkles size={14} />
        <span>Next-Generation Speech Intelligence</span>
      </div>

      <h1 className="hero-title">
        Master Your Voice With <span className="gradient-text">AI-Powered</span> Communication Coaching
      </h1>

      <p className="hero-subtitle">
        Upload your speech or record directly in your browser. Get measurable metrics on speaking tempo, filler words, and natural rhythm — paired with personalized, actionable AI feedback powered by Whisper and Gemini.
      </p>

      <div style={{ display: 'flex', gap: '14px', justifyContent: 'center', flexWrap: 'wrap' }}>
        <button className="btn btn-primary btn-lg" onClick={onScrollToUpload}>
          <span>Analyze Speech Now</span>
          <ArrowDown size={18} />
        </button>

        <button className="btn btn-secondary btn-lg" onClick={onQuickSample}>
          <Sparkles size={18} />
          <span>Try Demo Recording</span>
        </button>
      </div>

      <div className="hero-features-bar">
        <div className="hero-feature-item">
          <MessageSquareText size={18} className="hero-feature-icon" />
          <span>Whisper Speech-to-Text</span>
        </div>
        <div className="hero-feature-item">
          <Gauge size={18} className="hero-feature-icon" />
          <span>Words Per Minute (WPM)</span>
        </div>
        <div className="hero-feature-item">
          <ShieldAlert size={18} className="hero-feature-icon" />
          <span>Filler & Repetition Detection</span>
        </div>
        <div className="hero-feature-item">
          <Sparkles size={18} className="hero-feature-icon" />
          <span>Personalized AI Coaching</span>
        </div>
      </div>
    </section>
  );
}
