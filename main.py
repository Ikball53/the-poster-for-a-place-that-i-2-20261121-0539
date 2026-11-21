"""VELMORA poster entry: copy the bundled PNG to the output directory."""

import os
import pathlib
import shutil
import sys

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DEFAULT_OUTPUT_DIR = "/output"
OUTPUT_ENV_VAR = "MAKEFUN_OUTPUT_DIR"
SOURCE_NAME = "entry.png"
OUTPUT_NAME = "entry.png"


def source_path() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve().parent
    candidate = here / SOURCE_NAME
    if candidate.is_file():
        return candidate
    fallback = pathlib.Path.cwd() / SOURCE_NAME
    return fallback


def looks_like_png(path: pathlib.Path) -> bool:
    with path.open("rb") as handle:
        head = handle.read(len(PNG_SIGNATURE))
    return head == PNG_SIGNATURE


def output_directory() -> pathlib.Path:
    configured = os.environ.get(OUTPUT_ENV_VAR, "").strip()
    target = configured if configured else DEFAULT_OUTPUT_DIR
    return pathlib.Path(target).expanduser()


def verify_copied_bytes(source: pathlib.Path, dest: pathlib.Path) -> bool:
    if dest.stat().st_size != source.stat().st_size:
        return False
    return looks_like_png(dest)


def main() -> int:
    src = source_path()
    if not src.is_file():
        print(f"missing bundled image: {src}", file=sys.stderr)
        return 1
    if not looks_like_png(src):
        print("bundled image is not a PNG", file=sys.stderr)
        return 1
    dest_dir = output_directory()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / OUTPUT_NAME
    shutil.copyfile(src, dest)
    if not verify_copied_bytes(src, dest):
        print("copied image failed verification", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
