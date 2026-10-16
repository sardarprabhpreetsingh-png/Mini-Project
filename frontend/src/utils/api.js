const API_BASE = 'https://mini-project-0wvr.onrender.com';

/**
 * Checks backend health and config status
 */
export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Health check failed:', err);
    return { status: 'offline', gemini_configured: false };
  }
}

/**
 * Uploads audio file and initiates transcription, analysis, and AI coaching
 */
export async function analyzeAudioFile({ file, customFillers = [] }) {
  const formData = new FormData();
  formData.append('file', file);
  
  if (customFillers && customFillers.length > 0) {
    formData.append('custom_fillers', JSON.stringify(customFillers));
  }

  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to analyze speech recording.');
  }

  return data;
}

/**
 * Fetches bundled sample speech recordings
 */
export async function fetchSampleList() {
  try {
    const res = await fetch(`${API_BASE}/api/samples`);
    if (!res.ok) return { samples: [] };
    return await res.json();
  } catch (err) {
    console.warn('Could not fetch sample list:', err);
    return { samples: [] };
  }
}

/**
 * Downloads a sample audio file as a Blob/File to pass to analyzer
 */
export async function downloadSampleFile(filename) {
  const res = await fetch(`${API_BASE}/api/samples/${filename}`);
  if (!res.ok) throw new Error('Failed to fetch sample audio');
  const blob = await res.blob();
  const ext = '.' + filename.split('.').pop().toLowerCase();
  const mimeMap = {
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.m4a': 'audio/mp4',
    '.aac': 'audio/aac',
    '.ogg': 'audio/ogg',
    '.webm': 'audio/webm',
    '.flac': 'audio/flac',
  };
  const mimeType = blob.type && blob.type !== 'application/octet-stream'
    ? blob.type
    : (mimeMap[ext] || 'audio/mpeg');
  return new File([blob], filename, { type: mimeType });
}

/**
 * Regenerates AI feedback
 */
export async function regenerateAIFeedback(transcript, analysis) {
  const formData = new FormData();
  formData.append('transcript', transcript);
  formData.append('analysis_json', JSON.stringify(analysis));

  const res = await fetch(`${API_BASE}/api/feedback/regenerate`, {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to regenerate feedback.');
  }

  return data.feedback;
}
