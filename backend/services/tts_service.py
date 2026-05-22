"""Piper text-to-speech service."""
import base64
import io
import wave
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _get_voice(model_path: str, config_path: str):
    from piper import PiperVoice

    return PiperVoice.load(model_path, config_path)


def _resolve_config_path(model_path: str, config_path: str | None = None) -> str:
    return config_path or str(Path(model_path).with_suffix(".onnx.json"))


def synthesize(text: str, model_path: str, config_path: str | None = None) -> bytes:
    """Synthesize text into WAV bytes using Piper."""
    resolved_config_path = _resolve_config_path(model_path, config_path)
    voice = _get_voice(model_path, resolved_config_path)

    try:
        from piper import SynthesisConfig

        config = SynthesisConfig(length_scale=1.0)
    except (ImportError, TypeError, AttributeError):
        config = None

    audio_buffer = io.BytesIO()
    with wave.open(audio_buffer, "wb") as wav_file:
        if config is None:
            voice.synthesize_wav(text, wav_file)
        else:
            voice.synthesize_wav(text, wav_file, config)

    return audio_buffer.getvalue()


def synthesize_to_base64(text: str, model_path: str, config_path: str | None = None) -> str:
    """Synthesize text and return base64-encoded WAV audio."""
    wav = synthesize(text, model_path, config_path)
    return base64.b64encode(wav).decode("ascii")


class PiperTTSService:
    """Small wrapper around Piper synthesis paths."""

    def __init__(self, model_path: str, config_path: str | None = None):
        self.model_path = model_path
        self.config_path = config_path

    def speak(self, text: str) -> bytes:
        return synthesize(text, self.model_path, self.config_path)

    def speak_base64(self, text: str) -> str:
        return synthesize_to_base64(text, self.model_path, self.config_path)
