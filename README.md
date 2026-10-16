# SpeakSense — AI-Powered Communication Coaching

An intelligent speech analysis and AI coaching platform that turns spoken audio into measurable communication metrics and personalized coaching feedback.

---

## 🌟 Overview

**SpeakSense** helps speakers, students, and professionals elevate their verbal delivery. Upload an audio recording or record directly in your browser to receive:

1. **Automated Speech-to-Text Transcription** using OpenAI Whisper with segment timestamps.
2. **Measurable Speech Analytics**:
   - **Speaking Pace (WPM)**: Words Per Minute calculated against optimal benchmarks (130–160 WPM).
   - **Filler Word Detection**: Configurable count and density analysis (e.g., *um*, *uh*, *basically*, *actually*, *you know*).
   - **Repetition & Stammer Analysis**: Consecutive repeated words and overused content vocabulary.
   - **Pause & Cadence Estimation**: Silent intervals and conversational rhythm derived from Whisper audio segments.
   - **Composite Performance Score**: 0–100 communication score with pacing, filler, flow, and vocabulary subscores.
3. **Personalized AI Coaching**: Generative feedback powered by Google Gemini API covering delivery, clarity, strengths, areas for improvement, and actionable practice drills (with automatic heuristic engine fallback if an API key is not supplied).
4. **Interactive Dashboard**: Full transcript with filler word highlighting, audio playback preview, metrics grid, and downloadable markdown reports.

---

## 🛠️ Tech Stack

- **Frontend**: React 18, Vite 5, Vanilla CSS (rich dark glassmorphic design system with modern typography and animations), Lucide React Icons.
- **Backend**: Python 3.9+, FastAPI, Uvicorn, Python-Multipart.
- **Speech-to-Text**: OpenAI Whisper (cached `tiny` model for fast local inference) + `imageio-ffmpeg` for seamless bundled FFmpeg binary execution on macOS/Linux/Windows.
- **AI Coaching**: Google Gemini API via official `google-genai` SDK + SpeakSense heuristic rule-based fallback engine.

---

## 📂 Project Architecture

```
Mini-Project/
├── backend/
│   ├── main.py                 # FastAPI application, CORS, endpoints
│   ├── config.py               # App configuration, settings, env variables
│   ├── requirements.txt        # Python backend dependencies
│   ├── services/
│   │   ├── transcriber.py      # Whisper STT & segment extraction
│   │   ├── analyzer.py         # WPM, fillers, repetitions, pauses & scoring
│   │   └── ai_coach.py         # Gemini API coach & heuristic fallback engine
│   ├── utils/
│   │   └── audio.py            # Audio validation, temp file streaming & cleanup
│   └── samples/                # Bundled speech audio clips for 1-click demos
│       ├── pitch_presentation.mp3
│       └── crisp_keynote.mp3
├── frontend/
│   ├── index.html              # HTML shell with Google Fonts
│   ├── package.json            # Frontend dependencies
│   ├── vite.config.js          # Vite config with backend proxy (/api -> :8000)
│   └── src/
│       ├── main.jsx            # React root
│       ├── App.jsx             # Master app controller & state
│       ├── index.css           # Vanilla CSS design system
│       ├── components/
│       │   ├── Navbar.jsx      # Navigation & live backend health status
│       │   ├── Hero.jsx        # Project introduction & CTA
│       │   ├── AudioUpload.jsx # Dual-tab uploader + live microphone recorder
│       │   ├── ProcessingView.jsx # Multi-step pipeline animation
│       │   ├── Dashboard.jsx   # Results view with score gauge & metrics
│       │   ├── MetricCard.jsx  # Measurable statistics card
│       │   ├── TranscriptView.jsx # Transcript with interactive filler highlights
│       │   ├── FeedbackView.jsx # AI coaching feedback report & drills
│       │   ├── SettingsModal.jsx # Configurable filler words selector
│       │   └── Footer.jsx      # Project footer & tech badges
│       └── utils/
│           ├── api.js          # API client
│           └── exportReport.js # Markdown report exporter
├── .env.example                # Example environment variables
├── .env                        # Local environment configuration
├── .gitignore                  # Git ignore rules
└── README.md                   # Project documentation
```

---

## 🚀 Setup & Execution Guide

### Prerequisites
- Python 3.9 or higher
- Node.js 18+ and npm

### 1. Backend Setup

```bash
# In the project root, activate the virtual environment (or create one):
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies:
pip install -r backend/requirements.txt

# Start the FastAPI backend server:
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend API will be running at `http://127.0.0.1:8000`. You can inspect the interactive documentation at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

In a separate terminal window:

```bash
cd frontend

# Install frontend dependencies:
npm install

# Start the Vite development server:
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 🔑 Environment Variables & Gemini AI Configuration

The backend reads settings from `.env` in the project root:

```ini
# Google Gemini API Key for Generative AI Coaching
# Get a free key at: https://aistudio.google.com/
GEMINI_API_KEY=

# Gemini model identifier (default: gemini-3.8-flash)
GEMINI_MODEL=gemini-3.8-flash

# Whisper STT model ('tiny', 'base', 'small')
WHISPER_MODEL=tiny

# Maximum allowed audio upload size in MB (default: 25)
MAX_FILE_SIZE_MB=25

# Port
PORT=8000
```

> **Note on Missing API Keys:**  
> SpeakSense is completely functional **without an API key**! If `GEMINI_API_KEY` is empty, SpeakSense utilizes its built-in rule-based coaching engine which evaluates your exact measured metrics and generates actionable coaching recommendations with an informative notice. To activate Google Gemini generative coaching, simply add your API key to `.env` and restart the backend.

---

## 🧪 Testing the Application

1. **1-Click Demo Testing**: On the homepage, click on either **"Pitch Presentation"** or **"Crisp Keynote"** under *Quick Test Samples*. This immediately loads a bundled speech clip without requiring a microphone.
2. **Microphone Recording**: Switch to the **"Record with Microphone"** tab, allow microphone permissions, speak for 10–30 seconds, and watch the real-time audio waveform. Click stop, preview the audio, and click **"Analyze Speech with AI"**.
3. **Custom File Upload**: Drag and drop any `.wav`, `.mp3`, or `.m4a` file.
4. **Export**: Click **"Export Report"** on the dashboard to download a formatted Markdown report.

---

## 🎓 College Mini Project Highlights

- **Zero Database / Auth Overhead**: Clean, stateless REST architecture suitable for academic project reviews.
- **Resource Efficient**: Whisper `tiny` runs locally in seconds without GPU requirements.
- **Error Handling**: Graceful handling for non-audible speech, corrupted files, and missing API keys.
- **Accessible & Responsive**: High-contrast dark theme, fluid mobile/desktop layout, and visual indicators.
