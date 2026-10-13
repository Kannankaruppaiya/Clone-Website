# clone-skills

Claude Code skills for cloning apps and websites, vendored from two MIT-licensed projects:

| Skills | Upstream | What it does |
| --- | --- | --- |
| `replica-recon`, `replica-architect`, `replica-design`, `replica-build`, `replica-backend`, `replica-test`, `replica-diff`, `replica-entrepreneur`, `replica-brand`, `replica-launch`, `replica-deploy` | [Jakeschincariol/replica-skill](https://github.com/Jakeschincariol/replica-skill) | Clean-room rebuild of an app's **features and flows**, then rebrand and launch. Copies no code, assets or copy from the original. |
| `perfect-web-clone` | [ericshang98/Perfect-Web-Clone](https://github.com/ericshang98/Perfect-Web-Clone) | Visual clone of a **web page** into Vite + React, measured with the `pwc` CLI (SSIM gates). |

Pinned upstream commits are in `licenses/UPSTREAM.txt`.

> The two do not mix: replica's rules forbid reusing the original's HTML, CSS or assets, which is exactly what perfect-web-clone reproduces. Pick one per project.

## Use

Open this repo in Claude Code (or copy `.claude/skills/*` into another project's `.claude/skills/`, or into `~/.claude/skills/` for every project).

```
/replica-recon https://cal.com        # app clone: start here, then follow each skill's "next step"
/perfect-web-clone https://example.com  # page clone
```

### Requirements

- **replica**: Python 3.8+, standard library only.
- **perfect-web-clone**: Python 3.10+, Node 20+, and the `pwc` CLI:

  ```bash
  ./scripts/setup.sh
  ```

  In Claude Code cloud sessions a `SessionStart` hook (`.claude/settings.json`) runs this automatically.
  There it pins Playwright 1.56.0 to match the preinstalled Chromium; the environment's network policy
  must also allow the site you clone (a denied host fails with `ERR_TUNNEL_CONNECTION_FAILED`).

### Running perfect-web-clone: two `pwc` bugs and their workarounds

Found while cloning a real site end to end. Use these in place of the steps the skill names:

| Skill step | Problem | Use instead |
| --- | --- | --- |
| after `pwc extract <url>` | Assets and stylesheets are fetched with Playwright's request API, which ignores `HTTPS_PROXY`. Behind a proxy every download fails silently, yet capture integrity still reports `passed`; `pwc section` then returns empty `css_rules`. Check `downloaded_counts` in the extract output. | `python3 scripts/pwc-backfill-assets.py <source_id>` for images and fonts. Add `--with-css` (then rerun `pwc plan`) for `css_rules` too, but see the `theme.css` note below. |
| `pwc assemble` → `pwc build` | The sandbox lives in an in-process singleton, so every `pwc` CLI call starts a fresh one: a second `pwc assemble` never sees your section files and `pwc build` fails with "No sandbox exists". | Run `pwc assemble <source_id>` once to create the shell, write the sections, then `python3 scripts/pwc-assemble-build.py <source_id>` for every rebuild. |

Both scripts call pwc's own library functions; they need the `pwc` package installed and the same
`PWC_SOURCES_DIR` / `PWC_SANDBOX_DIR` (default `~/.pwc/...`) as your `pwc` commands.

## Known limits (from reviewing the code)

- `pwc score` compares pages on a 256×256 grayscale canvas, so it checks layout, not exact colours or small text.
  In a local test a recoloured header with the same layout scored 0.977 (pass) and a broken card row 0.961
  (fail, threshold 0.97): it catches layout breaks, but the margin is thin.
- `pwc assemble` reports `ok: false` until the agent has written every planned section file; that is expected.
- In a signal.org test `pwc plan` gave two sections the bounds of an earlier one, and `styles` stayed empty even
  with `css_rules` restored. Measure geometry and computed styles from the live page, and score with your own
  `--sections` bounds.
- Whenever a capture has stylesheets, `pwc assemble` writes the source's **entire** CSS (695 KB for signal.org,
  framework included) to `public/theme.css` and links it from `index.html`, so the clone ships the original
  stylesheet. Behind a proxy this only happens with `pwc-backfill-assets.py --with-css`. To build without it,
  remove the stylesheets from `css.json`, delete `public/theme.css` and its `<link>` in `index.html`.
- `pwc fingerprints` only matches Shopify patterns, so it passes trivially for any other platform.
- The default `pwc weight` budget (120 KB gzipped code) is exceeded by React plus any animation runtime such as Lottie.
- replica's `features.csv` parity score is filled in by the agent itself; treat it as self-reported. `imgdiff.py` is independent and takes ~13 s per retina screenshot pair.

## Tests

```bash
cd tests && python3 -m unittest discover -s .
```

Covers replica's Python tools (52 tests).

## License

Both upstreams are MIT; their licenses are in `licenses/`.
