#!/usr/bin/env python3
"""
Cross-platform OCR module.

Usage:
  python3 ocr-universal.py image1.png image2.jpg ...
  python3 ocr-universal.py --dir slides/
  python3 ocr-universal.py --check  (print detected OCR backend)

Output: JSON with { "results": [{"file": "...", "text": "..."}] }
"""
import argparse
import json
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".heic"}


# ── OCR Backends ────────────────────────────────────────────────────

class OCRBackend(ABC):
    name: str

    @abstractmethod
    def ocr(self, image_path: str) -> str:
        """Return extracted text from image."""
        ...


class MacOCR(OCRBackend):
    """macOS built-in Vision framework via swift CLI."""
    name = "macOS Vision"

    def ocr(self, image_path: str) -> str:
        # Use the built-in screencapture/Vision framework via a small Swift script
        swift_code = f'''
import Vision
import AppKit

let url = URL(fileURLWithPath: "{image_path}")
guard let image = NSImage(contentsOf: url),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {{
    exit(1)
}}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hant", "zh-Hans", "en"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage)
try handler.perform([request])

let text = (request.results ?? []).compactMap {{ $0.topCandidates(1).first?.string }}.joined(separator: "\\n")
print(text)
'''
        try:
            result = subprocess.run(
                ["swift", "-"],
                input=swift_code,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""


class WindowsOCR(OCRBackend):
    """Windows 10+ built-in WinRT OCR via PowerShell."""
    name = "Windows OCR"

    def ocr(self, image_path: str) -> str:
        # Normalize path for Windows
        win_path = image_path.replace("/", "\\")
        ps_script = f'''
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]

$file = [Windows.Storage.StorageFile]::GetFileFromPathAsync("{win_path}").GetAwaiter().GetResult()
$stream = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read).GetAwaiter().GetResult()
$decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream).GetAwaiter().GetResult()
$bitmap = $decoder.GetSoftwareBitmapAsync().GetAwaiter().GetResult()

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$result = $engine.RecognizeAsync($bitmap).GetAwaiter().GetResult()
Write-Output $result.Text
'''
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""


class TesseractOCR(OCRBackend):
    """Tesseract OCR (cross-platform, requires installation)."""
    name = "Tesseract"

    def ocr(self, image_path: str) -> str:
        try:
            result = subprocess.run(
                ["tesseract", image_path, "stdout", "-l", "chi_tra+eng"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""


# ── Backend detection ───────────────────────────────────────────────

def detect_ocr_backend() -> OCRBackend:
    if sys.platform == "darwin":
        return MacOCR()
    if sys.platform == "win32":
        return WindowsOCR()
    # Linux or fallback
    import shutil
    if shutil.which("tesseract"):
        return TesseractOCR()
    # No local OCR available — caller should use Claude Vision
    return None


def convert_tiff_to_png(image_path: str) -> str:
    """Convert TIFF to PNG if needed (TIFF is common from screenshots)."""
    p = Path(image_path)
    if p.suffix.lower() not in (".tiff", ".tif"):
        return image_path

    png_path = p.with_suffix(".png")
    if sys.platform == "darwin":
        subprocess.run(["sips", "-s", "format", "png", str(p), "--out", str(png_path)],
                       capture_output=True, timeout=10)
    else:
        # Use PIL if available, otherwise skip
        try:
            from PIL import Image
            img = Image.open(image_path)
            img.save(str(png_path), "PNG")
        except ImportError:
            return image_path
    return str(png_path) if png_path.exists() else image_path


# ── Main ────────────────────────────────────────────────────────────

def ocr_images(paths: list[str]) -> list[dict]:
    backend = detect_ocr_backend()
    results = []

    for path in paths:
        path = convert_tiff_to_png(path)

        if backend:
            text = backend.ocr(path)
        else:
            text = ""

        results.append({
            "file": path,
            "text": text,
            "backend": backend.name if backend else "none",
            "needs_claude_vision": len(text.strip()) < 10,
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Cross-platform OCR")
    parser.add_argument("images", nargs="*", help="Image file paths")
    parser.add_argument("--dir", type=str, help="Directory of images")
    parser.add_argument("--check", action="store_true", help="Print detected backend")
    args = parser.parse_args()

    if args.check:
        backend = detect_ocr_backend()
        name = backend.name if backend else "none (use Claude Vision)"
        print(json.dumps({"ocr_backend": name}, ensure_ascii=False))
        return

    paths = list(args.images or [])
    if args.dir:
        d = Path(args.dir)
        paths.extend(
            str(f) for f in sorted(d.iterdir())
            if f.suffix.lower() in IMAGE_EXTENSIONS
        )

    if not paths:
        parser.print_help()
        return

    results = ocr_images(paths)
    print(json.dumps({"results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
