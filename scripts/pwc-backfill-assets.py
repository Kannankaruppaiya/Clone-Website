#!/usr/bin/env python3
"""Download a pwc capture's images and fonts (and optionally stylesheets).

pwc's extractor fetches assets with Playwright's APIRequestContext, which does
not use HTTPS_PROXY. Behind a proxy (e.g. Claude Code cloud sessions) every
download fails silently and the clone ships with hotlinked or missing assets.
This re-downloads them with httpx (a pwc dependency, which honours the proxy)
and writes `downloaded_resources` in the shape pwc's own downloader uses, so
`pwc assemble` copies and localizes them as usual.

With --with-css it also stores the external stylesheets in `css.json`, which
gives `pwc section` real `css_rules` after the next `pwc plan`. pwc then also
writes the source's entire stylesheet to public/theme.css and links it from
index.html on every `pwc assemble`, i.e. the clone ships the original CSS.

Usage: pwc-backfill-assets.py <source_id> [--with-css]    (after `pwc extract`)
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
from core.extractor.storage import default_storage_root

SUBDIRS = {"images": ("assets/images", "image"), "fonts": ("assets/fonts", "font")}


def fetch(client: httpx.Client, url: str, failed: list):
    try:
        resp = client.get(url)
        resp.raise_for_status()
        return resp
    except httpx.HTTPError as exc:
        failed.append((url, str(exc)))
        return None


def backfill_files(client: httpx.Client, src: Path, assets: dict, failed: list) -> dict:
    out = {"images": [], "fonts": [], "scripts": [], "stylesheets": [], "videos": []}
    used = set()
    for kind, (subdir, rtype) in SUBDIRS.items():
        for asset in assets.get(kind) or []:
            url = asset.get("url", "")
            if not url.startswith(("http://", "https://")):
                continue
            resp = fetch(client, url, failed)
            if resp is None:
                continue
            name = re.sub(r"[^A-Za-z0-9._-]", "_", urlparse(url).path.split("/")[-1] or "res")
            rel, n = f"{subdir}/{name}", 1
            while rel in used:
                stem, _, ext = name.rpartition(".")
                rel, n = f"{subdir}/{stem}-{n}.{ext}", n + 1
            used.add(rel)
            (src / rel).parent.mkdir(parents=True, exist_ok=True)
            (src / rel).write_bytes(resp.content)
            out[kind].append({
                "url": url, "type": rtype, "content": None, "size": len(resp.content),
                "mime_type": resp.headers.get("content-type", ""), "filename": name, "saved_path": rel,
            })
    return out


def backfill_css(client: httpx.Client, src: Path, assets: dict, failed: list) -> int:
    """Store external stylesheets in css.json, where `pwc section` derives css_rules."""
    css_path = src / "css.json"
    css = json.loads(css_path.read_text(encoding="utf-8")) if css_path.is_file() else {}
    sheets = css.get("stylesheets") or []
    have = {s.get("url") for s in sheets}
    added = 0
    for asset in assets.get("stylesheets") or []:
        url = asset.get("url", "")
        if not url.startswith(("http://", "https://")) or url in have:
            continue
        resp = fetch(client, url, failed)
        if resp is None:
            continue
        sheets.append({"url": url, "content": resp.text, "is_inline": False})
        added += 1
    css["stylesheets"] = sheets
    css_path.write_text(json.dumps(css, ensure_ascii=False, indent=2), encoding="utf-8")
    return added


def main(source_id: str, with_css: bool) -> int:
    src = default_storage_root() / source_id
    manifest_path = src / "manifest.json"
    if not manifest_path.is_file():
        print(f"no capture at {src}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = manifest.get("assets") or {}
    failed: list = []

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        downloaded = backfill_files(client, src, assets, failed)
        added_css = backfill_css(client, src, assets, failed) if with_css else 0

    manifest["downloaded_resources"] = downloaded
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = {k: len(v) for k, v in downloaded.items() if v}
    if with_css:
        counts["stylesheets"] = added_css
    print(json.dumps({"ok": not failed, "downloaded": counts, "failed": failed}, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--with-css"]
    if len(args) != 1:
        sys.exit(__doc__)
    sys.exit(main(args[0], "--with-css" in sys.argv[1:]))
