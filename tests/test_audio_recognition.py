import pytest
import subprocess
import shutil
from pathlib import Path
from backend.utils.audio import ensure_ffmpeg_in_path
from backend.services.transcriber import transcribe_audio
from backend.services.analyzer import analyze_speech

ensure_ffmpeg_in_path()

@pytest.fixture(scope="module")
def real_speech_audio(tmp_path_factory):
    """
    Synthesizes real spoken audio with disfluencies using macOS speech synthesizer
    and converts to WAV via bundled FFmpeg.
    Sentence: 'Um, I think, uh, we should, you know, basically start now.'
    """
    tmp_dir = tmp_path_factory.mktemp("audio_test")
    aiff_path = tmp_dir / "known_filler.aiff"
    wav_path = tmp_dir / "known_filler.wav"

    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    spoken_text = "Um, I think, uh, we should, you know, basically start now."
    subprocess.run(["say", "-v", "Samantha", spoken_text, "-o", str(aiff_path)], check=True)
    subprocess.run([ffmpeg_exe, "-y", "-i", str(aiff_path), str(wav_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    yield wav_path

    # Cleanup
    if aiff_path.exists():
        aiff_path.unlink()
    if wav_path.exists():
        wav_path.unlink()


def test_real_audio_transcription_preserves_fillers(real_speech_audio):
    """
    Verifies that Whisper transcribes real spoken audio while preserving
    disfluencies (e.g. 'Um', 'uh', 'you know', 'basically') when conditioned with the disfluency prompt.
    """
    assert real_speech_audio.exists()

    result = transcribe_audio(real_speech_audio)
    transcript = result["text"]
    assert transcript, "Transcription returned empty text"

    print(f"\n[Real Audio Recognized Transcript]: '{transcript}'")

    # Verify that disfluencies were actually transcribed by Whisper from the audio
    lower_t = transcript.lower()
    assert "um" in lower_t or "uh" in lower_t, f"Whisper omitted all hesitations: '{transcript}'"

    # Now run analyzer on the real audio transcription
    analysis = analyze_speech(
        transcript=transcript,
        duration_sec=result["duration"],
        segments=result["segments"]
    )

    fillers = analysis["fillers"]
    print(f"[Real Audio Detected Fillers]: count={fillers['total_fillers']}, breakdown={fillers['breakdown']}")

    # The real audio must have detected fillers (not 0)
    assert fillers["total_fillers"] > 0, "Real audio failed: reported 0 fillers!"
    assert len(fillers["breakdown"]) > 0
    assert len(fillers["occurrences"]) > 0


def test_real_audio_against_api_endpoint(real_speech_audio):
    """
    Tests the complete end-to-end FastAPI endpoint with real audio upload.
    """
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    with open(real_speech_audio, "rb") as f:
        response = client.post(
            "/api/analyze",
            files={"file": ("known_filler.wav", f, "audio/wav")}
        )

    assert response.status_code == 200, f"API error: {response.text}"
    data = response.json()

    assert data["success"] is True
    assert "transcript" in data
    assert "analysis" in data
    assert "fillers" in data["analysis"]

    fillers_data = data["analysis"]["fillers"]
    print(f"\n[API Endpoint Response]: total_fillers={fillers_data['total_fillers']}, breakdown={fillers_data['breakdown']}")

    assert fillers_data["total_fillers"] > 0, "API returned 0 fillers on real audio containing fillers!"
    assert len(fillers_data["breakdown"]) > 0
    assert "diagnostics" in fillers_data
