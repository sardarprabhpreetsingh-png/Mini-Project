import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import whisper

from backend.config import WHISPER_MODEL
from backend.utils.audio import ensure_ffmpeg_in_path

_cached_model = None

# Disfluency-preserving prompt to prevent Whisper from smoothing over spoken fillers and hesitations
DEFAULT_DISFLUENCY_PROMPT = (
    "Um, uh, erm, er, hmm, like, you know, I mean, actually, basically, sort of, ah. "
    "Transcribe all speech verbatim, including hesitations, pauses, stammering, and filler words."
)

def get_whisper_model():
    """Lazily load and cache the Whisper model in memory."""
    global _cached_model
    ensure_ffmpeg_in_path()
    if _cached_model is None:
        print(f"Loading Whisper model '{WHISPER_MODEL}'...")
        _cached_model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded successfully.")
    return _cached_model


def transcribe_audio(audio_path: Path, prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribes audio file using Whisper.
    Preserves disfluencies and hesitations (um, uh, erm, etc.) using an initial prompt.
    Returns:
    {
        "text": full text transcript,
        "language": detected language,
        "duration": duration in seconds,
        "segments": [
            {"id": 0, "start": 0.0, "end": 2.5, "text": "..."}
        ],
        "disfluency_prompt_applied": True
    }
    """
    ensure_ffmpeg_in_path()
    model = get_whisper_model()
    prompt_to_use = prompt if (prompt and prompt.strip()) else DEFAULT_DISFLUENCY_PROMPT

    try:
        # Transcribe with disfluency prompt and word/segment timestamps
        transcribe_kwargs = {
            "fp16": False,  # CPU / Apple Silicon friendly
            "verbose": False,
            "initial_prompt": prompt_to_use,
            "condition_on_previous_text": True,
        }

        # carry_initial_prompt is supported in whisper >= 2024
        try:
            result = model.transcribe(str(audio_path), carry_initial_prompt=True, **transcribe_kwargs)
        except TypeError:
            result = model.transcribe(str(audio_path), **transcribe_kwargs)

        segments_data: List[Dict[str, Any]] = []
        duration = 0.0

        for seg in result.get("segments", []):
            start = round(float(seg.get("start", 0.0)), 2)
            end = round(float(seg.get("end", 0.0)), 2)
            text = seg.get("text", "").strip()
            segments_data.append({
                "id": seg.get("id", len(segments_data)),
                "start": start,
                "end": end,
                "text": text
            })
            if end > duration:
                duration = end

        full_text = result.get("text", "").strip()

        return {
            "text": full_text,
            "language": result.get("language", "en"),
            "duration": round(duration, 2),
            "segments": segments_data,
            "disfluency_prompt_applied": True,
            "initial_prompt_used": prompt_to_use
        }
    except Exception as e:
        print(f"Transcription error: {e}")
        raise RuntimeError(f"Speech-to-text transcription failed: {str(e)}")
