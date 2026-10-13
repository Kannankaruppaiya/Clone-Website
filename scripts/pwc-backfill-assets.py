#!/usr/bin/env python3
"""Download a pwc capture's images, fonts and stylesheets and record them.

pwc's extractor fetches assets with Playwright's APIRequestContext, which does
not use HTTPS_PROXY. Behind a proxy (e.g. Claude Code cloud sessions) every
download fails silently and the clone ships with hotlinked or missing assets.
This re-downloads them with httpx (a pwc dependency, which honours the proxy)
and writes `downloaded_resources` (images, fonts) and the external stylesheets in
`css.json` in the shapes pwc's own extractor uses, so `pwc section` returns the
real `css_rules` and `pwc assemble` copies and localizes the assets as usual.

Usage: pwc-backfill-assets.py <source_id>    (run after `pwc extract`)
"""
import json
import re
import sys
from urllib.parse import urlparse

import httpx
from core.extractor.storage import default_storage_root

SUBDIRS = {"images": ("assets/images", "image"), "fonts": ("assets/fonts", "font")}


def main(source_id: str) -> int:
    src = default_storage_root() / source_id
    manifest_path = src / "manifest.json"
    if not manifest_path.is_file():
        print(f"no capture at {src}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = manifest.get("assets") or {}
    out = {"images": [], "fonts": [], "scripts": [], "stylesheets": [], "videos": []}
    used, failed = set(), []

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for kind, (subdir, rtype) in SUBDIRS.items():
            for asset in assets.get(kind) or []:
                url = asset.get("url", "")
                if not url.startswith(("http://", "https://")):
                    continue
                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    failed.append((url, str(exc)))
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

        # External stylesheets go to css.json, where `pwc section` derives css_rules.
        css_path = src / "css.json"
        css = json.loads(css_path.read_text(encoding="utf-8")) if css_path.is_file() else {}
        sheets = css.get("stylesheets") or []
        have = {s.get("url") for s in sheets}
        added_css = 0
        for asset in assets.get("stylesheets") or []:
            url = asset.get("url", "")
            if not url.startswith(("http://", "https://")) or url in have:
                continue
            try:
                resp = client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                failed.append((url, str(exc)))
                continue
            sheets.append({"url": url, "content": resp.text, "is_inline": False})
            added_css += 1
        css["stylesheets"] = sheets
        css_path.write_text(json.dumps(css, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest["downloaded_resources"] = out
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": not failed, "downloaded": {**{k: len(v) for k, v in out.items() if v}, "stylesheets": added_css},
                      "failed": failed}, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
