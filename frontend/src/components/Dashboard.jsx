import React from 'react';
import {
  Gauge,
  ShieldAlert,
  Clock,
  Repeat,
  Activity,
  Download,
  RotateCcw,
  Sparkles,
  Volume2,
  BarChart3
} from 'lucide-react';
import MetricCard from './MetricCard';
import TranscriptView from './TranscriptView';
import FeedbackView from './FeedbackView';
import { exportReportAsMarkdown } from '../utils/exportReport';

export default function Dashboard({ result, audioUrl, onReset, onFeedbackUpdated }) {
  if (!result) return null;

  const { filename, transcript, segments, analysis, feedback } = result;
  const { score, pacing, fillers, pauses, repetitions, duration_formatted, word_count } = analysis;

  const handleDownload = () => {
    exportReportAsMarkdown(result);
  };

  const fillerBreakdown = fillers?.breakdown || {};
  const hasFillers = Object.keys(fillerBreakdown).length > 0;
  const maxFillerCount = hasFillers ? Math.max(...Object.values(fillerBreakdown)) : 1;

  const frequentWords = repetitions?.frequent_words || {};
  const hasFrequentWords = Object.keys(frequentWords).length > 0;

  return (
    <div style={{ paddingBottom: '60px' }}>
      {/* Top Score Banner */}
      <div className="score-banner">
        <div className="score-circle-wrap">
          <div
            className="score-radial"
            style={{ '--score-pct': score?.score || 75 }}
          >
            <div className="score-radial-inner">
              <span className="score-num">{score?.score || 75}</span>
              <span className="score-max">/ 100</span>
            </div>
          </div>

          <div className="score-meta">
            <span className={`badge badge-${score?.color || 'success'}`} style={{ marginBottom: '8px' }}>
              {score?.badge || 'Speech Performance'}
            </span>
            <h2>{score?.level || 'Proficient'} Communication</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '420px' }}>
              {feedback?.summary?.slice(0, 110) || 'Objective speech analysis calculated from your audio sample.'}...
            </p>

            <div className="subscores-bar-wrap">
              <div className="subscore-item">
                <span>Pacing:</span>
                <span className="subscore-value">{score?.subscores?.pacing || 25}/30</span>
              </div>
              <div className="subscore-item">
                <span>Fillers:</span>
                <span className="subscore-value">{score?.subscores?.fillers || 25}/30</span>
              </div>
              <div className="subscore-item">
                <span>Flow:</span>
                <span className="subscore-value">{score?.subscores?.flow || 18}/20</span>
              </div>
              <div className="subscore-item">
                <span>Vocabulary:</span>
                <span className="subscore-value">{score?.subscores?.vocabulary || 16}/20</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={handleDownload} title="Export markdown summary">
            <Download size={16} />
            <span>Export Report</span>
          </button>

          <button className="btn btn-primary" onClick={onReset} title="Upload or record a new speech">
            <RotateCcw size={16} />
            <span>Analyze Another</span>
          </button>
        </div>
      </div>

      {/* Audio Playback Bar */}
      {audioUrl && (
        <div className="glass-card" style={{ marginBottom: '28px', padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)' }}>
            <Volume2 size={20} />
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Recording Playback:
            </span>
          </div>
          <div style={{ flex: 1, minWidth: '220px' }}>
            <audio
              controls
              preload="metadata"
              src={audioUrl}
              style={{ width: '100%', filter: 'invert(0.9) hue-rotate(180deg)' }}
              onError={(e) => {
                const err = e.currentTarget?.error;
                console.warn('Dashboard audio playback error:', err);
              }}
            />
          </div>
        </div>
      )}

      {/* Measurable Statistics Grid */}
      <div className="metrics-grid">
        <MetricCard
          title="Speaking Speed"
          value={pacing?.wpm || 0}
          unit="WPM"
          badgeText={pacing?.status || 'Calculated'}
          badgeType={pacing?.status_color || 'info'}
          icon={Gauge}
          description={`Target: ${pacing?.target_range || '130 - 160 WPM'}. ${pacing?.message || ''}`}
          accentColor="#6366F1"
        />

        <MetricCard
          title="Filler Words"
          value={fillers?.total_fillers || 0}
          unit={`(${fillers?.filler_ratio_percent || 0}%)`}
          badgeText={fillers?.rating || 'Checked'}
          badgeType={fillers?.rating_color || 'info'}
          icon={ShieldAlert}
          description={fillers?.message || 'Identified using configured filler dictionary.'}
          accentColor="#F59E0B"
        />

        <MetricCard
          title="Pauses & Cadence"
          value={pauses?.pause_count || 0}
          unit="pauses"
          badgeText={pauses?.flow_rating || 'Measured'}
          badgeType={pauses?.flow_color || 'info'}
          icon={Clock}
          description={`Avg pause: ${pauses?.avg_pause_duration_sec || 0}s (${pauses?.pause_percentage || 0}% of speech). ${pauses?.message || ''}`}
          accentColor="#06B6D4"
        />

        <MetricCard
          title="Speech Volume & Time"
          value={word_count || 0}
          unit="words"
          badgeText={duration_formatted || '0s'}
          badgeType="neutral"
          icon={Activity}
          description={`Total speech span of ${analysis?.duration_seconds || 0} seconds analyzed.`}
          accentColor="#EC4899"
        />

        <MetricCard
          title="Repetitions & Stammers"
          value={repetitions?.consecutive_repeats_count || 0}
          unit="repeats"
          badgeText={repetitions?.consecutive_repeats_count === 0 ? 'Smooth' : 'Hesitations'}
          badgeType={repetitions?.consecutive_repeats_count === 0 ? 'success' : 'warning'}
          icon={Repeat}
          description={`Vocabulary variety: ${Math.round((repetitions?.vocabulary_diversity_ratio || 0.5) * 100)}% unique words.`}
          accentColor="#8B5CF6"
        />
      </div>

      {/* Transcript with Interactive Highlighting */}
      <TranscriptView
        transcript={transcript}
        segments={segments}
        fillers={fillers}
        repetitions={repetitions}
      />

      {/* Breakdown Analytics: Fillers & Overused Words */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Filler Word Distribution */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <BarChart3 size={18} style={{ color: '#FBBF24' }} />
            <h4 style={{ fontSize: '1.05rem' }}>Filler Word Distribution</h4>
          </div>

          {hasFillers ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {Object.entries(fillerBreakdown).map(([word, count]) => {
                const pct = Math.round((count / maxFillerCount) * 100);
                return (
                  <div key={word}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 600, color: '#FDE68A' }}>"{word}"</span>
                      <span style={{ color: 'var(--text-muted)' }}>{count} time{count > 1 ? 's' : ''}</span>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${pct}%`,
                          background: 'linear-gradient(90deg, #F59E0B, #EF4444)',
                          borderRadius: '3px'
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p style={{ fontSize: '0.88rem', color: '#34D399' }}>
              ✓ No filler words detected! Excellent vocal clarity and discipline.
            </p>
          )}
        </div>

        {/* Repetitions & Frequent Content Words */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Repeat size={18} style={{ color: '#A5B4FC' }} />
            <h4 style={{ fontSize: '1.05rem' }}>Frequent Words & Repetitions</h4>
          </div>

          {hasFrequentWords ? (
            <div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Key non-stop words repeated most often:
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {Object.entries(frequentWords).map(([word, count]) => (
                  <span
                    key={word}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.82rem',
                      color: '#E2E8F0',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <span>{word}</span>
                    <span style={{
                      fontSize: '0.7rem',
                      background: 'rgba(99, 102, 241, 0.3)',
                      color: '#C7D2FE',
                      padding: '1px 5px',
                      borderRadius: '4px'
                    }}>
                      ×{count}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Speech clip is short with balanced word distribution.
            </p>
          )}

          {repetitions?.consecutive_repeats_count > 0 && (
            <div style={{ marginTop: '16px', padding: '10px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 'var(--radius-sm)' }}>
              <span style={{ fontSize: '0.8rem', color: '#FCA5A5', fontWeight: 600 }}>
                Stammered word pairs: {Object.keys(repetitions.consecutive_repeats).join(', ')}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Filler Detection Diagnostics & Transcript Inspector Card */}
      <div className="glass-card" style={{ marginBottom: '32px', borderColor: 'rgba(99, 102, 241, 0.25)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={18} style={{ color: 'var(--accent-primary)' }} />
            <h4 style={{ fontSize: '1.05rem' }}>Filler Detection Diagnostics</h4>
          </div>
          <span className="badge badge-info" style={{ fontSize: '0.75rem' }}>
            {fillers?.total_fillers ?? 0} Matched Occurrence{fillers?.total_fillers === 1 ? '' : 's'}
          </span>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.5 }}>
          {fillers?.diagnostics?.detection_rule ||
            "Word-boundary regex match (\\b...\\b) with case-insensitivity. Substrings inside words like 'summer' or 'understand' are intentionally excluded."}
        </p>

        {fillers?.occurrences && fillers.occurrences.length > 0 ? (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Detected Occurrences in Transcript:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {fillers.occurrences.map((occ, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.85rem',
                    gap: '12px',
                    flexWrap: 'wrap'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, color: '#FDE68A', background: 'rgba(245, 158, 11, 0.2)', padding: '2px 8px', borderRadius: '4px' }}>
                      "{occ.word}"
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                      (as {occ.canonical})
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', fontStyle: 'italic' }}>
                    "...{occ.context}..."
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: 'var(--radius-sm)', marginBottom: '16px', fontSize: '0.85rem', color: '#6EE7B7' }}>
            ✓ No matches found in transcript for active filler vocabulary. (If fillers were spoken, check whether Whisper recognized them in the transcript above).
          </div>
        )}

        {fillers?.diagnostics?.unmatched_fillers && fillers.diagnostics.unmatched_fillers.length > 0 && (
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Unmatched Vocabulary Checked ({fillers.diagnostics.unmatched_fillers.length} terms):
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {fillers.diagnostics.unmatched_fillers.map((w) => (
                <span
                  key={w}
                  style={{
                    fontSize: '0.75rem',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    color: 'var(--text-muted)',
                    border: '1px solid rgba(255, 255, 255, 0.05)'
                  }}
                >
                  {w}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* AI Coaching Section */}
      <FeedbackView
        feedback={feedback}
        transcript={transcript}
        analysis={analysis}
        onFeedbackUpdated={onFeedbackUpdated}
      />

      {/* Bottom Practice Again CTA */}
      <div style={{ textAlign: 'center', marginTop: '40px', padding: '30px', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
        <h3 style={{ fontSize: '1.3rem', marginBottom: '8px' }}>
          Ready for your next speaking round?
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '18px' }}>
          Practice makes perfect. Implement the advice above and measure your progress.
        </p>
        <button className="btn btn-primary btn-lg" onClick={onReset}>
          <RotateCcw size={18} />
          <span>Analyze Another Speech Recording</span>
        </button>
      </div>
    </div>
  );
}
