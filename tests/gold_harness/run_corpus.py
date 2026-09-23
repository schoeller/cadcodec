#!/usr/bin/env python3
"""Batch driver for the gold-vs-silver roundtrip harness.

Runs `run_roundtrip.py` over the in-scope corpus and aggregates a
`report.json`/`report.md` ranking divergent (entity_type, field) pairs.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

GOLD_TESTDATA = os.environ.get("GOLD_TESTDATA", str(Path.home() / "work/libredwg/test/test-data"))


def in_scope_files(testdata: Path) -> List[Path]:
    files: List[Path] = []
    for version in ["2000", "2004", "2007", "2010", "2013", "2018"]:
        d = testdata / version
        if d.exists():
            files.extend(
                sorted(
                    p
                    for p in d.iterdir()
                    if p.suffix.lower() == ".dwg"
                    # Pathological upstream-crash file (GitHub issue 44):
                    # gold's decode emits -nan tokens and thousands of
                    # garbage rows on an intentionally corrupt file. Frozen
                    # audit decision (IMPLEMENTATION.md §8.1.6a): excluded
                    # from the campaign's scope and rankings. It was
                    # previously excluded de facto by the normalize crash;
                    # normalize_gold's -nan shim (2026-09-20) made it parse,
                    # so keep the exclusion explicit.
                    and p.name != "gh44-error.dwg"
                )
            )
    for prefix in ["example_", "sample_"]:
        for p in testdata.iterdir():
            if p.name.startswith(prefix) and p.suffix.lower() == ".dwg":
                # Scope guard: only R2000-R2018 (AC1015..AC1032). Exclude the
                # R13/R14 examples, which use a different, out-of-scope format.
                lower = p.name.lower()
                if "r13" in lower or "r14" in lower:
                    continue
                files.append(p)
    # In-repo authored fixtures (IMPLEMENTATION.md §F2.1): one operation
    # per file, version-suffixed stems, qualified per the §F2.1 gates
    # before landing. Collected after the gold tree so a fixture stem
    # colliding with a gold stem stays visible in the report (stems
    # are required globally unique; a collision is a fixture bug).
    files.extend(sorted((SCRIPT_DIR / "tests").rglob("*.dwg")))
    return sorted(set(files))


def run_file(path: Path, workdir: Path) -> Dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "run_roundtrip.py"), str(path), str(workdir / path.stem)],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    diff_orig_path = workdir / path.stem / f"{path.stem}_diff_orig.json"
    diff_rt_path = workdir / path.stem / f"{path.stem}_diff_rt.json"
    diff_orig: Dict[str, Any] = {"total_diffs": -1, "diffs": []}
    diff_rt: Dict[str, Any] = {"total_diffs": -1, "diffs": []}
    if diff_orig_path.exists():
        with open(diff_orig_path, "r", encoding="utf-8") as f:
            diff_orig = json.load(f)
    if diff_rt_path.exists():
        with open(diff_rt_path, "r", encoding="utf-8") as f:
            diff_rt = json.load(f)
    return {
        "file": str(path),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "read_fidelity_diffs": diff_orig["total_diffs"],
        "write_fidelity_diffs": diff_rt["total_diffs"],
    }


def default_workdir() -> Path:
    """Return a repo-relative default corpus workdir under target/gold_harness_corpus/."""
    target = REPO_ROOT / "target"
    target.mkdir(parents=True, exist_ok=True)
    return target / "gold_harness_corpus"


def aggregate(results: List[Dict[str, Any]], workdir: Path) -> Tuple[Dict[Tuple[str, str], int], Dict[Tuple[str, str], int]]:
    read_counts: Dict[Tuple[str, str], int] = {}
    write_counts: Dict[Tuple[str, str], int] = {}
    for r in results:
        if r["read_fidelity_diffs"] == -1:
            continue
        # Re-read the diff files to aggregate by (type, field).
        stem = Path(r["file"]).stem
        file_workdir = workdir / stem
        for diff_path, counter in [
            (file_workdir / f"{stem}_diff_orig.json", read_counts),
            (file_workdir / f"{stem}_diff_rt.json", write_counts),
        ]:
            if not diff_path.exists():
                continue
            with open(diff_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data.get("diffs", []):
                if d.get("kind") == "count_mismatch":
                    key = (d.get("type", "?"), "_count")
                elif d.get("kind") == "missing":
                    key = (d.get("type", "?"), "_missing")
                else:
                    key = (d.get("type", "?"), d.get("field", "-"))
                counter[key] = counter.get(key, 0) + 1
    return read_counts, write_counts


def main() -> int:
    testdata = Path(GOLD_TESTDATA)
    workdir = default_workdir()
    workdir.mkdir(parents=True, exist_ok=True)

    files = in_scope_files(testdata)
    print(f"[corpus] {len(files)} files in scope")

    results: List[Dict[str, Any]] = []
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name}")
        results.append(run_file(f, workdir))

    read_counts, write_counts = aggregate(results, workdir)

    report = {
        "files": len(results),
        "read_fidelity_total": sum(r["read_fidelity_diffs"] for r in results if r["read_fidelity_diffs"] != -1),
        "write_fidelity_total": sum(r["write_fidelity_diffs"] for r in results if r["write_fidelity_diffs"] != -1),
        "read_fidelity_by_type_field": {f"{k[0]}.{k[1]}": v for k, v in sorted(read_counts.items(), key=lambda x: -x[1])},
        "write_fidelity_by_type_field": {f"{k[0]}.{k[1]}": v for k, v in sorted(write_counts.items(), key=lambda x: -x[1])},
        "per_file": results,
    }

    report_json = workdir / "report.json"
    with open(report_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[corpus] wrote {report_json}")

    md = ["# Gold-vs-Silver Corpus Report\n"]
    md.append(f"Files: {report['files']}\n")
    md.append(f"Read-fidelity diffs: {report['read_fidelity_total']}\n")
    md.append(f"Write-fidelity diffs: {report['write_fidelity_total']}\n\n")
    md.append("## Top read-fidelity divergences\n")
    for k, v in sorted(read_counts.items(), key=lambda x: -x[1])[:30]:
        md.append(f"- {k[0]}.{k[1]}: {v}\n")
    md.append("\n## Top write-fidelity divergences\n")
    for k, v in sorted(write_counts.items(), key=lambda x: -x[1])[:30]:
        md.append(f"- {k[0]}.{k[1]}: {v}\n")
    report_md = workdir / "report.md"
    with open(report_md, "w", encoding="utf-8") as f:
        f.writelines(md)
    print(f"[corpus] wrote {report_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
