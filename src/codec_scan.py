import json
import os
import subprocess
import argparse

from rich import print
from rich.table import Table

# Configure accepted formats for direct play on NVIDIA Shield
SUPPORTED_VIDEO = {"h264", "hevc", "vp8", "vp9", "mpeg1", "mpeg2", "h263", "mjpeg", "mpeg4", "vc1"}
SUPPORTED_AUDIO = {"aac", "ac3", "eac3", "dts", "flac", "mp3", "opus", "vorbis"}
SUPPORTED_SUBS = {"subrip", "ass", "dvbsub", "dvdsub"}
SUPPORTED_CONTAINERS = {"matroska", "mov", "mp4", "m2ts", "mpegts", "avi", "asf", "webm"}


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


def analyze(path, ignore_subs=False):
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

    if not ignore_subs and subtitle_codecs and not subtitle_codecs <= SUPPORTED_SUBS:
        issues.append(f"Subtitles: {', '.join(subtitle_codecs)}")

    return (False if issues else True), ", ".join(issues)


def scan_directory(root, ignore_subs=False):
    table = Table(title="Media Compatibility Report (NVIDIA Shield + Jellyfin)")
    table.add_column("File", style="bold")
    table.add_column("Direct Play?", justify="center")
    table.add_column("Issues", style="red")

    total_files = 0
    direct_play_files = 0

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.lower().endswith((".mkv", ".mp4", ".mov")):
                total_files += 1
                full_path = os.path.join(dirpath, f)
                is_direct, reason = analyze(full_path, ignore_subs)
                if is_direct:
                    direct_play_files += 1
                table.add_row(
                    f, "[green]Yes[/green]" if is_direct else "[red]No[/red]", reason
                )

    print(table)
    
    if total_files > 0:
        direct_play_percent = (direct_play_files / total_files) * 100
        transcode_percent = 100 - direct_play_percent
        print("\n[bold]Summary:[/bold]")
        print(f"Total files scanned: {total_files}")
        print(f"Direct Play: [green]{direct_play_files} ({direct_play_percent:.1f}%)[/green]")
        print(f"Needs Transcode: [red]{total_files - direct_play_files} ({transcode_percent:.1f}%)[/red]")
        if ignore_subs:
            print("[yellow]Note: Subtitle compatibility issues were ignored[/yellow]")
    else:
        print("\n[yellow]No media files found in the specified directory.[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="Scan media files for NVIDIA Shield compatibility")
    parser.add_argument("directory", help="Directory containing media files to scan")
    parser.add_argument("--ignore-subs", action="store_true", help="Ignore subtitle compatibility issues")
    
    args = parser.parse_args()
    scan_directory(args.directory, args.ignore_subs)
