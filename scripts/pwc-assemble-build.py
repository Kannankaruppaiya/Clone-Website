#!/usr/bin/env python3
"""Run `pwc assemble` and `pwc build` against an existing sandbox, in one process.

pwc keeps its sandbox in an in-process singleton. Each separate `pwc` CLI call
therefore creates a fresh, empty sandbox: `pwc assemble` never sees the section
files written into the previous one, and `pwc build` fails with "No sandbox
exists". This finds the sandbox that belongs to the source, re-attaches it
without re-initializing (which would wipe it), and calls the same library
functions the CLI wraps.

Usage: pwc-assemble-build.py <source_id> [sandbox_dir_name]
"""
import asyncio
import json
import sys
from pathlib import Path

from core.boxlite import sandbox_manager as sm
from core.boxlite.models import SandboxStatus
from mcp_server.tools.build_deploy import assemble_project, build_project


def find_sandbox(source_id: str) -> str:
    base = Path(sm.SANDBOX_BASE_DIR)
    matches = [
        d for d in base.glob("sandbox-*")
        if (d / ".pwc" / "source-id").is_file()
        and (d / ".pwc" / "source-id").read_text(encoding="utf-8").strip() == source_id
    ]
    if not matches:
        sys.exit(f"no sandbox under {base} belongs to {source_id}; run `pwc assemble {source_id}` once first")
    return max(matches, key=lambda d: d.stat().st_mtime).name


async def main(source_id: str, sandbox_id: str) -> int:
    sb = sm.BoxLiteSandbox(sandbox_id)
    sb._initialized = True
    sb.state.status = SandboxStatus.READY
    sm._sandboxes[sandbox_id] = sb
    sm._singleton_id = sandbox_id

    assembled = await assemble_project(source_id)
    print(json.dumps({"sandbox": str(sb.work_dir), "assemble_ok": assembled.get("ok"),
                      "missing_section_files": assembled.get("missing_section_files")}, indent=2))
    if not assembled.get("ok"):
        return 1
    built = await build_project()
    print(json.dumps({k: built.get(k) for k in ("success", "exit_code", "dist_dir", "errors")},
                     indent=2, default=str))
    if not built.get("success"):
        print(built.get("stdout_tail", ""), built.get("stderr_tail", ""), sep="\n")
    return 0 if built.get("success") else 1


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    source = sys.argv[1]
    sys.exit(asyncio.run(main(source, sys.argv[2] if len(sys.argv) == 3 else find_sandbox(source))))
