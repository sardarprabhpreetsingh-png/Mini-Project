import React, { useState } from 'react';
import { X, Plus, RotateCcw, Check, Sliders } from 'lucide-react';

const DEFAULT_FILLERS = [
  'um', 'uh', 'erm', 'er', 'hmm', 'basically', 'actually',
  'literally', 'you know', 'i mean', 'sort of', 'kind of',
  'like', 'ah', 'honestly', 'right', 'to be honest'
];

export default function SettingsModal({
  isOpen,
  onClose,
  activeFillers,
  onSaveFillers,
}) {
  const [fillers, setFillers] = useState([...activeFillers]);
  const [newWord, setNewWord] = useState('');

  if (!isOpen) return null;

  const toggleFiller = (word) => {
    if (fillers.includes(word)) {
      setFillers(fillers.filter((w) => w !== word));
    } else {
      setFillers([...fillers, word]);
    }
  };

  const addCustomFiller = (e) => {
    e.preventDefault();
    const trimmed = newWord.trim().toLowerCase();
    if (trimmed && !fillers.includes(trimmed)) {
      setFillers([...fillers, trimmed]);
      setNewWord('');
    }
  };

  const resetToDefaults = () => {
    setFillers([...DEFAULT_FILLERS]);
  };

  const handleSave = () => {
    onSaveFillers(fillers);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#A5B4FC'
            }}>
              <Sliders size={18} />
            </div>
            <h3 style={{ fontSize: '1.25rem' }}>Configure Filler Words</h3>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            style={{ padding: '6px' }}
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '20px' }}>
          Select which filler words SpeakSense should identify during speech analysis. You can also add your own colloquial phrases.
        </p>

        {/* Add custom filler form */}
        <form onSubmit={addCustomFiller} style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
          <input
            type="text"
            placeholder="Add custom word (e.g., seriously, anyway)"
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            style={{
              flex: 1,
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 14px',
              color: '#FFFFFF',
              fontFamily: 'var(--font-body)',
              fontSize: '0.9rem'
            }}
          />
          <button type="submit" className="btn btn-primary btn-sm" disabled={!newWord.trim()}>
            <Plus size={16} />
            <span>Add</span>
          </button>
        </form>

        {/* Filler chips grid */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          maxHeight: '220px',
          overflowY: 'auto',
          padding: '12px',
          background: 'rgba(0,0,0,0.2)',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '24px'
        }}>
          {fillers.map((word) => (
            <button
              key={word}
              type="button"
              onClick={() => toggleFiller(word)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.82rem',
                border: '1px solid rgba(99, 102, 241, 0.4)',
                background: 'rgba(99, 102, 241, 0.18)',
                color: '#C7D2FE',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <Check size={12} />
              <span>{word}</span>
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={resetToDefaults}
          >
            <RotateCcw size={14} />
            <span>Reset to Defaults</span>
          </button>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
              Cancel
            </button>
            <button type="button" className="btn btn-primary btn-sm" onClick={handleSave}>
              Save Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
