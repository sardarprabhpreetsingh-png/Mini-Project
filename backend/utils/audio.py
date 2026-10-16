import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from contextlib import contextmanager
from fastapi import UploadFile, HTTPException

from backend.config import ALLOWED_AUDIO_EXTENSIONS, MAX_FILE_SIZE_BYTES

# Ensure imageio-ffmpeg is in PATH
_ffmpeg_initialized = False

def ensure_ffmpeg_in_path() -> str:
    global _ffmpeg_initialized
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = Path(ffmpeg_exe).parent

        # Whisper looks specifically for an executable called 'ffmpeg'
        standard_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        standard_path = ffmpeg_dir / standard_name

        if not standard_path.exists():
            try:
                if os.name != "nt":
                    os.symlink(os.path.basename(ffmpeg_exe), standard_path)
                else:
                    shutil.copy2(ffmpeg_exe, standard_path)
            except Exception as se:
                print(f"Could not symlink ffmpeg: {se}")

        current_path = os.environ.get("PATH", "")
        ffmpeg_dir_str = str(ffmpeg_dir)
        if ffmpeg_dir_str not in current_path:
            os.environ["PATH"] = ffmpeg_dir_str + os.pathsep + current_path

        _ffmpeg_initialized = True
        return str(standard_path if standard_path.exists() else ffmpeg_exe)
    except Exception as e:
        print(f"Warning: imageio_ffmpeg could not be initialized: {e}")
        return "ffmpeg"


def validate_audio_file(filename: str, file_size: int = 0):
    """Validate audio filename extension and size."""
    if not filename:
        raise HTTPException(status_code=400, detail="No file uploaded or filename missing.")

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        allowed_list = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{ext}'. Allowed formats: {allowed_list}"
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {max_mb}MB."
        )


@contextmanager
def temporary_audio_file(upload_file: UploadFile):
    """
    Saves an uploaded FastAPI file to a temporary file on disk,
    yields the Path, and guarantees deletion when finished.
    """
    ensure_ffmpeg_in_path()
    ext = Path(upload_file.filename).suffix.lower() or ".wav"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    temp_path = Path(temp_file.name)

    total_bytes = 0
    try:
        # Stream chunks to prevent high memory usage
        while chunk := upload_file.file.read(1024 * 1024):  # 1MB chunks
            total_bytes += len(chunk)
            if total_bytes > MAX_FILE_SIZE_BYTES:
                max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded audio exceeds maximum limit of {max_mb}MB."
                )
            temp_file.write(chunk)
        temp_file.close()

        if total_bytes == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        yield temp_path
    finally:
        # Guarantee cleanup
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as e:
                print(f"Failed to delete temp file {temp_path}: {e}")
