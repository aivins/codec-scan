# Just a quick script to scan some codecs

Needs python 3.10+ and needs ffmpeg installed on PATH.

```
pip install https://github.com/aivins/codec-scan/archive/refs/heads/main.tar.gz

> codec-scan --help

usage: codec-scan [-h] [--ignore-subs] directory

Scan media files for NVIDIA Shield compatibility

positional arguments:
  directory      Directory containing media files to scan

options:
  -h, --help     show this help message and exit
  --ignore-subs  Ignore subtitle compatibility issues
``` 

Examples:

`codec-scan /mnt/media/movies`

This might even work, but not tested:

`codec-scan C:/stuff/movies`


