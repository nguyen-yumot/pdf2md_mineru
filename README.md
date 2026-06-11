# pdf2md-mineru

Convert PDFs (and other documents) to Markdown using [MinerU](https://github.com/opendatalab/MinerU).

## Requirements

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) for dependency and environment management

## Quick start

Set up the environment, then convert your first PDF:

```bash
uv sync                                       # install dependencies into .venv
uv run main.py downloads/example.pdf
```

`uv sync` builds the virtual environment from `pyproject.toml` and `uv.lock`. You can skip it — any `uv run` command syncs first automatically — but running it once up front makes the (sizable) MinerU model download explicit.

## Setup on a new computer

```bash
brew install uv                  # or: curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/nguyen-yumot/pdf2md_mineru.git && cd pdf2md_mineru
uv sync                          # exact environment from uv.lock (Python included)
uv run main.py some.pdf          # first run downloads ~5 GB of models, then converts
```

Notes:

- **Models are not in the repo.** MinerU downloads them to `~/.cache/huggingface/` automatically on first conversion (internet required, allow ~20 GB free disk per upstream guidance). To pre-fetch them explicitly: `uv run mineru-models-download`.
- **Match the memory setting to the machine.** `main.py` defaults `MINERU_VIRTUAL_VRAM_SIZE=16`, sized for a 32 GB Mac. On a 16 GB machine, `export MINERU_VIRTUAL_VRAM_SIZE=8`; with 64 GB or more, try `24`–`32`.
- **Hardware**: the MLX fast path needs Apple Silicon and macOS ≥ 14. On Intel Macs or Linux, MinerU falls back to transformers/CUDA/CPU automatically — same commands, different speed.

## Converting documents

`main.py` is a thin wrapper around the `mineru` CLI with Mac-friendly defaults (see [Performance on Mac](#performance-on-mac)):

```bash
uv run main.py downloads/example.pdf                  # output to downloads/mineru/
uv run main.py downloads/example.pdf -o output/       # custom output dir
uv run main.py scans/ -l japan                        # batch a directory, Japanese OCR
uv run main.py downloads/example.pdf -b pipeline      # extra args pass through to mineru
```

Input may be a pdf, image, `docx`/`pptx`/`xlsx` file, or a directory to batch-convert everything inside it. You can also call `uv run mineru -p <input> -o <output>` directly — `main.py` just adds the defaults below.

### Output

MinerU writes results to `<output>/<filename>/<backend>/`, for example:

```
downloads/mineru/example/hybrid_auto/
├── example.md                 # the Markdown output
├── images/                    # extracted figures, referenced by the Markdown
├── example_layout.pdf         # layout-annotated source for inspection
└── example_content_list.json  # structured content (text, tables, formulas)
```

### Common options

| Flag | Description |
| --- | --- |
| `-p, --path` | Input file or directory (pdf, image, docx, pptx, xlsx) — required |
| `-o, --output` | Output directory — required |
| `-m, --method` | `auto` (default), `txt`, or `ocr` |
| `-l, --lang` | OCR language hint, e.g. `en`, `ch`, `japan` (default `ch`) |
| `-s, --start` / `-e, --end` | Start/end page (0-indexed) |
| `-f, --formula` | Enable formula parsing (default `True`) |
| `-t, --table` | Enable table parsing (default `True`) |

Run `uv run mineru --help` for the full list.

## Performance on Mac

On Apple Silicon, MinerU already auto-detects the best compute paths — no configuration needed for quality:

- **Device**: MPS (Metal) is selected automatically by PyTorch.
- **VLM engine**: the default `hybrid-auto-engine` backend resolves to **MLX** (`mlx-vlm`) on Apple Silicon, the highest-quality option.

There is one gap: MinerU's VRAM auto-detection has no MPS branch, so on Mac it assumes **1 GB** and runs with the smallest batch sizes (`batch_ratio = 1`). `main.py` fixes this by defaulting `MINERU_VIRTUAL_VRAM_SIZE=16`, which yields `batch_ratio = 8` on a 32 GB machine while leaving headroom for the MLX model and macOS.

Tune via environment variables (exports override `main.py`'s defaults):

```bash
export MINERU_VIRTUAL_VRAM_SIZE=24   # faster; use when not multitasking
export MINERU_VIRTUAL_VRAM_SIZE=12   # safer; heavy multitasking or less RAM
export MINERU_HYBRID_BATCH_RATIO=8   # or set the batch ratio directly
```

Other knobs:

- **Language**: `main.py` defaults the OCR hint to `en` (MinerU's own default is `ch`). Pass `-l japan` for Japanese documents — the `en` model is Latin-only and cannot read kana/kanji, while `japan` covers both Japanese and English text.
- **VLM OCR for Japanese scans**: in the hybrid backend, scanned pages are OCR'd by the VLM only when the language is `ch` or `en`; with `-l japan` MinerU falls back to the classic OCR model. Since the VLM is multilingual, forcing it on can improve quality for scanned Japanese documents:

  ```bash
  MINERU_FORCE_VLM_OCR_ENABLE=1 uv run main.py scan.pdf -l japan
  ```

  Experimental — compare the output against a normal run before adopting it. Irrelevant for digital-born PDFs with a text layer.
- **Speed over quality**: `-b pipeline` uses the classic CV pipeline — faster and CPU-capable, but less accurate than the default hybrid backend (~85+ vs ~95+ on OmniDocBench, per upstream).

## Updating dependencies

Upgrade everything to the newest versions allowed by `pyproject.toml`:

```bash
uv lock --upgrade   # re-resolve uv.lock
uv sync             # install the updates
```

To upgrade only MinerU, use `uv lock --upgrade-package mineru` instead. Confirm the result with `uv run mineru --version`.

## Project layout

```
main.py          Converter entry point (mineru CLI wrapper with Mac defaults)
pyproject.toml   Project metadata and dependencies (mineru[all])
uv.lock          Pinned dependency versions
downloads/       Input documents and MinerU output
```
