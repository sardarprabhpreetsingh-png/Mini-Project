import os
import json
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    WHISPER_MODEL,
    MAX_FILE_SIZE_BYTES,
    CORS_ORIGINS,
    DEFAULT_FILLER_WORDS,
    DEFAULT_TARGET_WPM_MIN,
    DEFAULT_TARGET_WPM_MAX
)
from backend.utils.audio import (
    validate_audio_file,
    temporary_audio_file,
    ensure_ffmpeg_in_path
)
from backend.services.transcriber import transcribe_audio, get_whisper_model
from backend.services.analyzer import analyze_speech
from backend.services.ai_coach import generate_ai_feedback, verify_gemini_model_availability

app = FastAPI(
    title="SpeakSense API",
    description="AI-Powered Communication Coaching & Speech Analysis",
    version="1.0.0"
)

# Enable CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLES_DIR = Path(__file__).resolve().parent / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    ensure_ffmpeg_in_path()
    print("SpeakSense API started.")
    print(f"Whisper Model: {WHISPER_MODEL}")
    print(f"Gemini Model: {GEMINI_MODEL}")
    print(f"Gemini API configured: {'Yes' if GEMINI_API_KEY else 'No (using rule-based fallback)'}")


@app.get("/api/health")
async def health_check():
    """Health status and configuration check."""
    return {
        "status": "online",
        "service": "SpeakSense API",
        "version": "1.0.0",
        "gemini_configured": bool(GEMINI_API_KEY),
        "gemini_model": GEMINI_MODEL if GEMINI_API_KEY else None,
        "whisper_model": WHISPER_MODEL,
        "max_file_size_mb": MAX_FILE_SIZE_BYTES // (1024 * 1024),
        "default_fillers": DEFAULT_FILLER_WORDS,
        "target_wpm_range": [DEFAULT_TARGET_WPM_MIN, DEFAULT_TARGET_WPM_MAX]
    }


@app.get("/api/gemini/verify")
async def verify_gemini():
    """Validates real connectivity and availability of the configured Gemini model."""
    if not GEMINI_API_KEY:
        return {
            "configured": False,
            "available": False,
            "model": GEMINI_MODEL,
            "error": "GEMINI_API_KEY environment variable is not configured."
        }
    status = verify_gemini_model_availability(GEMINI_MODEL, GEMINI_API_KEY)
    return {"configured": True, **status}


@app.post("/api/analyze")
async def analyze_recording(
    file: UploadFile = File(...),
    custom_fillers: Optional[str] = Form(None),
):
    """
    Main pipeline:
    1. Validate audio format and size
    2. Transcribe speech using Whisper
    3. Measure WPM, filler words, repetitions, pauses, and score
    4. Generate AI coaching feedback via Gemini (or fallback engine)
    5. Clean up temporary audio file
    """
    validate_audio_file(file.filename)

    # Parse custom fillers if provided
    fillers_list = None
    if custom_fillers:
        try:
            # Check if JSON array
            fillers_list = json.loads(custom_fillers)
        except Exception:
            # Comma-separated list fallback
            fillers_list = [f.strip() for f in custom_fillers.split(",") if f.strip()]

    try:
        with temporary_audio_file(file) as temp_audio_path:
            # Step 1: Transcribe with disfluency preservation
            custom_prompt = None
            if fillers_list:
                sample_fillers = ", ".join(fillers_list[:12])
                custom_prompt = f"{sample_fillers}. Transcribe all speech verbatim including hesitations, pauses, stammering, and filler words."
            transcription = transcribe_audio(temp_audio_path, prompt=custom_prompt)
            transcript_text = transcription.get("text", "").strip()

            if not transcript_text:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "No audible speech could be transcribed from the audio file. Please check audio clarity, volume, and background noise."
                    }
                )

            duration_sec = transcription.get("duration", 0.0)
            segments = transcription.get("segments", [])

            # Step 2: Speech Metrics Analysis
            analysis = analyze_speech(
                transcript=transcript_text,
                duration_sec=duration_sec,
                segments=segments,
                custom_fillers=fillers_list
            )

            # Step 3: AI Coaching Feedback
            feedback = generate_ai_feedback(transcript_text, analysis)

            return {
                "success": True,
                "filename": file.filename,
                "transcript": transcript_text,
                "language": transcription.get("language", "en"),
                "segments": segments,
                "analysis": analysis,
                "feedback": feedback
            }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error during audio processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your recording: {str(e)}"
        )


@app.post("/api/feedback/regenerate")
async def regenerate_feedback(
    transcript: str = Form(...),
    analysis_json: str = Form(...)
):
    """
    Regenerates AI feedback for an already transcribed recording.
    """
    try:
        analysis = json.loads(analysis_json)
        feedback = generate_ai_feedback(transcript, analysis)
        return {"success": True, "feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to regenerate feedback: {str(e)}")


@app.get("/api/samples")
async def list_sample_recordings():
    """Returns available sample audio recordings for 1-click testing."""
    samples = []
    if SAMPLES_DIR.exists():
        for f in SAMPLES_DIR.iterdir():
            if f.suffix.lower() in [".mp3", ".wav", ".m4a"]:
                samples.append({
                    "id": f.stem,
                    "filename": f.name,
                    "title": f.stem.replace("_", " ").title(),
                    "size_bytes": f.stat().st_size
                })
    return {"samples": samples}


@app.get("/api/samples/{filename}")
async def get_sample_audio(filename: str):
    """Streams a sample audio file."""
    file_path = SAMPLES_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Sample recording not found.")
    
    media_type = "audio/mpeg" if file_path.suffix == ".mp3" else "audio/wav"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)
