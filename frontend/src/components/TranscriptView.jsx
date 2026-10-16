import React, { useState, useMemo } from 'react';
import { Copy, Check, MessageSquare } from 'lucide-react';

export default function TranscriptView({ transcript, segments = [], fillers = {}, repetitions = {} }) {
  const [highlightFillers, setHighlightFillers] = useState(true);
  const [highlightRepeats, setHighlightRepeats] = useState(true);
  const [viewMode, setViewMode] = useState('full'); // 'full' | 'segments'
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(transcript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const detectedFillerTerms = useMemo(() => {
    return Object.keys(fillers?.breakdown || {}).sort((a, b) => b.length - a.length);
  }, [fillers]);

  const repeatedWords = useMemo(() => {
    return new Set(
      Object.keys(repetitions?.consecutive_repeats || {}).map((w) => w.toLowerCase())
    );
  }, [repetitions]);

  // Regex pattern for matching all detected fillers (handles both single-word and multi-word phrases)
  const fillerRegex = useMemo(() => {
    if (!detectedFillerTerms || detectedFillerTerms.length === 0) return null;
    const escaped = detectedFillerTerms.map((t) =>
      t.split(/\s+/).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('\\s+')
    );
    return new RegExp(`\\b(${escaped.join('|')})\\b`, 'gi');
  }, [detectedFillerTerms]);

  // Robust highlighting supporting multi-word phrases (e.g. "you know") and single words
  const renderHighlightedText = (text) => {
    if (!text) return null;
    if (!highlightFillers && !highlightRepeats) return text;

    if (!highlightFillers || !fillerRegex) {
      if (!highlightRepeats) return text;
      // Only highlight repetitions
      const tokens = text.split(/(\s+|[.,!?;:()]+)/);
      return tokens.map((token, i) => {
        const clean = token.trim().toLowerCase();
        if (clean && repeatedWords.has(clean)) {
          return (
            <span key={i} className="highlight-repeat" title="Consecutive Repeated Word">
              {token}
            </span>
          );
        }
        return <span key={i}>{token}</span>;
      });
    }

    // Split text by the combined filler regex while keeping capturing delimiters
    const parts = text.split(fillerRegex);

    return parts.map((part, index) => {
      const lowerPart = part.trim().toLowerCase();
      const isFillerMatch = detectedFillerTerms.some(
        (f) => f.toLowerCase() === lowerPart
      );

      if (isFillerMatch) {
        return (
          <span
            key={index}
            className="highlight-filler"
            title={`Detected Filler Word: "${part}"`}
          >
            {part}
          </span>
        );
      }

      // Inside regular text, check for repeated words if enabled
      if (highlightRepeats && part.trim()) {
        const tokens = part.split(/(\s+|[.,!?;:()]+)/);
        return (
          <span key={index}>
            {tokens.map((token, subIdx) => {
              const clean = token.trim().toLowerCase();
              if (clean && repeatedWords.has(clean)) {
                return (
                  <span
                    key={subIdx}
                    className="highlight-repeat"
                    title="Consecutive Repeated Word"
                  >
                    {token}
                  </span>
                );
              }
              return <span key={subIdx}>{token}</span>;
            })}
          </span>
        );
      }

      return <span key={index}>{part}</span>;
    });
  };

  const formatTimestamp = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  return (
    <div className="glass-card transcript-card">
      <div className="transcript-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'rgba(99, 102, 241, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#A5B4FC'
          }}>
            <MessageSquare size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.15rem' }}>Speech Transcript</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Transcribed with OpenAI Whisper
            </span>
          </div>
        </div>

        <div className="transcript-controls">
          <button
            className={`toggle-chip ${highlightFillers ? 'active-filler' : ''}`}
            onClick={() => setHighlightFillers(!highlightFillers)}
            title="Toggle highlighting of detected filler words and multi-word phrases"
          >
            ● Filler Words ({fillers?.total_fillers ?? 0})
          </button>

          <button
            className={`toggle-chip ${highlightRepeats ? 'active-repeat' : ''}`}
            onClick={() => setHighlightRepeats(!highlightRepeats)}
            title="Toggle highlighting of repeated words"
          >
            ● Repetitions ({repetitions?.consecutive_repeats_count ?? 0})
          </button>

          <div style={{ display: 'flex', background: 'rgba(255,255,255,0.06)', borderRadius: 'var(--radius-sm)', padding: '2px' }}>
            <button
              className={`btn btn-sm ${viewMode === 'full' ? 'btn-secondary' : ''}`}
              style={{ padding: '4px 10px', fontSize: '0.75rem', background: viewMode === 'full' ? 'var(--bg-elevated)' : 'transparent' }}
              onClick={() => setViewMode('full')}
            >
              Full
            </button>
            <button
              className={`btn btn-sm ${viewMode === 'segments' ? 'btn-secondary' : ''}`}
              style={{ padding: '4px 10px', fontSize: '0.75rem', background: viewMode === 'segments' ? 'var(--bg-elevated)' : 'transparent' }}
              onClick={() => setViewMode('segments')}
            >
              Timestamps
            </button>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            onClick={copyToClipboard}
            title="Copy transcript text to clipboard"
          >
            {copied ? <Check size={14} style={{ color: '#34D399' }} /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {viewMode === 'full' ? (
        <div className="transcript-body">
          {renderHighlightedText(transcript)}
        </div>
      ) : (
        <div className="transcript-body" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {segments && segments.length > 0 ? (
            segments.map((seg) => (
              <div key={seg.id} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  padding: '2px 6px',
                  background: 'rgba(255,255,255,0.06)',
                  borderRadius: '4px',
                  color: '#A5B4FC',
                  flexShrink: 0
                }}>
                  {formatTimestamp(seg.start)} - {formatTimestamp(seg.end)}
                </span>
                <span style={{ fontSize: '0.95rem', color: '#E2E8F0' }}>
                  {renderHighlightedText(seg.text)}
                </span>
              </div>
            ))
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No segment timestamps available.</p>
          )}
        </div>
      )}
    </div>
  );
}
