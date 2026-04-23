#!/usr/bin/env python3
"""
Universal Transcription Script — multi-backend, cross-platform.

Usage:
  python3 transcribe-universal.py --file "path.m4a" --name "Meeting" --context "Jim, Canon"
  python3 transcribe-universal.py --file "p1.m4a" "p2.m4a" --name "Meeting" --context "..."
  python3 transcribe-universal.py --file "path.m4a"  (name defaults to filename stem)
  python3 transcribe-universal.py --check  (print detected backend and exit)

Output: {output_base}/{date}_{name}/raw-transcript.md
"""
import argparse
import json
import os
import re
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────

CONFIG_PATH = Path.home() / ".transcribe-universal" / "config.json"
DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"
GROQ_MODEL = "whisper-large-v3-turbo"
GROQ_MAX_BYTES = 25 * 1024 * 1024  # 25 MB
CHUNK_MINUTES = 10  # split length for oversized files

BASE_PROMPT = (
    "以下是繁體中文和英文混雜的會議內容。"
    "包含技術術語如 AI、SaaS、AWS、API、EC、PIM、MOU、KPI 等。"
    "請使用繁體中文輸出。"
)


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ── Post-processing (from CYB proven logic) ─────────────────────────

def load_replacements(config):
    rpath = config.get("replacements_path", "")
    if rpath:
        rpath = Path(rpath).expanduser()
    else:
        rpath = Path.home() / ".transcribe-universal" / "replacements.json"
    if not rpath.exists():
        return {}
    try:
        with open(rpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except (json.JSONDecodeError, IOError):
        return {}


def apply_replacements(text, replacements):
    for wrong, correct in replacements.items():
        has_cjk = any("\u4e00" <= c <= "\u9fff" for c in wrong)
        if has_cjk:
            text = text.replace(wrong, correct)
        else:
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(wrong) + r"(?![a-zA-Z0-9])"
            text = re.sub(pattern, correct, text, flags=re.IGNORECASE)
    return text


def clean_hallucination(text):
    pattern = r"([\u4e00-\u9fff\w]{1,10}?)\s*(?:\1\s*){3,}"
    return re.sub(pattern, lambda m: m.group(1) + " [⚠️ 音訊不清]", text)


def post_process_segments(segments, replacements):
    for seg in segments:
        text = seg["text"]
        if replacements:
            text = apply_replacements(text, replacements)
        text = clean_hallucination(text)
        seg["text"] = text
    return segments


def convert_s2t(segments, language="zh"):
    """Simplified → Traditional Chinese if opencc is available."""
    if language not in ("zh", "zh-tw", "zh-hant"):
        return segments
    try:
        from opencc import OpenCC

        cc = OpenCC("s2twp")
        for seg in segments:
            seg["text"] = cc.convert(seg["text"])
    except ImportError:
        print(
            "⚠️  opencc 未安裝，簡繁轉換已跳過。"
            "轉錄結果可能包含簡體字。"
            "\n   安裝方式：pip install opencc-python-reimplemented"
        )
    return segments


# ── Backend abstraction ─────────────────────────────────────────────

class TranscribeBackend(ABC):
    name: str

    @abstractmethod
    def transcribe(self, audio_path: str, prompt: str, language: str) -> list[dict]:
        """Return list of {'start': float, 'end': float, 'text': str}."""
        ...


class MLXBackend(TranscribeBackend):
    name = "MLX Whisper"

    def transcribe(self, audio_path, prompt, language):
        import mlx_whisper

        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=DEFAULT_MODEL,
            language=language,
            initial_prompt=prompt,
            verbose=False,
        )
        return result.get("segments", [])


class GroqBackend(TranscribeBackend):
    name = "Groq API"

    def transcribe(self, audio_path, prompt, language):
        from groq import Groq

        client = Groq()
        file_size = os.path.getsize(audio_path)

        if file_size > GROQ_MAX_BYTES:
            return self._transcribe_chunked(client, audio_path, prompt, language)

        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                file=(Path(audio_path).name, f.read()),
                model=GROQ_MODEL,
                prompt=prompt,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
        return [
            {"start": s.start, "end": s.end, "text": s.text}
            for s in (result.segments or [])
        ]

    def _transcribe_chunked(self, client, audio_path, prompt, language):
        """Split audio into chunks and transcribe each."""
        try:
            from pydub import AudioSegment
        except ImportError:
            print("❌ pydub is required for files > 25MB. Install: pip install pydub")
            sys.exit(1)

        audio = AudioSegment.from_file(audio_path)
        chunk_ms = CHUNK_MINUTES * 60 * 1000
        chunks = [audio[i : i + chunk_ms] for i in range(0, len(audio), chunk_ms)]

        all_segments = []
        time_offset = 0.0

        for i, chunk in enumerate(chunks):
            print(f"   ▶ 片段 {i + 1}/{len(chunks)}")
            tmp_path = Path(audio_path).parent / f"_chunk_{i}.mp3"
            chunk.export(str(tmp_path), format="mp3", bitrate="128k")

            try:
                with open(tmp_path, "rb") as f:
                    result = client.audio.transcriptions.create(
                        file=(tmp_path.name, f.read()),
                        model=GROQ_MODEL,
                        prompt=prompt,
                        language=language,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                    )
                for s in result.segments or []:
                    all_segments.append({
                        "start": s.start + time_offset,
                        "end": s.end + time_offset,
                        "text": s.text,
                    })
            finally:
                tmp_path.unlink(missing_ok=True)

            time_offset += len(chunk) / 1000.0

        return all_segments


class FasterWhisperBackend(TranscribeBackend):
    name = "faster-whisper"

    def transcribe(self, audio_path, prompt, language):
        from faster_whisper import WhisperModel

        model = WhisperModel("large-v3", device="auto", compute_type="auto")
        segs, _info = model.transcribe(
            audio_path, language=language, initial_prompt=prompt
        )
        return [{"start": s.start, "end": s.end, "text": s.text} for s in segs]


class OpenAIWhisperBackend(TranscribeBackend):
    name = "OpenAI Whisper (CPU)"

    def transcribe(self, audio_path, prompt, language):
        import whisper

        model = whisper.load_model("turbo")
        result = model.transcribe(
            audio_path, language=language, initial_prompt=prompt, verbose=False
        )
        return result.get("segments", [])


# ── Backend detection ───────────────────────────────────────────────

BACKENDS = {
    "mlx": MLXBackend,
    "groq": GroqBackend,
    "faster_whisper": FasterWhisperBackend,
    "openai_whisper": OpenAIWhisperBackend,
}


def detect_backend(config):
    """Return the best available backend, respecting config preference."""
    preferred = config.get("backend", "")
    if preferred and preferred in BACKENDS:
        return BACKENDS[preferred]()

    # Auto-detect priority order
    import platform as _platform

    if sys.platform == "darwin" and _platform.machine() == "arm64":
        try:
            import mlx_whisper  # noqa: F401
            return MLXBackend()
        except ImportError:
            pass

    if os.environ.get("GROQ_API_KEY"):
        try:
            import groq  # noqa: F401
            return GroqBackend()
        except ImportError:
            pass

    try:
        import faster_whisper  # noqa: F401
        return FasterWhisperBackend()
    except ImportError:
        pass

    try:
        import whisper  # noqa: F401
        return OpenAIWhisperBackend()
    except ImportError:
        pass

    print("❌ No transcription backend available.")
    print("   Install one of: pip install mlx-whisper / groq / faster-whisper / openai-whisper")
    sys.exit(1)


# ── Helpers ─────────────────────────────────────────────────────────

def sanitize_dirname(name):
    name = re.sub(r'[/\\:*?"<>|]', "-", name)
    return re.sub(r"\s+", "-", name.strip())


def format_timestamp(seconds):
    h, remainder = divmod(int(seconds), 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"


def build_prompt(context=None):
    if context:
        return f"{BASE_PROMPT}本次會議相關資訊：{context}"
    return BASE_PROMPT


def open_file_cross_platform(filepath):
    """Open a file with the system default application."""
    import subprocess

    if sys.platform == "darwin":
        subprocess.Popen(["open", filepath])
    elif sys.platform == "win32":
        os.startfile(filepath)
    else:
        subprocess.Popen(["xdg-open", filepath])


# ── Main transcription flow ─────────────────────────────────────────

def transcribe_files(files, name, context, language, config, force=False):
    backend = detect_backend(config)
    replacements = load_replacements(config)

    output_base = config.get("output_base", "./transcripts")
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    dir_name = f"{date_prefix}_{sanitize_dirname(name)}"
    output_dir = Path(output_base) / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = output_dir / ".raw"
    raw_dir.mkdir(exist_ok=True)

    output_file = output_dir / "raw-transcript.md"

    if output_file.exists() and not force:
        print(f"⚠️  已存在：{output_file}，加 --force 覆蓋")
        return str(output_file)

    # Resolve to absolute paths (colons in macOS paths confuse ffmpeg)
    files = [str(Path(fp).resolve()) for fp in files]

    # Validate files
    for fp in files:
        if not os.path.exists(fp):
            print(f"❌ 檔案不存在：{fp}")
            return None

    # Calculate total duration estimate (from file size)
    total_size_mb = sum(os.path.getsize(f) for f in files) / (1024 * 1024)

    print(f"\n🎙️  轉錄中：{name}")
    print(f"   🔧 使用：{backend.name}")
    if len(files) > 1:
        print(f"   📁 共 {len(files)} 個檔案")
    else:
        print(f"   🔊 檔案：{files[0]}")
    print(f"   📦 大小：{total_size_mb:.1f} MB")
    if context:
        print(f"   📝 Context：{context}")
    print()

    start_time = time.time()
    prompt = build_prompt(context)

    # Transcribe each file, merge segments
    all_segments = []
    time_offset = 0.0
    file_boundaries = []

    for file_idx, audio_path in enumerate(files):
        if file_idx > 0:
            file_boundaries.append((len(all_segments), Path(audio_path).name))
            print(f"   ▶ 檔案 {file_idx + 1}/{len(files)}: {Path(audio_path).name}")

        segments = backend.transcribe(audio_path, prompt, language)

        for seg in segments:
            seg["start"] += time_offset
            seg["end"] += time_offset
            all_segments.append(seg)

        if all_segments:
            time_offset = all_segments[-1]["end"]

    elapsed = time.time() - start_time
    duration_min = round(time_offset / 60, 1)

    # Post-processing: S2T conversion → replacements → hallucination cleanup
    all_segments = convert_s2t(all_segments, language)
    all_segments = post_process_segments(all_segments, replacements)

    # Build raw-transcript.md
    lines = [
        f"# {name} — 逐字稿",
        f"> 📅 {date_prefix} ｜ ⏱ {duration_min} 分鐘",
        f"> 🔧 {backend.name} ｜ 轉錄耗時：{elapsed:.0f} 秒",
    ]
    if context:
        lines.append(f"> 📝 Context：{context}")
    if len(files) > 1:
        filenames = ", ".join(Path(f).name for f in files)
        lines.append(f"> 📁 來源：{filenames}")
    lines.extend(["", "---", ""])

    boundary_at = {idx: fname for idx, fname in file_boundaries}
    for seg_idx, seg in enumerate(all_segments):
        if seg_idx in boundary_at:
            part_num = list(boundary_at.keys()).index(seg_idx) + 2
            lines.extend(["", f"--- [📁 片段 {part_num}: {boundary_at[seg_idx]}] ---", ""])
        ts = format_timestamp(seg["start"])
        text = seg["text"].strip()
        if text:
            lines.append(f"[{ts}] {text}")
    lines.append("")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Print results as JSON for Claude to parse
    result = {
        "status": "ok",
        "output_dir": str(output_dir),
        "raw_transcript": str(output_file),
        "backend": backend.name,
        "elapsed_sec": round(elapsed),
        "duration_min": duration_min,
        "segments": len(all_segments),
        "replacements_applied": len(replacements),
        "files_count": len(files),
    }
    print(json.dumps(result, ensure_ascii=False))
    return str(output_file)


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Universal Transcription")
    parser.add_argument(
        "--file", nargs="+", metavar="PATH", required=False,
        help="Audio/video file path(s)",
    )
    parser.add_argument("--name", type=str, help="Output name")
    parser.add_argument("--context", type=str, default="", help="Context keywords")
    parser.add_argument("--language", type=str, help="Language (default from config)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing")
    parser.add_argument("--check", action="store_true", help="Print detected backend and exit")
    args = parser.parse_args()

    config = load_config()

    if args.check:
        backend = detect_backend(config)
        print(json.dumps({"backend": backend.name}, ensure_ascii=False))
        return

    if not args.file:
        parser.print_help()
        return

    name = args.name or Path(args.file[0]).stem
    language = args.language or config.get("default_language", "zh")

    transcribe_files(args.file, name, args.context, language, config, args.force)


if __name__ == "__main__":
    main()
