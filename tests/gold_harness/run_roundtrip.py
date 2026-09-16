#!/usr/bin/env python3
"""Run the gold-vs-silver roundtrip harness on one DWG file.

Requires:
  - GOLD_DWGREAD env var pointing to a built libredwg `dwgread` binary.
  - acadrust `dwg2json` and `dwgrewrite` examples built with `--features serde`.

Produces:
  - <workdir>/<stem>_gold_orig.json
  - <workdir>/<stem>_silver_orig.json
  - <workdir>/<stem>_rt.dwg
  - <workdir>/<stem>_gold_rt.json
  - <workdir>/<stem>_silver_rt.json
  - <workdir>/<stem>_diff.json
  - <workdir>/<stem>_report.md
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

GOLD_DWGREAD = os.environ.get("GOLD_DWGREAD", "")
CARGO = os.environ.get("CARGO", "cargo")
SCRIPT_DIR = Path(__file__).resolve().parent
HARNESS_DIR = SCRIPT_DIR.parent
REPO_ROOT = HARNESS_DIR.parent


def run(cmd: List[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def run_gold_dwgread(dwg: Path, out_json: Path) -> None:
    if not GOLD_DWGREAD:
        raise RuntimeError("GOLD_DWGREAD env var is not set")
    with open(out_json, "w", encoding="utf-8") as f:
        subprocess.run(
            [GOLD_DWGREAD, "-O", "JSON", str(dwg)],
            stdout=f,
            stderr=subprocess.DEVNULL,
            check=True,
        )


def run_silver_dwg2json(dwg: Path, out_json: Path) -> None:
    run(
        [
            CARGO,
            "run",
            "--quiet",
            "--example",
            "dwg2json",
            "--features",
            "serde",
            "--",
            str(dwg),
            str(out_json),
        ],
        cwd=REPO_ROOT,
    )


def run_silver_rewrite(dwg: Path, out_dwg: Path) -> None:
    run(
        [
            CARGO,
            "run",
            "--quiet",
            "--example",
            "dwgrewrite",
            "--features",
            "serde",
            "--",
            str(dwg),
            str(out_dwg),
        ],
        cwd=REPO_ROOT,
    )


def normalize(gold_json: Path, silver_json: Path, ignore: Optional[Path]) -> Tuple[Path, Path]:
    gold_norm = gold_json.with_suffix(".norm.json")
    silver_norm = silver_json.with_suffix(".norm.json")
    ignore_arg = [str(ignore)] if ignore else []
    run([sys.executable, str(SCRIPT_DIR / "normalize_gold.py"), str(gold_json)] + ignore_arg, stdout=open(gold_norm, "w", encoding="utf-8"))
    run([sys.executable, str(SCRIPT_DIR / "normalize_silver.py"), str(silver_json)] + ignore_arg, stdout=open(silver_norm, "w", encoding="utf-8"))
    return gold_norm, silver_norm


def diff(gold_norm: Path, silver_norm: Path, ignore: Optional[Path]) -> Dict[str, Any]:
    ignore_arg = [str(ignore)] if ignore else []
    result = run(
        [sys.executable, str(SCRIPT_DIR / "diff_fields.py"), str(gold_norm), str(silver_norm)] + ignore_arg,
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def summarize(name: str, result: Dict[str, Any]) -> str:
    lines = [f"## {name}: {result['total_diffs']} diff(s)"]
    if result["total_diffs"] == 0:
        lines.append("Perfect match.")
        return "\n".join(lines)

    by_kind: Dict[str, int] = {}
    by_type_field: Dict[Tuple[str, str], int] = {}
    for d in result["diffs"]:
        by_kind[d["kind"]] = by_kind.get(d["kind"], 0) + 1
        key = (d.get("type", "?"), d.get("field", "-"))
        by_type_field[key] = by_type_field.get(key, 0) + 1

    lines.append("### By kind")
    for k, c in sorted(by_kind.items()):
        lines.append(f"- {k}: {c}")
    lines.append("### Top divergent (type, field)")
    for (typ, field), c in sorted(by_type_field.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"- {typ}.{field}: {c}")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: run_roundtrip.py <file.dwg> [workdir]", file=sys.stderr)
        return 2
    dwg = Path(sys.argv[1]).resolve()
    workdir = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("/tmp/harness")
    workdir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", dwg.stem)

    ignore = SCRIPT_DIR / "ignore_fields.toml"
    if not ignore.exists():
        ignore = None

    gold_orig = workdir / f"{stem}_gold_orig.json"
    silver_orig = workdir / f"{stem}_silver_orig.json"
    rt_dwg = workdir / f"{stem}_rt.dwg"
    gold_rt = workdir / f"{stem}_gold_rt.json"
    silver_rt = workdir / f"{stem}_silver_rt.json"
    diff_orig_path = workdir / f"{stem}_diff_orig.json"
    diff_rt_path = workdir / f"{stem}_diff_rt.json"
    report_path = workdir / f"{stem}_report.md"

    print(f"[harness] processing {dwg}")
    print("[harness] reading original with libredwg...")
    run_gold_dwgread(dwg, gold_orig)
    print("[harness] reading original with acadrust...")
    run_silver_dwg2json(dwg, silver_orig)

    print("[harness] rewriting with acadrust...")
    run_silver_rewrite(dwg, rt_dwg)

    print("[harness] reading rewrite with libredwg...")
    run_gold_dwgread(rt_dwg, gold_rt)
    print("[harness] reading rewrite with acadrust...")
    run_silver_dwg2json(rt_dwg, silver_rt)

    print("[harness] normalizing and diffing original...")
    gold_norm, silver_norm = normalize(gold_orig, silver_orig, ignore)
    diff_orig = diff(gold_norm, silver_norm, ignore)
    with open(diff_orig_path, "w", encoding="utf-8") as f:
        json.dump(diff_orig, f, indent=2, ensure_ascii=False)

    print("[harness] normalizing and diffing rewrite...")
    gold_rt_norm, silver_rt_norm = normalize(gold_rt, silver_rt, ignore)
    diff_rt = diff(gold_rt_norm, silver_rt_norm, ignore)
    with open(diff_rt_path, "w", encoding="utf-8") as f:
        json.dump(diff_rt, f, indent=2, ensure_ascii=False)

    report = f"""# Roundtrip report: {dwg.name}

Workdir: `{workdir}`

{summarize("Read fidelity (gold_orig vs silver_orig)", diff_orig)}

{summarize("Write fidelity (gold_orig vs gold_rt)", diff_rt)}

{summarize("Internal consistency (silver_orig vs silver_rt)", {"total_diffs": 0, "diffs": []})}

## Outputs
- gold original: `{gold_orig}`
- silver original: `{silver_orig}`
- rewrite DWG: `{rt_dwg}`
- gold rewrite: `{gold_rt}`
- silver rewrite: `{silver_rt}`
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[harness] wrote report to {report_path}")
    print(f"[harness] read-fidelity diffs: {diff_orig['total_diffs']}")
    print(f"[harness] write-fidelity diffs: {diff_rt['total_diffs']}")
    return 0 if diff_orig["total_diffs"] == 0 and diff_rt["total_diffs"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
