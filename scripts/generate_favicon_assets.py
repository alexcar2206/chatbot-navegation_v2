#!/usr/bin/env python3
"""Generate derived icon assets from static/favicon.png (canonical source).

Writes to static/static/ and backend/open_webui/static/ only.
Does not place derived PNGs next to the source in static/ root.
"""
import os
import shutil
import sys

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "static", "favicon.png")
SVG_SRC_CANDIDATES = [
    os.path.join(ROOT, "static", "static", "favicon.svg"),
    os.path.join(ROOT, "backend", "open_webui", "static", "favicon.svg"),
]
DIRS = [
    os.path.join(ROOT, "static", "static"),
    os.path.join(ROOT, "backend", "open_webui", "static"),
]

RESAMPLE = Image.Resampling.LANCZOS

PNG_SPECS = [
    ("favicon-96x96.png", 96),
    ("apple-touch-icon.png", 180),
    ("web-app-manifest-192x192.png", 192),
    ("web-app-manifest-512x512.png", 512),
    ("logo.png", 512),
    ("splash.png", 512),
    ("splash-dark.png", 512),
]

ICO_SIZES = [(16, 16), (32, 32), (48, 48)]

# Orphan derived assets previously written under static/ root (keep favicon.png).
STATIC_ROOT_ORPHANS = [
    "apple-touch-icon.png",
    "favicon-96x96.png",
    "favicon.ico",
    "logo.png",
    "splash-dark.png",
    "splash.png",
    "web-app-manifest-192x192.png",
    "web-app-manifest-512x512.png",
]


def file_size(path):
    return os.path.getsize(path)


def main():
    errors = []
    written = []
    removed = []

    if not os.path.isfile(SRC):
        errors.append(f"Source missing: {SRC}")
        print("\n".join(errors))
        sys.exit(1)

    with Image.open(SRC) as im:
        src_w, src_h = im.size
        print(f"Source: {SRC} ({src_w}x{src_h}, {file_size(SRC)} bytes)")

        generated = {}

        for name, size in PNG_SPECS:
            out = im.convert("RGBA").resize((size, size), RESAMPLE)
            generated[name] = out

        ico_base = im.convert("RGBA")
        generated["favicon.ico"] = ico_base

    for d in DIRS:
        os.makedirs(d, exist_ok=True)

    for d in DIRS:
        for name, size in PNG_SPECS:
            path = os.path.join(d, name)
            try:
                generated[name].save(path, format="PNG", optimize=True)
                written.append((path, f"{size}x{size} PNG", file_size(path)))
            except Exception as e:
                errors.append(f"{path}: {e}")

    for d in DIRS:
        path = os.path.join(d, "favicon.ico")
        try:
            generated["favicon.ico"].save(
                path,
                format="ICO",
                sizes=ICO_SIZES,
            )
            written.append((path, f"ICO {ICO_SIZES}", file_size(path)))
        except Exception as e:
            errors.append(f"{path}: {e}")

    for d in DIRS:
        dest = os.path.join(d, "favicon.png")
        try:
            shutil.copy2(SRC, dest)
            written.append((dest, "copy of source", file_size(dest)))
        except Exception as e:
            errors.append(f"{dest}: {e}")

    # Sync favicon.svg across destination dirs when present.
    svg_src = next((p for p in SVG_SRC_CANDIDATES if os.path.isfile(p)), None)
    if svg_src:
        for d in DIRS:
            dest = os.path.join(d, "favicon.svg")
            if os.path.abspath(svg_src) == os.path.abspath(dest):
                written.append((dest, "svg source (unchanged)", file_size(dest)))
                continue
            try:
                shutil.copy2(svg_src, dest)
                written.append((dest, "copy of favicon.svg", file_size(dest)))
            except Exception as e:
                errors.append(f"{dest}: {e}")
    else:
        print("WARN: no favicon.svg found to sync")

    static_root = os.path.join(ROOT, "static")
    for name in STATIC_ROOT_ORPHANS:
        path = os.path.join(static_root, name)
        if os.path.isfile(path):
            try:
                os.remove(path)
                removed.append(path)
            except Exception as e:
                errors.append(f"remove {path}: {e}")

    print("\n=== Files written ===")
    for path, desc, sz in written:
        print(f"{path}\t{desc}\t{sz} bytes")

    if removed:
        print("\n=== Orphans removed from static/ root ===")
        for path in removed:
            print(path)

    if errors:
        print("\n=== Errors ===")
        for e in errors:
            print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
