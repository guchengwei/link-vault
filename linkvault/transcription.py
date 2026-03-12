"""
Local video transcription using faster-whisper (GPU-accelerated).

Pipeline:
  1. Download audio from video URL via yt-dlp
  2. Transcribe audio locally with faster-whisper
  3. Return cleaned transcript text

All errors are non-fatal — functions return None on failure and log warnings.
"""

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TranscriptionConfig:
    model_size: str = "small"   # tiny, base, small, medium, large-v3
    device: str = "auto"        # auto, cuda, cpu
    language: str = "auto"      # auto, en, zh, ja, ko, ...
    audio_timeout: int = 120    # seconds for yt-dlp audio download
    transcribe_timeout: int = 300  # seconds max for whisper transcription


# ---------------------------------------------------------------------------
# Singleton model cache (lazy-loaded)
# ---------------------------------------------------------------------------

_model_cache: dict = {}


def _get_model(config: TranscriptionConfig):
    """Lazy-load and cache the WhisperModel singleton."""
    key = (config.model_size, config.device)
    if key not in _model_cache:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("[transcription] faster-whisper not installed", file=sys.stderr)
            return None

        device = config.device
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        compute_type = "float16" if device == "cuda" else "int8"
        print(f"[transcription] Loading whisper model: {config.model_size} "
              f"on {device} ({compute_type})", file=sys.stderr)
        try:
            model = WhisperModel(config.model_size, device=device,
                                 compute_type=compute_type)
            _model_cache[key] = model
        except Exception as e:
            print(f"[transcription] Failed to load model: {e}", file=sys.stderr)
            return None
    return _model_cache[key]


# ---------------------------------------------------------------------------
# Audio download via yt-dlp
# ---------------------------------------------------------------------------

def download_audio(url: str, dest_dir: str, timeout: int = 120) -> Optional[Path]:
    """Download audio from a video URL using yt-dlp. Returns path to WAV file."""
    output_template = str(Path(dest_dir) / "audio.%(ext)s")
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--no-playlist",
        "--no-post-overwrites",
        "-o", output_template,
        url,
    ]
    print(f"[transcription] Downloading audio: {url}", file=sys.stderr)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            print(f"[transcription] yt-dlp audio download failed: "
                  f"{proc.stderr[:300]}", file=sys.stderr)
            return None
    except FileNotFoundError:
        print("[transcription] yt-dlp not installed", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print(f"[transcription] yt-dlp audio download timed out ({timeout}s)",
              file=sys.stderr)
        return None

    # Find the output WAV file
    wav_files = list(Path(dest_dir).glob("audio*.wav"))
    if not wav_files:
        # yt-dlp may produce other formats if wav conversion fails
        all_audio = list(Path(dest_dir).glob("audio*"))
        if all_audio:
            print(f"[transcription] No WAV found, got: {[f.name for f in all_audio]}",
                  file=sys.stderr)
        else:
            print("[transcription] No audio file produced", file=sys.stderr)
        return None

    return wav_files[0]


# ---------------------------------------------------------------------------
# Whisper transcription
# ---------------------------------------------------------------------------

def transcribe_audio(audio_path: Path,
                     config: TranscriptionConfig) -> Optional[str]:
    """Transcribe an audio file with faster-whisper. Returns transcript text."""
    model = _get_model(config)
    if model is None:
        return None

    language = config.language if config.language != "auto" else None
    print(f"[transcription] Transcribing: {audio_path.name} "
          f"(lang={language or 'auto-detect'})", file=sys.stderr)

    try:
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True,
        )
        detected_lang = info.language
        print(f"[transcription] Detected language: {detected_lang} "
              f"(prob={info.language_probability:.2f})", file=sys.stderr)

        lines = []
        for segment in segments:
            text = segment.text.strip()
            if text and (not lines or lines[-1] != text):
                lines.append(text)

        transcript = "\n".join(lines)
        if transcript:
            print(f"[transcription] Transcript: {len(transcript)} chars, "
                  f"{len(lines)} segments", file=sys.stderr)
        else:
            print("[transcription] Empty transcript (no speech detected)",
                  file=sys.stderr)
            return None
        return transcript

    except Exception as e:
        print(f"[transcription] Whisper error: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# High-level: URL → transcript (download + transcribe)
# ---------------------------------------------------------------------------

def transcribe_url(url: str,
                   config: Optional[TranscriptionConfig] = None) -> Optional[str]:
    """
    Download audio from URL and transcribe with faster-whisper.

    Returns transcript text, or None if any step fails.
    All errors are non-fatal (logged to stderr).
    """
    if config is None:
        config = TranscriptionConfig()

    try:
        with tempfile.TemporaryDirectory(prefix="lv-whisper-") as tmpdir:
            audio_path = download_audio(url, tmpdir, timeout=config.audio_timeout)
            if audio_path is None:
                return None
            return transcribe_audio(audio_path, config)
    except Exception as e:
        print(f"[transcription] Unexpected error: {e}", file=sys.stderr)
        return None
