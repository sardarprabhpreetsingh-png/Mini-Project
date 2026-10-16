import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Mic, StopCircle, RefreshCw, Play, Trash2, Sparkles, AlertCircle, FileAudio } from 'lucide-react';
import { downloadSampleFile } from '../utils/api';

const ALLOWED_EXTS = ['.wav', '.mp3', '.m4a', '.aac', '.ogg', '.webm', '.flac'];
const MAX_SIZE_MB = 25;

const MIME_BY_EXT = {
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
  '.m4a': 'audio/mp4',
  '.aac': 'audio/aac',
  '.ogg': 'audio/ogg',
  '.webm': 'audio/webm',
  '.flac': 'audio/flac',
};

function getAudioMimeType(file, ext) {
  if (file.type && file.type !== 'application/octet-stream') {
    return file.type;
  }
  return MIME_BY_EXT[ext] || 'audio/mpeg';
}

function checkBrowserAudioSupport(mimeType, ext) {
  const audio = document.createElement('audio');
  let support = audio.canPlayType(mimeType);
  if (!support && ext === '.m4a') {
    support = audio.canPlayType('audio/mp4; codecs="mp4a.40.2"') || audio.canPlayType('audio/aac') || audio.canPlayType('audio/x-m4a');
  }
  return support === 'probably' || support === 'maybe';
}

export default function AudioUpload({ onAnalyze, samples = [], customFillers = [] }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'record'
  const [audioFile, setAudioFile] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioDuration, setAudioDuration] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [playbackError, setPlaybackError] = useState('');
  const [loadingSample, setLoadingSample] = useState(false);

  // Microphone recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);

  const fileInputRef = useRef(null);
  const audioRef = useRef(null);
  const audioUrlRef = useRef(null);

  const revokeCurrentUrl = () => {
    if (audioUrlRef.current && !audioUrlRef.current.startsWith('/api')) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
  };

  // Clean up object URLs only when component unmounts
  useEffect(() => {
    return () => {
      revokeCurrentUrl();
    };
  }, []);

  // Clean up recording timers/contexts on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    };
  }, []);

  const handleFileSelection = (file) => {
    setErrorMsg('');
    setPlaybackError('');
    if (!file) return;

    if (file.size === 0) {
      setErrorMsg('The selected audio file is empty (0 bytes). Please upload a valid recording.');
      return;
    }

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setErrorMsg(`Unsupported file type '${ext}'. Please upload an audio file (${ALLOWED_EXTS.join(', ')}).`);
      return;
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setErrorMsg(`File exceeds ${MAX_SIZE_MB}MB size limit.`);
      return;
    }

    // Revoke previous object URL if any
    revokeCurrentUrl();

    // Ensure blob has a valid audio MIME type so browser can decode it
    const determinedType = getAudioMimeType(file, ext);
    let playableBlob = file;
    if (!file.type || file.type === 'application/octet-stream' || file.type === 'audio/x-m4a' || file.type === 'audio/m4a') {
      playableBlob = new Blob([file], { type: determinedType });
    }

    const newUrl = URL.createObjectURL(playableBlob);
    audioUrlRef.current = newUrl;
    setAudioFile(file);
    setAudioUrl(newUrl);
    setAudioDuration(null);

    // Codec compatibility check
    if (!checkBrowserAudioSupport(determinedType, ext)) {
      setPlaybackError(
        `Note: Your browser does not support ${ext.slice(1).toUpperCase()} playback. You can still analyze this file with AI below, or use WAV/MP3 or open SpeakSense in Google Chrome or Safari.`
      );
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  // Microphone recording methods
  const startRecording = async () => {
    setErrorMsg('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      // Setup audio analyzer for waveform visualizer
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const recordedFile = new File([audioBlob], `mic_recording_${Date.now()}.webm`, {
          type: 'audio/webm',
        });
        handleFileSelection(recordedFile);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start(200);
      setIsRecording(true);
      setRecordingSeconds(0);

      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);

      // Start waveform rendering
      renderWaveform();
    } catch (err) {
      console.error(err);
      setErrorMsg('Microphone access denied or not available. Please allow microphone permissions or upload an audio file.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    }
  };

  const renderWaveform = () => {
    if (!canvasRef.current || !analyserRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = (canvas.width / bufferLength) * 1.8;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;
        ctx.fillStyle = `rgb(${99 + barHeight * 1.5}, ${102}, ${241})`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 2;
      }
    };
    draw();
  };

  const clearAudio = () => {
    revokeCurrentUrl();
    setAudioFile(null);
    setAudioUrl(null);
    setAudioDuration(null);
    setPlaybackError('');
    setErrorMsg('');
  };

  const handleLoadedMetadata = (e) => {
    const dur = e.currentTarget?.duration;
    if (Number.isFinite(dur) && dur > 0) {
      setAudioDuration(dur);
      setPlaybackError('');
    }
  };

  const handleCanPlay = () => {
    setPlaybackError('');
  };

  const handleAudioError = (e) => {
    const err = e.currentTarget?.error;
    console.warn('Audio playback error:', err);
    const ext = audioFile?.name ? '.' + audioFile.name.split('.').pop().toLowerCase() : '';
    let msg = 'Failed to load audio for preview.';
    if (err) {
      switch (err.code) {
        case 1:
          msg = 'Audio playback was aborted.';
          break;
        case 2:
          msg = 'Network error occurred while loading audio.';
          break;
        case 3:
          msg = 'Audio decoding failed. The file may be corrupt or encoded with an unsupported codec.';
          break;
        case 4:
          msg = `Your browser cannot decode ${ext ? ext.slice(1).toUpperCase() : 'this'} audio format. Try WAV or MP3, or open SpeakSense in Google Chrome or Safari.`;
          break;
        default:
          msg = `Audio preview error (${err.message || 'unknown'}).`;
      }
    }
    setPlaybackError(msg);
  };

  const handleAudioPlay = (e) => {
    const playPromise = e.currentTarget?.play?.();
    if (playPromise !== undefined) {
      playPromise.catch((err) => {
        if (err.name !== 'AbortError') {
          console.warn('Audio play failure:', err);
          setPlaybackError(err.message || 'Browser prevented audio playback.');
        }
      });
    }
  };

  const handleSampleClick = async (filename) => {
    setErrorMsg('');
    setPlaybackError('');
    setLoadingSample(true);
    try {
      const file = await downloadSampleFile(filename);
      handleFileSelection(file);
    } catch (err) {
      setErrorMsg('Failed to load sample clip: ' + err.message);
    } finally {
      setLoadingSample(false);
    }
  };

  const formatTimer = (sec) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const mb = bytes / (1024 * 1024);
    return mb >= 1 ? `${mb.toFixed(2)} MB` : `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <div className="upload-container" id="upload-section">
      <div className="glass-card">
        {/* Dual Tab Switcher */}
        <div className="tabs-header">
          <button
            className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <UploadCloud size={18} />
            <span>Upload Audio File</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'record' ? 'active' : ''}`}
            onClick={() => setActiveTab('record')}
          >
            <Mic size={18} />
            <span>Record with Microphone</span>
          </button>
        </div>

        {errorMsg && (
          <div style={{
            background: 'var(--danger-bg)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            color: '#FCA5A5',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '16px'
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Tab 1: Upload */}
        {activeTab === 'upload' && (
          <div
            className={`dropzone ${dragOver ? 'dragover' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept={ALLOWED_EXTS.join(',')}
              onClick={(e) => { e.target.value = null; }}
              onChange={(e) => {
                if (e.target.files?.[0]) handleFileSelection(e.target.files[0]);
              }}
            />
            <div className="dropzone-icon">
              <UploadCloud size={32} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>
              Drag & drop your speech recording
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '14px' }}>
              Supports WAV, MP3, M4A, AAC, OGG, WEBM (Max {MAX_SIZE_MB}MB)
            </p>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
            >
              Browse Files
            </button>
          </div>
        )}

        {/* Tab 2: Microphone Recorder */}
        {activeTab === 'record' && (
          <div className="recorder-view">
            {!isRecording ? (
              <div>
                <button
                  type="button"
                  className="mic-pulse-btn"
                  onClick={startRecording}
                  title="Click to start recording"
                >
                  <Mic size={36} />
                </button>
                <div style={{ marginTop: '16px' }}>
                  <h3 style={{ fontSize: '1.15rem' }}>Click to Record Speech</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    Speak naturally into your microphone for 10-60 seconds
                  </p>
                </div>
              </div>
            ) : (
              <div>
                <button
                  type="button"
                  className="mic-pulse-btn recording"
                  onClick={stopRecording}
                  title="Click to stop recording"
                >
                  <StopCircle size={36} />
                </button>
                <div className="rec-timer">{formatTimer(recordingSeconds)}</div>
                <p style={{ color: '#F87171', fontSize: '0.85rem', fontWeight: 600 }}>
                  Recording in progress... Click stop when finished.
                </p>
                <canvas
                  ref={canvasRef}
                  width="280"
                  height="45"
                  style={{ marginTop: '16px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)' }}
                />
              </div>
            )}
          </div>
        )}

        {/* Audio Player Preview */}
        {audioFile && audioUrl && (
          <div className="audio-preview-box">
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(99, 102, 241, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#A5B4FC'
            }}>
              <FileAudio size={22} />
            </div>

            <div className="audio-preview-info">
              <div className="audio-filename">{audioFile.name}</div>
              <div className="audio-filesize">
                {formatBytes(audioFile.size)}
                {audioDuration && Number.isFinite(audioDuration) ? ` • ${formatTimer(Math.round(audioDuration))}` : ''}
              </div>
              <audio
                ref={audioRef}
                key={audioUrl}
                controls
                preload="metadata"
                src={audioUrl}
                className="custom-audio-elem"
                onLoadedMetadata={handleLoadedMetadata}
                onCanPlay={handleCanPlay}
                onError={handleAudioError}
                onPlay={handleAudioPlay}
              />
              {playbackError && (
                <div style={{
                  marginTop: '8px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '8px 12px',
                  color: '#FCA5A5',
                  fontSize: '0.82rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <AlertCircle size={16} style={{ flexShrink: 0 }} />
                  <span>{playbackError}</span>
                </div>
              )}
            </div>

            <button
              className="btn btn-secondary btn-sm"
              onClick={clearAudio}
              title="Remove audio"
              style={{ color: '#F87171' }}
            >
              <Trash2 size={16} />
            </button>
          </div>
        )}

        {/* 1-Click Sample Audio Test Bar */}
        <div className="samples-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <Sparkles size={16} style={{ color: 'var(--accent-primary)' }} />
            <span>Quick Test Samples:</span>
          </div>

          <div className="sample-pills-wrap">
            {samples && samples.length > 0 ? (
              samples.map((s) => (
                <button
                  key={s.id}
                  className="sample-pill"
                  disabled={loadingSample || isRecording}
                  onClick={() => handleSampleClick(s.filename)}
                  title={`Test with ${s.title}`}
                >
                  <Play size={12} fill="currentColor" />
                  <span>{s.title}</span>
                </button>
              ))
            ) : (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Sample clips loading...
              </span>
            )}
          </div>
        </div>

        {/* Big Action Submit Button */}
        <div style={{ marginTop: '24px', textAlign: 'center' }}>
          <button
            className="btn btn-primary btn-lg"
            style={{ width: '100%', maxWidth: '420px' }}
            disabled={!audioFile || isRecording}
            onClick={() => onAnalyze(audioFile)}
          >
            <Sparkles size={20} />
            <span>Analyze Speech with AI</span>
          </button>
        </div>
      </div>
    </div>
  );
}
