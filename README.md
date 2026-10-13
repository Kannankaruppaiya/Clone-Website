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

## Known limits (from reviewing the code)

- `pwc score` compares pages on a 256×256 grayscale canvas, so it checks layout, not exact colours or small text.
  In a local test a recoloured header with the same layout scored 0.977 (pass) and a broken card row 0.961
  (fail, threshold 0.97): it catches layout breaks, but the margin is thin.
- `pwc assemble` reports `ok: false` until the agent has written every planned section file; that is expected.
- replica's `features.csv` parity score is filled in by the agent itself; treat it as self-reported. `imgdiff.py` is independent and takes ~13 s per retina screenshot pair.

## Tests

```bash
cd tests && python3 -m unittest discover -s .
```

Covers replica's Python tools (52 tests).

## License

Both upstreams are MIT; their licenses are in `licenses/`.
