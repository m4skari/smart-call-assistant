
import os
import uuid
import wave
from typing import Optional, Dict, Any

try:
    from google import genai
    from google.genai import types
    _gemini_ok = True
except Exception as _e:
    _gemini_ok = False
    _gemini_import_error = str(_e)


def _save_wav(pcm_bytes: bytes, path: str, rate: int = 24000, channels: int = 1, sampwidth: int = 2) -> None:
    """Save raw PCM bytes to a WAV file on disk."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(rate)
        wf.writeframes(pcm_bytes)


def synthesize_tts(text: str,
                   lang: Optional[str] = None,
                   voice: Optional[str] = None,
                   gender: Optional[str] = None,
                   server: Optional[str] = None,
                   timeout_sec: int = 60) -> Dict[str, Any]:
    """Gemini TTS in the *old* talkbot_tts format.

    Parameters mirror the previous API so the rest of the app doesn't need changes.
    Returns a dict that (on success) includes 'audio_file' pointing to a saved WAV file.
    """
    if not text or not isinstance(text, str):
        raise ValueError("text must be a non-empty string")

    meta: Dict[str, Any] = {
        "engine": "gemini",
        "model": os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts"),
        "voice": voice or os.getenv("GEMINI_TTS_VOICE", "achernar"),
        "lang": (lang or os.getenv("TTS_LANG") or "auto"),
        "status_code": 0,
    }

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        meta["error"] = "GEMINI_API_KEY env var is required"
        return meta

    if not _gemini_ok:
        meta["error"] = f"google-genai import failed: {_gemini_import_error}"
        return meta

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=meta["model"],
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=meta["voice"]
                        )
                    )
                )
            ),
            # NOTE: timeout is handled by underlying client; we keep timeout_sec for signature compatibility
        )

        # Extract the first audio part
        part = resp.candidates[0].content.parts[0]
        if not hasattr(part, "inline_data") or not getattr(part.inline_data, "data", None):
            meta["error"] = "No audio data returned from Gemini"
            return meta

        pcm_bytes = part.inline_data.data  # bytes (PCM)

        # Where to save (same convention as old script)
        responses_dir = os.getenv("RESPONSES_DIR", "storage/responses")
        os.makedirs(responses_dir, exist_ok=True)
        file_name = f"response_{uuid.uuid4()}.wav"
        out_path = os.path.join(responses_dir, file_name)

        # 24kHz mono 16-bit PCM as per runner example
        _save_wav(pcm_bytes, out_path, rate=24000, channels=1, sampwidth=2)

        meta.update({
            "status_code": 200,
            "audio_file": out_path,
            "audio_mime": "audio/wav",
            "bytes": len(pcm_bytes)
        })
        return meta

    except Exception as e:
        meta["error"] = str(e)
        return meta
