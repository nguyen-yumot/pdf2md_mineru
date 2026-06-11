"""Convert PDFs to Markdown with MinerU, tuned for Apple Silicon Macs.

MinerU's VRAM auto-detection has no MPS branch, so on Mac it assumes 1 GB
and runs with the smallest batch sizes. This wrapper sets a sane default
(MINERU_VIRTUAL_VRAM_SIZE=16) before invoking the mineru CLI, and defaults
the OCR language hint to English instead of Chinese.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Defaults applied via os.environ.setdefault, so exported env vars win.
ENV_DEFAULTS = {
    # M1 Max has 32 GB unified memory; 16 -> batch_ratio 8 with headroom
    # for the MLX VLM and macOS. Export a different value to override.
    "MINERU_VIRTUAL_VRAM_SIZE": "16",
}


def find_mineru() -> str | None:
    """Locate the mineru CLI next to the running interpreter, else on PATH."""
    venv_mineru = Path(sys.executable).parent / "mineru"
    if venv_mineru.is_file():
        return str(venv_mineru)
    return shutil.which("mineru")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        # No abbreviations: unknown long flags must pass through to mineru,
        # not get silently captured by --output/--lang prefix matching.
        allow_abbrev=False,
        epilog="Extra arguments are passed through to the mineru CLI "
        "(e.g. -b pipeline, -s/-e page ranges). See: uv run mineru --help",
    )
    parser.add_argument("input", help="input file (pdf, image, docx, pptx, xlsx) or directory")
    parser.add_argument("-o", "--output", default="downloads/mineru", help="output directory (default: %(default)s)")
    # 'en' is Latin-only; pass -l japan for Japanese documents.
    parser.add_argument("-l", "--lang", default="en", help="OCR language hint (default: %(default)s)")
    args, extra = parser.parse_known_args()

    if not Path(args.input).exists():
        parser.error(f"input path does not exist: {args.input}")

    mineru = find_mineru()
    if mineru is None:
        parser.error("mineru CLI not found; run via `uv run main.py` so the project venv is used")

    for key, value in ENV_DEFAULTS.items():
        os.environ.setdefault(key, value)

    cmd = [mineru, "-p", args.input, "-o", args.output, "-l", args.lang, *extra]
    try:
        return subprocess.run(cmd).returncode
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
