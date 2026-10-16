import React from 'react';
import { Mic, Heart, Code2 } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="content-wrapper">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
          <Mic size={18} style={{ color: 'var(--accent-primary)' }} />
          <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '1rem' }}>
            SpeakSense
          </span>
          <span style={{ color: 'var(--text-muted)' }}>— AI-Powered Communication Coaching</span>
        </div>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '600px', margin: '0 auto 12px' }}>
          An end-to-end speech intelligence platform built for measurable communication assessment and generative AI coaching.
        </p>

        <div className="footer-badges">
          <span className="badge badge-neutral">React 18 + Vite</span>
          <span className="badge badge-neutral">FastAPI + Python</span>
          <span className="badge badge-neutral">OpenAI Whisper STT</span>
          <span className="badge badge-neutral">Google Gemini API</span>
          <span className="badge badge-neutral">Vanilla CSS Design System</span>
        </div>

        <div style={{ marginTop: '20px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          College Mini Project • Academic Demo & Speech Evaluation Tool
        </div>
      </div>
    </footer>
  );
}
