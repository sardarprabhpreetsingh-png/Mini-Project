import React, { useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ArrowRight,
  RefreshCw,
  Info,
  Dumbbell,
  Quote
} from 'lucide-react';
import { regenerateAIFeedback } from '../utils/api';

export default function FeedbackView({ feedback, transcript, analysis, onFeedbackUpdated }) {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const isAI = feedback?.is_ai_available;
  const modelName = feedback?.model_used || 'SpeakSense Engine';

  const handleRegenerate = async () => {
    setErrorMsg('');
    setIsRegenerating(true);
    try {
      const newFeedback = await regenerateAIFeedback(transcript, analysis);
      if (onFeedbackUpdated) {
        onFeedbackUpdated(newFeedback);
      }
    } catch (err) {
      setErrorMsg('Failed to regenerate feedback: ' + err.message);
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <section className="ai-coach-section">
      <div className="ai-header-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'var(--gradient-brand)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white'
          }}>
            <Sparkles size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem' }}>Personalized AI Coaching Report</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Analyzed using {modelName}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className={`badge ${isAI ? 'badge-success' : 'badge-info'}`}>
            {isAI ? 'Gemini AI Verified' : 'Heuristic Rules Engine'}
          </span>

          <button
            className="btn btn-secondary btn-sm"
            onClick={handleRegenerate}
            disabled={isRegenerating}
            title="Re-run coaching synthesis"
          >
            <RefreshCw size={14} className={isRegenerating ? 'spin-icon' : ''} style={{ animation: isRegenerating ? 'spin 1s linear infinite' : 'none' }} />
            <span>{isRegenerating ? 'Regenerating...' : 'Regenerate'}</span>
          </button>
        </div>
      </div>

      {feedback?.notice && (
        <div style={{
          background: isAI ? 'rgba(99, 102, 241, 0.08)' : 'rgba(59, 130, 246, 0.08)',
          border: `1px solid ${isAI ? 'rgba(99, 102, 241, 0.25)' : 'rgba(59, 130, 246, 0.25)'}`,
          borderRadius: 'var(--radius-sm)',
          padding: '10px 16px',
          fontSize: '0.82rem',
          color: isAI ? '#C7D2FE' : '#93C5FD',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Info size={16} style={{ flexShrink: 0 }} />
            <span>{feedback.notice}</span>
          </div>
          {feedback?.error_details?.suggested_alternatives?.length > 0 && (
            <div style={{ paddingLeft: '24px', fontSize: '0.78rem', opacity: 0.9 }}>
              Supported model alternatives: <strong>{feedback.error_details.suggested_alternatives.join(', ')}</strong>
            </div>
          )}
        </div>
      )}

      {errorMsg && (
        <div style={{
          background: 'var(--danger-bg)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 'var(--radius-sm)',
          padding: '10px 16px',
          color: '#F87171',
          fontSize: '0.85rem',
          marginBottom: '20px'
        }}>
          {errorMsg}
        </div>
      )}

      {/* Executive Summary */}
      <div className="ai-summary-card">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <Quote size={28} style={{ color: 'var(--accent-primary)', flexShrink: 0, opacity: 0.8 }} />
          <div>
            <h4 style={{ fontSize: '1.05rem', color: '#A5B4FC', marginBottom: '6px' }}>
              Executive Coach Summary
            </h4>
            <p style={{ fontSize: '1rem', color: '#F1F5F9', lineHeight: 1.6 }}>
              {feedback?.summary}
            </p>
          </div>
        </div>
      </div>

      {/* Strengths & Weaknesses 2-Col Grid */}
      <div className="ai-two-col">
        {/* Strengths */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background: 'var(--success-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#34D399'
            }}>
              <CheckCircle2 size={16} />
            </div>
            <h4 style={{ fontSize: '1.1rem', color: '#34D399' }}>Key Strengths</h4>
          </div>

          <ul className="feedback-list">
            {(feedback?.strengths || []).map((s, idx) => (
              <li key={idx} className="feedback-item">
                <span className="feedback-item-icon" style={{ color: '#34D399' }}>✓</span>
                <span style={{ color: '#E2E8F0' }}>{s}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Areas for Improvement */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background: 'var(--warning-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FBBF24'
            }}>
              <AlertTriangle size={16} />
            </div>
            <h4 style={{ fontSize: '1.1rem', color: '#FBBF24' }}>Areas to Improve</h4>
          </div>

          <ul className="feedback-list">
            {(feedback?.weaknesses || []).map((w, idx) => (
              <li key={idx} className="feedback-item">
                <span className="feedback-item-icon" style={{ color: '#FBBF24' }}>▲</span>
                <span style={{ color: '#E2E8F0' }}>{w}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Actionable Exercises */}
      {feedback?.actionable_exercises && feedback.actionable_exercises.length > 0 && (
        <div className="glass-card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#A5B4FC'
            }}>
              <Dumbbell size={16} />
            </div>
            <h4 style={{ fontSize: '1.1rem' }}>Personalized Practice Drills</h4>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {feedback.actionable_exercises.map((drill, idx) => (
              <div key={idx} className="exercise-card">
                <div className="exercise-title">
                  <span style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    background: 'rgba(99, 102, 241, 0.25)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    color: '#C7D2FE'
                  }}>
                    {idx + 1}
                  </span>
                  <span>{drill.title}</span>
                </div>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {drill.instruction}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rephrasing Suggestions */}
      {feedback?.rephrasing_suggestions && feedback.rephrasing_suggestions.length > 0 && (
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background: 'rgba(6, 182, 212, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38BDF8'
            }}>
              <Lightbulb size={16} />
            </div>
            <h4 style={{ fontSize: '1.1rem' }}>Impactful Rephrasing Suggestions</h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {feedback.rephrasing_suggestions.map((rep, idx) => (
              <div key={idx} className="rephrase-card">
                <div>
                  <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#F87171', fontWeight: 600, marginBottom: '4px' }}>
                    Spoken Phrase
                  </div>
                  <div className="rephrase-orig">"{rep.original}"</div>
                </div>

                <div>
                  <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#34D399', fontWeight: 600, marginBottom: '4px' }}>
                    Polished Delivery
                  </div>
                  <div className="rephrase-better">"{rep.improved}"</div>
                  {rep.reason && (
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Why: {rep.reason}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
