import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import AudioUpload from './components/AudioUpload';
import ProcessingView from './components/ProcessingView';
import Dashboard from './components/Dashboard';
import SettingsModal from './components/SettingsModal';
import Footer from './components/Footer';
import { fetchHealth, fetchSampleList, analyzeAudioFile, downloadSampleFile } from './utils/api';
import { AlertCircle, X } from 'lucide-react';

const INITIAL_FILLERS = [
  'um', 'uh', 'erm', 'er', 'hmm', 'basically', 'actually',
  'literally', 'you know', 'i mean', 'sort of', 'kind of',
  'like', 'ah', 'honestly', 'right', 'to be honest'
];

export default function App() {
  const [health, setHealth] = useState(null);
  const [samples, setSamples] = useState([]);
  const [customFillers, setCustomFillers] = useState(INITIAL_FILLERS);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const [isProcessing, setIsProcessing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [activeAudioUrl, setActiveAudioUrl] = useState(null);
  const [globalError, setGlobalError] = useState('');

  // Initial load: backend health and sample clips
  useEffect(() => {
    async function loadInitialData() {
      const healthData = await fetchHealth();
      setHealth(healthData);
      if (healthData?.default_fillers && Array.isArray(healthData.default_fillers)) {
        setCustomFillers(healthData.default_fillers);
      }

      const samplesData = await fetchSampleList();
      setSamples(samplesData?.samples || []);
    }
    loadInitialData();
  }, []);

  const handleAnalyze = async (file) => {
    setGlobalError('');
    setIsProcessing(true);

    try {
      // Store preview url
      if (activeAudioUrl) {
        URL.revokeObjectURL(activeAudioUrl);
      }
      const audioUrl = URL.createObjectURL(file);
      setActiveAudioUrl(audioUrl);

      const result = await analyzeAudioFile({
        file,
        customFillers,
      });

      setAnalysisResult(result);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Analysis error:', err);
      setGlobalError(err.message || 'An unexpected error occurred during speech analysis.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    if (activeAudioUrl) {
      URL.revokeObjectURL(activeAudioUrl);
      setActiveAudioUrl(null);
    }
    setAnalysisResult(null);
    setGlobalError('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleQuickSample = async () => {
    if (samples && samples.length > 0) {
      try {
        const file = await downloadSampleFile(samples[0].filename);
        handleAnalyze(file);
      } catch (err) {
        setGlobalError('Failed to load demo recording: ' + err.message);
      }
    } else {
      handleScrollToUpload();
    }
  };

  const handleScrollToUpload = () => {
    const el = document.getElementById('upload-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleFeedbackUpdated = (newFeedback) => {
    if (analysisResult) {
      setAnalysisResult({
        ...analysisResult,
        feedback: newFeedback,
      });
    }
  };

  return (
    <div className="app-container">
      <Navbar
        health={health}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <main className="content-wrapper">
        {globalError && (
          <div style={{
            margin: '24px 0',
            background: 'var(--danger-bg)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
            color: '#FCA5A5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={20} style={{ flexShrink: 0 }} />
              <span style={{ fontSize: '0.95rem' }}>{globalError}</span>
            </div>
            <button
              onClick={() => setGlobalError('')}
              style={{ background: 'transparent', border: 'none', color: '#FCA5A5', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
          </div>
        )}

        {isProcessing ? (
          <ProcessingView />
        ) : analysisResult ? (
          <Dashboard
            result={analysisResult}
            audioUrl={activeAudioUrl}
            onReset={handleReset}
            onFeedbackUpdated={handleFeedbackUpdated}
          />
        ) : (
          <>
            <Hero
              onScrollToUpload={handleScrollToUpload}
              onQuickSample={handleQuickSample}
            />
            <AudioUpload
              onAnalyze={handleAnalyze}
              samples={samples}
              customFillers={customFillers}
            />
          </>
        )}
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        activeFillers={customFillers}
        onSaveFillers={(newFillers) => setCustomFillers(newFillers)}
      />

      <Footer />
    </div>
  );
}
