import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, Sparkles, AudioWaveform, Calculator, Cpu } from 'lucide-react';

const STEPS = [
  { id: 1, title: 'Audio Upload & Validation', desc: 'Validating format and audio bitrate stream' },
  { id: 2, title: 'Whisper Speech-to-Text Transcription', desc: 'Transcribing speech phonemes and calculating timestamps' },
  { id: 3, title: 'Speech Cadence & Filler Analysis', desc: 'Calculating words per minute, pauses, and repetition' },
  { id: 4, title: 'AI Coaching Synthesis', desc: 'Formulating personalized strengths, weaknesses, and drills' }
];

export default function ProcessingView() {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    // Advance progress indicators smoothly
    const t1 = setTimeout(() => setCurrentStepIndex(1), 800);
    const t2 = setTimeout(() => setCurrentStepIndex(2), 2400);
    const t3 = setTimeout(() => setCurrentStepIndex(3), 4200);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, []);

  return (
    <div className="processing-container">
      <div className="loader-spinner-wrap">
        <div className="loader-circle" />
      </div>

      <h2 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>
        Analyzing Your Speech...
      </h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: '480px', margin: '0 auto' }}>
        Whisper is extracting your transcript while our intelligence engine calculates metrics and generates coaching feedback.
      </p>

      <div className="pipeline-steps-card">
        {STEPS.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isActive = idx === currentStepIndex;
          const isPending = idx > currentStepIndex;

          return (
            <div key={step.id} className="pipeline-step-row">
              <div
                className={`step-status-icon ${
                  isDone ? 'done' : isActive ? 'active' : 'pending'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 size={18} />
                ) : isActive ? (
                  <Loader2 size={18} className="spin-icon" style={{ animation: 'spin 1s linear infinite' }} />
                ) : (
                  <span>{step.id}</span>
                )}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{
                  fontWeight: 600,
                  fontSize: '0.95rem',
                  color: isActive ? '#FFFFFF' : isDone ? '#E2E8F0' : 'var(--text-muted)'
                }}>
                  {step.title}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {step.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
