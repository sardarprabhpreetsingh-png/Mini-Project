import os
import pytest
from pathlib import Path

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.services.ai_coach import (
    sanitize_gemini_message,
    parse_gemini_error,
    verify_gemini_model_availability,
    build_fallback_feedback,
    generate_ai_feedback,
)
from backend.services.analyzer import analyze_speech
from backend.services.transcriber import transcribe_audio


def test_model_configuration_and_env():
    """Verify GEMINI_MODEL is configured and defaults to gemini-3.8-flash if not specified."""
    assert GEMINI_MODEL, "GEMINI_MODEL must not be empty"
    # Should be gemini-3.8-flash or valid model configured
    assert "gemini" in GEMINI_MODEL.lower()
    assert GEMINI_API_KEY, "GEMINI_API_KEY should be loaded from project-root .env"


def test_api_key_sanitization():
    """Verify that sensitive API keys are never leaked in error messages."""
    fake_key = "AIzaSyB1234567890abcdefghijklmnopqrstuv"
    raw_message = f"Error calling Google API with key={fake_key}: 404 NOT_FOUND. Model gemini-2.5-flash is no longer available."
    sanitized = sanitize_gemini_message(raw_message, fake_key)

    assert fake_key not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "404 NOT_FOUND" in sanitized


def test_404_error_diagnostics_and_alternatives():
    """Verify that a 404 error (e.g. from deprecated gemini-2.5-flash) reports the real error and alternatives."""
    mock_404 = Exception("404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.8-flash.'}}")
    diag = parse_gemini_error(mock_404, "gemini-2.5-flash")

    assert "gemini-2.5-flash" in diag["user_message"]
    assert "no longer available" in diag["user_message"] or "not found" in diag["user_message"]
    assert "gemini-3.8-flash" in diag["suggested_alternatives"]


def test_429_quota_exhausted_diagnostics():
    """Verify that a 429 quota error produces an informative diagnostic message with lightweight alternatives."""
    mock_429 = Exception("429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-3.8-flash'}}")
    diag = parse_gemini_error(mock_429, "gemini-3.8-flash")

    assert "quota" in diag["user_message"].lower() or "limit" in diag["user_message"].lower()
    assert "gemini-2.5-flash-lite" in diag["suggested_alternatives"]


def test_heuristic_fallback_labeling():
    """Verify fallback feedback is clearly marked as heuristic rule engine, not AI."""
    sample_analysis = {
        "word_count": 20,
        "duration_formatted": "8s",
        "duration_seconds": 8.0,
        "pacing": {"wpm": 150, "status": "Optimal", "message": "Good pace"},
        "fillers": {"total_fillers": 1, "filler_ratio_percent": 5.0, "breakdown": {"um": 1}},
        "repetitions": {"consecutive_repeats": {}, "frequent_words": {}},
        "pauses": {"pause_count": 1, "avg_pause_duration_sec": 0.5, "flow_rating": "Natural"},
        "score": {"score": 82, "level": "Proficient"}
    }
    fallback = build_fallback_feedback("Hello world, um, testing.", sample_analysis, reason="Test fallback")

    assert fallback["is_ai_available"] is False
    assert fallback["source"] == "heuristic_fallback"
    assert fallback["model_used"] == "SpeakSense Rule Engine"
    assert "Notice: Test fallback" in fallback["notice"]
    assert len(fallback["strengths"]) > 0
    assert len(fallback["actionable_exercises"]) > 0


def test_real_gemini_api_feedback_generation():
    """
    Tests live Gemini API feedback generation with the user's active API key.
    Uses an available model to ensure a real generative request succeeds.
    """
    assert GEMINI_API_KEY, "GEMINI_API_KEY is required for live testing"

    sample_transcript = "Good morning team. Today I want to share our progress on the quarterly initiatives. We achieved a twenty percent increase in user engagement."
    sample_analysis = {
        "word_count": 23,
        "duration_formatted": "9s",
        "duration_seconds": 9.2,
        "pacing": {"wpm": 150, "status": "Optimal", "message": "Optimal presentation cadence"},
        "fillers": {"total_fillers": 0, "filler_ratio_percent": 0.0, "breakdown": {}},
        "repetitions": {"consecutive_repeats": {}, "frequent_words": {"quarterly": 1}},
        "pauses": {"pause_count": 2, "avg_pause_duration_sec": 0.7, "flow_rating": "Natural"},
        "score": {"score": 90, "level": "Exemplary"}
    }

    # Test with available model: gemini-2.5-flash-lite or gemini-3.8-flash
    # First check availability of GEMINI_MODEL
    avail_check = verify_gemini_model_availability(GEMINI_MODEL)
    test_model = GEMINI_MODEL if avail_check["available"] else "gemini-2.5-flash-lite"

    result = generate_ai_feedback(sample_transcript, sample_analysis, model_override=test_model)

    assert result["is_ai_available"] is True, f"Live Gemini API call failed: {result.get('notice')}"
    assert result["source"] == "gemini_ai"
    assert result["model_used"] == test_model
    assert "summary" in result and len(result["summary"]) > 10
    assert "strengths" in result and len(result["strengths"]) > 0
    assert "actionable_exercises" in result and len(result["actionable_exercises"]) > 0


def test_full_audio_analysis_to_gemini_feedback_workflow():
    """
    End-to-end integration test:
    Audio file -> Whisper transcription -> Speech metrics analysis -> Live Gemini AI coaching report.
    """
    audio_path = Path(__file__).resolve().parent.parent / "backend" / "samples" / "crisp_keynote.mp3"
    if not audio_path.exists():
        audio_path = Path(__file__).resolve().parent / "test_sample.wav"

    assert audio_path.exists(), f"Sample audio not found at {audio_path}"

    # Step 1: Transcribe with Whisper
    transcription = transcribe_audio(audio_path)
    transcript = transcription["text"]
    assert transcript, "Transcription must return non-empty text"

    # Step 2: Extract speech metrics
    analysis = analyze_speech(
        transcript=transcript,
        duration_sec=transcription["duration"],
        segments=transcription["segments"]
    )
    assert analysis["word_count"] > 0
    assert analysis["pacing"]["wpm"] > 0

    # Step 3: Send real transcript & metrics to Gemini API
    avail_check = verify_gemini_model_availability(GEMINI_MODEL)
    test_model = GEMINI_MODEL if avail_check["available"] else "gemini-2.5-flash-lite"

    feedback = generate_ai_feedback(transcript, analysis, model_override=test_model)

    assert feedback["is_ai_available"] is True, f"End-to-end feedback failed: {feedback.get('notice')}"
    assert feedback["source"] == "gemini_ai"
    assert feedback["model_used"] == test_model
    assert feedback["summary"]
    assert len(feedback["strengths"]) >= 1
