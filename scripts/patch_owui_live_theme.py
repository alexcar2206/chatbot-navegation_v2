#!/usr/bin/env python3
"""Hot-fix helper: patch a built index.html theme-color and splash CSS.

Canonical branding lives in src/app.html and static/*/custom.css.
Use this only against an already-deployed build (e.g. docker container)
without rebuilding. Palette: #0b4f6c / #e8f1f5 / #042a3a.
"""
from __future__ import annotations

import sys
from pathlib import Path

BRAND_PRIMARY = "#0b4f6c"
BRAND_SURFACE_LIGHT = "#e8f1f5"
BRAND_SURFACE_DARK = "#042a3a"


def patch_html(text: str) -> tuple[str, list[str]]:
    applied: list[str] = []

    replacements: list[tuple[str, str, str]] = [
        (
            'meta name="theme-color" content="#171717"',
            f'meta name="theme-color" content="{BRAND_PRIMARY}"',
            "default meta theme-color",
        ),
        (
            f'<meta name="theme-color" content="#171717" />',
            f'<meta name="theme-color" content="{BRAND_PRIMARY}" />',
            "default meta theme-color (self-closing)",
        ),
        # Already-branded older palette → current
        (
            'meta name="theme-color" content="#086178"',
            f'meta name="theme-color" content="{BRAND_PRIMARY}"',
            "legacy meta theme-color #086178",
        ),
        (
            f'<meta name="theme-color" content="#086178" />',
            f'<meta name="theme-color" content="{BRAND_PRIMARY}" />',
            "legacy meta theme-color #086178 (self-closing)",
        ),
        (
            "const THEME_DARK = '#171717';",
            f"const THEME_DARK = '{BRAND_PRIMARY}';",
            "THEME_DARK constant",
        ),
        (
            'const THEME_DARK = "#171717";',
            f'const THEME_DARK = "{BRAND_PRIMARY}";',
            "THEME_DARK constant (double quotes)",
        ),
        (
            "const THEME_LIGHT = '#ffffff';",
            f"const THEME_LIGHT = '{BRAND_SURFACE_LIGHT}';",
            "THEME_LIGHT constant",
        ),
        (
            'const THEME_LIGHT = "#ffffff";',
            f'const THEME_LIGHT = "{BRAND_SURFACE_LIGHT}";',
            "THEME_LIGHT constant (double quotes)",
        ),
        (
            "metaThemeColorTag.setAttribute('content', '#000000');",
            f"metaThemeColorTag.setAttribute('content', '{BRAND_SURFACE_DARK}');",
            "oled-dark meta theme-color",
        ),
        (
            'metaThemeColorTag.setAttribute("content", "#000000");',
            f'metaThemeColorTag.setAttribute("content", "{BRAND_SURFACE_DARK}");',
            "oled-dark meta theme-color (double quotes)",
        ),
        (
            "#splash-screen {\n\t\t\tbackground: #fff;",
            f"#splash-screen {{\n\t\t\tbackground: {BRAND_SURFACE_LIGHT};",
            "splash light background",
        ),
        (
            "#splash-screen {\n\t\t\tbackground: #ffffff;",
            f"#splash-screen {{\n\t\t\tbackground: {BRAND_SURFACE_LIGHT};",
            "splash light background (#ffffff)",
        ),
        (
            "html.dark #splash-screen {\n\t\t\tbackground: #000;",
            f"html.dark #splash-screen {{\n\t\t\tbackground: {BRAND_SURFACE_DARK};",
            "splash dark background",
        ),
        (
            "html.dark #splash-screen {\n\t\t\tbackground: #000000;",
            f"html.dark #splash-screen {{\n\t\t\tbackground: {BRAND_SURFACE_DARK};",
            "splash dark background (#000000)",
        ),
        # Upgrade older brand splash colors
        (
            "#splash-screen {\n\t\t\tbackground: #eef8f6;",
            f"#splash-screen {{\n\t\t\tbackground: {BRAND_SURFACE_LIGHT};",
            "legacy splash light #eef8f6",
        ),
        (
            "html.dark #splash-screen {\n\t\t\tbackground: #043944;",
            f"html.dark #splash-screen {{\n\t\t\tbackground: {BRAND_SURFACE_DARK};",
            "legacy splash dark #043944",
        ),
    ]

    for old, new, label in replacements:
        if old in text and old != new:
            text = text.replace(old, new)
            applied.append(label)
        elif new in text and old not in text:
            pass  # already patched

    # Fallback: theme-color JS literals when constants are inlined
    inline = [
        (
            "prefersDarkTheme ? '#171717' : '#ffffff'",
            f"prefersDarkTheme ? '{BRAND_PRIMARY}' : '{BRAND_SURFACE_LIGHT}'",
        ),
        (
            'prefersDarkTheme ? "#171717" : "#ffffff"',
            f'prefersDarkTheme ? "{BRAND_PRIMARY}" : "{BRAND_SURFACE_LIGHT}"',
        ),
        (
            "prefersDarkTheme ? '#086178' : '#eef8f6'",
            f"prefersDarkTheme ? '{BRAND_PRIMARY}' : '{BRAND_SURFACE_LIGHT}'",
        ),
        (
            'prefersDarkTheme ? "#086178" : "#eef8f6"',
            f'prefersDarkTheme ? "{BRAND_PRIMARY}" : "{BRAND_SURFACE_LIGHT}"',
        ),
        (f"setAttribute('content', '#171717')", f"setAttribute('content', '{BRAND_PRIMARY}')"),
        (f"setAttribute('content', '#ffffff')", f"setAttribute('content', '{BRAND_SURFACE_LIGHT}')"),
        (f"setAttribute('content', '#086178')", f"setAttribute('content', '{BRAND_PRIMARY}')"),
        (f"setAttribute('content', '#eef8f6')", f"setAttribute('content', '{BRAND_SURFACE_LIGHT}')"),
        (f"setAttribute('content', '#043944')", f"setAttribute('content', '{BRAND_SURFACE_DARK}')"),
    ]
    for old, new in inline:
        if old in text:
            text = text.replace(old, new)
            applied.append(f"inline: {old[:40]}...")

    return text, applied


SPLASH_CSS_BLOCK = f"""
/* Brand splash overrides (Chatbot Navegation / Miño-Sil) */
#splash-screen {{ background: {BRAND_SURFACE_LIGHT} !important; }}
html.dark #splash-screen {{ background: {BRAND_SURFACE_DARK} !important; }}
"""


def patch_custom_css(text: str) -> tuple[str, bool]:
    marker = "Brand splash overrides"
    if marker in text:
        # Refresh palette if an older block is present
        if BRAND_SURFACE_LIGHT in text and BRAND_SURFACE_DARK in text:
            return text, False
        # Replace known legacy block
        lines = text.splitlines(keepends=True)
        out: list[str] = []
        skipping = False
        changed = False
        for line in lines:
            if "Brand splash overrides" in line:
                skipping = True
                changed = True
                continue
            if skipping:
                if line.strip().startswith("html.dark #splash-screen") or (
                    line.strip().startswith("#splash-screen") and "background" in line
                ):
                    continue
                if line.strip() == "}" or line.strip().endswith("}"):
                    # end of a one-line or multi-line rule; keep skipping until block ends
                    if "html.dark" in "".join(out[-3:]) or "#splash-screen" in "".join(out[-5:]):
                        continue
                    skipping = False
                    continue
                if line.strip() == "" and changed:
                    skipping = False
                    continue
            out.append(line)
        text = "".join(out).rstrip() + "\n" + SPLASH_CSS_BLOCK
        return text, True
    return text.rstrip() + "\n" + SPLASH_CSS_BLOCK, True


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <index.html>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    original = path.read_text(encoding="utf-8")
    patched, applied = patch_html(original)
    if patched == original:
        print("WARN: no HTML replacements applied (file may already be patched or format differs)")
    else:
        path.write_text(patched, encoding="utf-8")
        print("HTML patches applied:")
        for item in applied:
            print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
