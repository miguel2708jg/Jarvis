"""Voice endpoints for Groq STT and Piper TTS."""
import io
import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from langchain_core.messages import HumanMessage

from backend.api.dependencies import get_jarvis_graph
from backend.api.errors import llm_unavailable_message
from backend.api.routers.chat import _ensure_visible_thread, _extract_text_content
from backend.config import settings
from backend.models.chat import TTSRequest, TTSResponse, VoiceResponse
from backend.services import message_service, thread_service
from backend.services.tts_service import PiperTTSService

router = APIRouter()


def _convert_to_wav(content: bytes, content_type: str) -> bytes:
    """Convert arbitrary audio bytes to 16 kHz mono PCM WAV using ffmpeg."""
    _ = content_type
    try:
        proc = subprocess.run(
            [
                settings.ffmpeg_path,
                "-i",
                "pipe:0",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                "-f",
                "wav",
                "pipe:1",
            ],
            input=content,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError(
            f"Audio conversion failed: ffmpeg was not found at {settings.ffmpeg_path!r}"
        ) from exc

    if proc.returncode != 0:
        detail = proc.stderr.decode(errors="replace")[:200]
        raise ValueError(f"Audio conversion failed: {detail}")
    return proc.stdout


async def _transcribe(wav_content: bytes) -> str:
    """Transcribe WAV audio through Groq."""
    if settings.stt_provider.lower() != "groq":
        raise RuntimeError(f"Unsupported STT_PROVIDER: {settings.stt_provider}")
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is required for voice transcription")

    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    kwargs = {
        "model": settings.groq_stt_model,
        "file": ("audio.wav", io.BytesIO(wav_content), "audio/wav"),
    }
    if settings.groq_stt_language:
        kwargs["language"] = settings.groq_stt_language

    response = client.audio.transcriptions.create(**kwargs)
    return response.text


async def _chat(transcript: str, session_id: str, personality_id: str | None, graph) -> str:
    """Run the agent for a voice transcript and persist the visible turn."""
    _ensure_visible_thread(session_id, transcript)
    message_service.create_message(session_id, transcript, role="user")

    state = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=transcript)],
            "user_id": "default",
            "session_id": session_id,
            "personality_id": personality_id,
        }
    )
    response_text = _extract_text_content(state["messages"][-1])
    message_service.create_message(session_id, response_text, role="assistant")
    thread_service.touch_thread(session_id)
    return response_text


def _synthesize(text: str) -> str:
    if settings.tts_provider.lower() != "piper":
        raise RuntimeError(f"Unsupported TTS_PROVIDER: {settings.tts_provider}")
    model_path = settings.piper_model_path or str(Path("/tmp/piper-voices") / f"{settings.tts_voice}.onnx")
    service = PiperTTSService(model_path, settings.piper_config_path)
    return service.speak_base64(text)


@router.post("/voice", response_model=VoiceResponse)
async def voice_pipeline(
    audio: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    personality_id: str | None = Form(default=None),
    graph=Depends(get_jarvis_graph),
):
    resolved_session_id = session_id or str(uuid.uuid4())
    try:
        content = await audio.read()
        wav_content = _convert_to_wav(content, audio.content_type or "application/octet-stream")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        transcript = await _transcribe(wav_content)
        response_text = await _chat(transcript, resolved_session_id, personality_id, graph)
        audio_base64 = _synthesize(response_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=llm_unavailable_message(exc)) from exc

    return VoiceResponse(
        transcript=transcript,
        response_text=response_text,
        audio_base64=audio_base64,
        session_id=resolved_session_id,
    )


@router.post("/voice/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        return TTSResponse(audio_base64=_synthesize(text))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
