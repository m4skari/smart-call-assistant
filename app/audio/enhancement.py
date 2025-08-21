import os
import tempfile
from typing import Tuple

import numpy as np
import soundfile as sf
import librosa

try:
    import noisereduce as nr  # type: ignore
    _nr_available = True
except Exception:
    _nr_available = False


def _normalize_loudness(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    if audio.size == 0:
        return audio
    rms = np.sqrt(np.mean(np.square(audio))) + 1e-9
    current_db = 20.0 * np.log10(rms)
    gain_db = target_db - current_db
    gain = np.power(10.0, gain_db / 20.0)
    normalized = audio * gain
    max_abs = np.max(np.abs(normalized)) + 1e-12
    if max_abs > 1.0:
        normalized = normalized / max_abs
    return normalized


def enhance_audio_file(input_path: str) -> Tuple[str, dict]:
    """
    Enhance audio file by:
      - resampling to 16k mono
      - spectral noise reduction (if available)
      - loudness normalization to target RMS dB
    Returns path to temp enhanced wav and stats.
    """
    target_sr = int(os.getenv("AUDIO_TARGET_SR", "16000"))
    target_db = float(os.getenv("AUDIO_TARGET_DB", "-20.0"))
    enable_nr = os.getenv("AUDIO_NOISE_REDUCTION", "1") == "1"

    audio, sr = librosa.load(input_path, sr=target_sr, mono=True)

    if enable_nr and _nr_available:
        try:
            reduced = nr.reduce_noise(y=audio, sr=target_sr)
        except Exception:
            reduced = audio
    else:
        reduced = audio

    enhanced = _normalize_loudness(reduced, target_db=target_db)

    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(tmp_path, enhanced, target_sr)

    stats = {
        "sample_rate": target_sr,
        "duration_sec": float(len(enhanced) / float(target_sr)),
        "noise_reduction": enable_nr and _nr_available,
        "target_db": target_db
    }
    return tmp_path, stats
