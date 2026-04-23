#!/usr/bin/env python3
"""
Environment detection for transcribe-universal onboarding.
Outputs JSON with available backends and platform info.
"""
import json
import os
import platform
import shutil
import sys


def check_env():
    result = {
        "platform": sys.platform,
        "arch": platform.machine(),
        "is_apple_silicon": sys.platform == "darwin" and platform.machine() == "arm64",
        "backends": {},
        "ocr": {},
        "config_exists": os.path.exists(
            os.path.expanduser("~/.transcribe-universal/config.json")
        ),
    }

    # -- Transcription backends --

    # MLX Whisper (Apple Silicon only)
    if result["is_apple_silicon"]:
        try:
            import mlx_whisper  # noqa: F401
            result["backends"]["mlx"] = {"available": True, "note": "Apple Silicon GPU"}
        except ImportError:
            result["backends"]["mlx"] = {
                "available": False,
                "install": "pip install mlx-whisper",
            }
    else:
        result["backends"]["mlx"] = {"available": False, "note": "requires Apple Silicon"}

    # Groq API
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        result["backends"]["groq"] = {"available": True, "note": "API key found"}
    else:
        result["backends"]["groq"] = {
            "available": False,
            "note": "GROQ_API_KEY not set",
            "setup_guide": "https://app.guideflow.com/player/np18zw3fek",
        }

    # faster-whisper
    try:
        import faster_whisper  # noqa: F401
        result["backends"]["faster_whisper"] = {"available": True, "note": "CPU/GPU"}
    except ImportError:
        result["backends"]["faster_whisper"] = {
            "available": False,
            "install": "pip install faster-whisper",
        }

    # OpenAI Whisper (CPU fallback)
    try:
        import whisper  # noqa: F401
        result["backends"]["openai_whisper"] = {"available": True, "note": "CPU"}
    except ImportError:
        result["backends"]["openai_whisper"] = {
            "available": False,
            "install": "pip install openai-whisper",
        }

    # -- OCR backends --
    if sys.platform == "darwin":
        result["ocr"]["macos_vision"] = {"available": True, "note": "built-in"}
    elif sys.platform == "win32":
        result["ocr"]["windows_ocr"] = {"available": True, "note": "built-in (Win10+)"}

    if shutil.which("tesseract"):
        result["ocr"]["tesseract"] = {"available": True}
    else:
        install_cmd = {
            "darwin": "brew install tesseract",
            "linux": "sudo apt install tesseract-ocr",
            "win32": "choco install tesseract",
        }.get(sys.platform, "install tesseract-ocr")
        result["ocr"]["tesseract"] = {"available": False, "install": install_cmd}

    result["ocr"]["claude_vision"] = {"available": True, "note": "always available"}

    # -- OpenCC (simplified → traditional Chinese) --
    try:
        from opencc import OpenCC  # noqa: F401
        result["opencc"] = {"available": True}
    except ImportError:
        result["opencc"] = {
            "available": False,
            "important_for": ["zh", "zh-tw", "zh-hant"],
            "install": "pip install opencc-python-reimplemented",
            "note": "中文轉錄必備 — Whisper 輸出常為簡體，需轉換為繁體",
        }

    # -- pydub (audio splitting for Groq 25MB limit) --
    try:
        from pydub import AudioSegment  # noqa: F401
        result["pydub"] = True
    except ImportError:
        result["pydub"] = False

    return result


if __name__ == "__main__":
    env = check_env()
    print(json.dumps(env, indent=2, ensure_ascii=False))
