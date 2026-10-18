#!/usr/bin/env python3
"""Prepare a PDF or image for multimodal extraction by OpenCode.

The script rasterizes each PDF page to an image, extracts the native text layer
when present, and writes a JSON manifest to disk. Cache files always live inside
the folder that contains the source document, and a relative output path is
anchored to that folder too, so nothing is written to the current working
directory.

It is intentionally launcher-agnostic: it does not assume it was invoked as
``python3``. Callers should probe ``python3`` -> ``python`` -> ``py -3``.

Usage:
    python prepare_doc.py <input_file> [output_md] [--manifest PATH] [--max-dim N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import pymupdf as fitz  # PyMuPDF >= 1.24 (new canonical name)
except ImportError:
    try:
        import fitz  # PyMuPDF legacy module name
    except ImportError:
        sys.stderr.write(
            "ERROR: PyMuPDF is not installed.\n"
            "Install it with:  python -m pip install pymupdf\n"
        )
        raise SystemExit(1)

SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
CACHE_DIR_NAME = ".doc2md_cache"


def _reconfigure_stdout() -> None:
    """Force UTF-8 output so Windows consoles do not raise UnicodeEncodeError."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def resolve_output_md(src: Path, custom_out: str | None) -> Path:
    """Resolve the output Markdown path.

    Relative paths (including those with sub-directories) are anchored to the
    document's own folder (``src.parent``), never to the current working
    directory, so output cannot accidentally land in the workspace root.
    ``..`` segments are resolved normally and may leave the folder on purpose.
    Absolute paths are honoured as given.
    """
    if not custom_out or not custom_out.strip():
        return src.with_suffix(".md")
    candidate = Path(custom_out.strip()).expanduser()
    if candidate.is_absolute():
        return candidate
    return (src.parent / candidate).resolve()


def render_pdf(pdf_path: Path, cache_dir: Path, max_dim: int = 2000) -> list[dict]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    pages: list[dict] = []
    doc = fitz.open(str(pdf_path))
    try:
        if getattr(doc, "needs_pass", False):
            raise ValueError(
                f"{pdf_path.name} is password-protected; decrypt it first"
            )
        for idx, page in enumerate(doc, start=1):
            rect = page.rect
            longest_edge = max(rect.width, rect.height) or 1.0
            zoom = min(max_dim / longest_edge, 3.0)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)

            img_path = cache_dir / f"page_{idx:03d}.png"
            pix.save(str(img_path))

            native_text = page.get_text("text").strip()
            txt_path = None
            if native_text:
                txt_path = cache_dir / f"page_{idx:03d}_native.txt"
                txt_path.write_text(native_text, encoding="utf-8")

            pages.append(
                {
                    "page": idx,
                    "image_path": img_path.as_posix(),
                    "native_text_path": txt_path.as_posix() if txt_path else None,
                    "width": pix.width,
                    "height": pix.height,
                }
            )
    finally:
        doc.close()
    return pages


def build_manifest(args: argparse.Namespace) -> dict:
    src = Path(args.input_file).expanduser().resolve()
    if not src.exists():
        sys.stderr.write(f"ERROR: File not found: {src}\n")
        raise SystemExit(1)
    if not src.is_file():
        sys.stderr.write(f"ERROR: Not a file: {src}\n")
        raise SystemExit(1)

    project_doc_dir = src.parent
    target_md = resolve_output_md(src, args.output_md)

    ext = src.suffix.lower()
    cache_dir: Path | None = None

    if ext == ".pdf":
        cache_dir = project_doc_dir / CACHE_DIR_NAME / src.stem
        try:
            pages = render_pdf(src, cache_dir, max_dim=args.max_dim)
        except Exception as exc:
            sys.stderr.write(f"ERROR: could not process PDF: {exc}\n")
            raise SystemExit(1)
        doc_type = "pdf"
    elif ext in SUPPORTED_IMAGES:
        pages = [
            {
                "page": 1,
                "image_path": src.as_posix(),
                "native_text_path": None,
                "width": None,
                "height": None,
            }
        ]
        doc_type = "image"
    else:
        sys.stderr.write(
            f"ERROR: Unsupported file format '{ext}'. "
            "Use PDF, PNG, JPG, JPEG, WEBP or GIF.\n"
        )
        raise SystemExit(1)

    return {
        "source_file": src.as_posix(),
        "project_folder": project_doc_dir.as_posix(),
        "target_markdown_file": target_md.as_posix(),
        "cache_dir": cache_dir.as_posix() if cache_dir is not None else None,
        "type": doc_type,
        "total_pages": len(pages),
        "pages": pages,
    }


def resolve_manifest_path(raw: str, manifest: dict) -> Path:
    if raw and raw.strip():
        candidate = Path(raw.strip()).expanduser()
        if candidate.is_absolute():
            return candidate
        return Path(manifest["project_folder"]) / candidate
    cache = manifest.get("cache_dir")
    if cache:
        return Path(cache) / "manifest.json"
    return Path(manifest["project_folder"]) / CACHE_DIR_NAME / "manifest.json"


def main() -> None:
    _reconfigure_stdout()

    parser = argparse.ArgumentParser(
        description="Rasterize a PDF or stage an image inside its project folder."
    )
    parser.add_argument("input_file", help="Path to the source PDF or image file")
    parser.add_argument(
        "output_md",
        nargs="?",
        default="",
        help="Optional output Markdown path or filename",
    )
    parser.add_argument(
        "--manifest",
        default="",
        help="Path where the JSON manifest is written (default: inside the cache dir)",
    )
    parser.add_argument(
        "--max-dim",
        type=int,
        default=2000,
        help="Maximum pixel dimension for the longest edge (default: 2000)",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Also print the manifest JSON to stdout (default: print only its path)",
    )
    args = parser.parse_args()

    if args.max_dim <= 0:
        sys.stderr.write("ERROR: --max-dim must be a positive integer\n")
        raise SystemExit(1)

    manifest = build_manifest(args)
    manifest_path = resolve_manifest_path(args.manifest, manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    Path(manifest["target_markdown_file"]).parent.mkdir(parents=True, exist_ok=True)

    if args.print_json:
        sys.stdout.write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(manifest_path.as_posix() + "\n")


if __name__ == "__main__":
    main()
