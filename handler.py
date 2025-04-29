"""
RunPod serverless handler — Kokoro-82M
Returns ONE base-64 μ-law (G.711) blob for Twilio.
"""
import os, base64, numpy as np, audioop
from kokoro import KPipeline
import runpod
import subprocess

# ---------------------------------------------------------------------------
SR_MODEL      = 24_000           # Kokoro native
SR_TWILIO     = 8_000            # Telephony standard
DEFAULT_LANG  = os.getenv("KOKORO_LANG" , "a")
DEFAULT_VOICE = os.getenv("KOKORO_VOICE", "af_heart")
# ---------------------------------------------------------------------------

pipelines = {} # Global cache for KPipeline instances


def kokoro_to_mulaw(pipeline: KPipeline, text: str, voice: str) -> bytes:
    """
    Synthesize with Kokoro, then use ffmpeg to convert:
      float32 24 kHz  →  ffmpeg → bytes mulaw 8 kHz
    Returns raw μ-law bytes (no WAV header).
    Requires ffmpeg to be installed in the environment.
    """
    # 1) synth
    gen = pipeline(text, voice=voice)
    audio = np.concatenate([a for _, _, a in gen])          # float32 −1..1

    # 2) Convert float32 numpy array directly to bytes
    audio_bytes = audio.astype(np.float32).tobytes()

    # 3) Use ffmpeg for resampling and encoding
    try:
        process = subprocess.run(
            [
                "ffmpeg",
                "-f", "f32le",              # Input format: float 32-bit little-endian
                "-ar", str(SR_MODEL),      # Input sample rate: 24000
                "-ac", "1",                # Input channels: 1 (mono)
                "-i", "pipe:0",             # Input source: stdin
                "-f", "mulaw",             # Output format: mu-law
                "-ar", str(SR_TWILIO),     # Output sample rate: 8000
                "-ac", "1",                # Output channels: 1 (mono)
                "pipe:1"                  # Output destination: stdout
            ],
            input=audio_bytes,
            capture_output=True,
            check=True  # Raise CalledProcessError if ffmpeg fails
        )
        mulaw_bytes = process.stdout
    except FileNotFoundError:
        print("ERROR: ffmpeg command not found. Is ffmpeg installed in the environment?")
        raise
    except subprocess.CalledProcessError as e:
        print(f"ERROR: ffmpeg failed with exit code {e.returncode}")
        print(f"ffmpeg stderr: {e.stderr.decode()}")
        raise

    return mulaw_bytes


def handler(job):
    """
    Input JSON:
      { "text": "...", "voice": "af_heart", "lang": "a" }

    Output JSON:
      { "status": "completed",
        "audio_mulaw_b64": "<base64>",
        "encoding": "audio/x-mulaw",
        "sample_rate": 8000 }
    """
    inp   = job["input"]
    text  = inp.get("text", "Hello from Kokoro on RunPod!")
    voice = inp.get("voice", DEFAULT_VOICE)
    lang  = inp.get("lang",  DEFAULT_LANG)

    # Get or initialize the pipeline for the requested language
    if lang not in pipelines:
        print(f"Initializing pipeline for lang='{lang}'...")
        pipelines[lang] = KPipeline(lang_code=lang)
        print(f"Pipeline for lang='{lang}' initialized.")
    pipeline = pipelines[lang]

    mulaw_bytes = kokoro_to_mulaw(pipeline, text, voice)
    mulaw_b64   = base64.b64encode(mulaw_bytes).decode()

    return {
        "status":           "completed",
        "audio_mulaw_b64":  mulaw_b64,
        "encoding":         "audio/x-mulaw",
        "sample_rate":      SR_TWILIO           # 8000
    }


# ---------------------- RunPod bootstrap ------------------------------------
runpod.serverless.start({"handler": handler})