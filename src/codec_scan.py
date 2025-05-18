import json
import os
import subprocess

from rich import print
from rich.table import Table

# Configure accepted formats for direct play on NVIDIA Shield
SUPPORTED_VIDEO = {"h264", "hevc"}
SUPPORTED_AUDIO = {"aac", "ac3", "eac3"}
SUPPORTED_SUBS = {"subrip", "ass"}
SUPPORTED_CONTAINERS = {"matroska", "mov", "mp4"}


def probe_file(path):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                path,
            ],
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[red]Failed to probe {path}: {e}[/red]")
        return None


def analyze(path):
    data = probe_file(path)
    if not data:
        return False, "Probe error"

    format_name = data.get("format", {}).get("format_name", "")
    container = format_name.split(",")[0]  # take the first format name

    video_codecs = {
        s["codec_name"] for s in data["streams"] if s["codec_type"] == "video"
    }
    audio_codecs = {
        s["codec_name"] for s in data["streams"] if s["codec_type"] == "audio"
    }
    subtitle_codecs = {
        s["codec_name"] for s in data["streams"] if s["codec_type"] == "subtitle"
    }

    # Determine compatibility
    issues = []

    if container not in SUPPORTED_CONTAINERS:
        issues.append(f"Container: {container}")

    if not video_codecs & SUPPORTED_VIDEO:
        issues.append(f"Video: {', '.join(video_codecs)}")

    if not audio_codecs & SUPPORTED_AUDIO:
        issues.append(f"Audio: {', '.join(audio_codecs)}")

    if subtitle_codecs and not subtitle_codecs <= SUPPORTED_SUBS:
        issues.append(f"Subtitles: {', '.join(subtitle_codecs)}")

    return (False if issues else True), ", ".join(issues)


def scan_directory(root):
    table = Table(title="Media Compatibility Report (NVIDIA Shield + Jellyfin)")
    table.add_column("File", style="bold")
    table.add_column("Direct Play?", justify="center")
    table.add_column("Issues", style="red")

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.lower().endswith((".mkv", ".mp4", ".mov")):
                full_path = os.path.join(dirpath, f)
                is_direct, reason = analyze(full_path)
                table.add_row(
                    f, "[green]Yes[/green]" if is_direct else "[red]No[/red]", reason
                )

    print(table)


def main():
    import sys

    if len(sys.argv) != 2:
        print("[yellow]Usage: python codec_scan.py /path/to/media[/yellow]")
        exit(1)

    scan_directory(sys.argv[1])
