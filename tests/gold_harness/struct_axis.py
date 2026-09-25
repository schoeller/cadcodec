#!/usr/bin/env python3
"""The structure axis (IMPLEMENTATION.md §19, packet H0 — the skeleton).

A second, separately-gated comparison axis beside the OBJECTS axis: the
17 observed structure keys gold emits (§19.1's closed enumeration), with
a per-key leaf-census compare. This module is the measuring instrument —
the per-field typed projections land with the H2-H5 packets; H0 only
measures per-key presence and leaf-level gaps (name-canonical matches,
value diffs on matches, leaves missing on either side).

Design rules (§19.2's H0):
- The OBJECTS axis stays frozen: nothing here touches the record-list
  normalizers or the differ.
- `created_by` is EXCLUDED (gold's own PACKAGE_STRING stamp — not file
  content); VBAProject/Signature are DECLARED-ABSENT (corpus-absent);
  any UNDECLARED gold top-level key is surfaced (the no-leak assertion),
  never silently passed.

CLI: struct_axis.py <gold.json> <silver_or_gold2.json> [--write-target]
prints the per-file census JSON.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from normalize_gold import _sanitize_gold_acis  # the byte-level JSON fixer

# ── The key registry (§19.1's closed enumeration) ──

#: The 17 observed structure keys (the corpus-wide union; presence is
#: per-version, §19.1's matrix).
OBSERVED_KEYS: List[str] = [
    "HEADER",
    "FILEHEADER",
    "R2004_Header",
    "R2007_Header",
    "SecondHeader",
    "AuxHeader",
    "SummaryInfo",
    "AppInfo",
    "AppInfoHistory",
    "Template",
    "FileDepList",
    "RevHistory",
    "Security",
    "ObjFreeSpace",
    "THUMBNAILIMAGE",
    "AcDs",
    "CLASSES",
]

#: Keys with recorded exclusion reasons (never compared).
EXCLUDED_KEYS: Dict[str, str] = {
    "created_by": "gold's own PACKAGE_STRING stamp (out_json.c:2617) — oracle identity, not file content",
    "OBJECTS": "the body axis — already gated by the record-list comparison",
}

#: Declared in gold's drop-list but absent from the corpus files.
DECLARED_ABSENT: Dict[str, str] = {
    "VBAProject": "corpus-absent (the drop-list declares it)",
    "Signature": "corpus-absent AND gold's emitter is deliberately disabled (out_json.c:2673)",
}

_MAX_SAMPLES = 8
_MAX_SAMPLE_CHARS = 120
_REL_TOL = 1e-6


# ── Loaders (gold output needs the -nan / raw-ACIS shims) ──


def load_gold_json(path: Path) -> Dict[str, Any]:
    raw = _sanitize_gold_acis(open(str(path), "rb").read())
    s = raw.decode("utf-8", errors="replace")
    # Gold prints invalid doubles as -nan (bit-double error code '11');
    # normalize_gold maps them to NaN for its own strict=False load. Here
    # they map to a plain 0.0 for census counting (a census leaf with a
    # NaN on the gold side still counts as one leaf; exact NaN-vs-value
    # fidelity is record-axis work, already handled there).
    s = re.sub(r"(?<![\"\w])-?nan(?![\"\w])", "0.0", s)
    s = s.replace("-nan", "0.0").replace("NaN", "0.0")
    return json.loads(s, strict=False)


def load_silver_json(path: Path) -> Dict[str, Any]:
    return json.load(open(str(path), "r", encoding="utf-8"))


def load_auto(path: Path) -> Tuple[Dict[str, Any], str]:
    """Load a raw dump, robustly: try plain JSON first (silver), fall
    back to the gold shims. Returns (doc, side) with side 'gold'/'silver'."""
    try:
        return load_silver_json(path), "silver"
    except (json.JSONDecodeError, UnicodeDecodeError):
        return load_gold_json(path), "gold"


# ── Structure views ──


def gold_structure_views(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Extract the observed keys; return (views, undeclared-top-level-keys).

    The undeclared list drives the no-leak assertion: a gold top-level
    key outside OBSERVED/EXCLUDED/ABSENT must surface, never silently
    pass (§19.2's H0 corollary — `Signature` was the latent example).
    """
    views: Dict[str, Any] = {k: data.get(k) for k in OBSERVED_KEYS}
    known = set(OBSERVED_KEYS) | set(EXCLUDED_KEYS) | set(DECLARED_ABSENT)
    undeclared = sorted(k for k in data.keys() if k not in known)
    return views, undeclared


#: Silver's minimal seed projection (the H0 baseline — H2-H5 packets
#: replace these with real field-list projections from the spec files):
#: what silver's dwg2json emits today, mapped into gold's key names.
def silver_structure_views(doc: Dict[str, Any]) -> Dict[str, Any]:
    views: Dict[str, Any] = {}
    fh: Dict[str, Any] = {}
    if isinstance(doc.get("version"), str):
        fh["version"] = doc["version"]
    if isinstance(doc.get("maintenance_version"), int):
        # silver's `maintenance_version` is gold's `maint_rel_version`
        # (the release level: AC1015 files carry 15 there while gold's
        # `maint_version` stays 0 — the R2000 census finding that pinned
        # this mapping).
        fh["maint_rel_version"] = doc["maintenance_version"]
    if fh:
        views["FILEHEADER"] = fh
    if isinstance(doc.get("header"), dict):
        views["HEADER"] = doc["header"]
    if isinstance(doc.get("summary_info"), dict):
        views["SummaryInfo"] = doc["summary_info"]
    if isinstance(doc.get("preview"), dict):
        views["THUMBNAILIMAGE"] = doc["preview"]
    if isinstance(doc.get("classes"), dict) and isinstance(
        doc["classes"].get("entries"), list
    ):
        views["CLASSES"] = doc["classes"]["entries"]
    return views


# ── The leaf census ──


def _canon(name: Any) -> str:
    """Canonical leaf-name for cross-side matching: silver's snake_case
    names canon onto gold's mixed-case names (required_versions →
    REQUIREDVERSIONS). H3's per-variable ledger replaces this with the
    authoritative name map."""
    return re.sub(r"[^A-Z0-9]", "", str(name).upper())


def flatten(value: Any, prefix: str = "") -> Dict[str, Any]:
    """Flatten a nested dict/list to a leaf map (path → scalar).

    Scalars (str/int/float/bool/None) are terminal; dicts recurse per
    key; lists recurse per index. Long hex strings stay one leaf (the
    thumbnail blob compares as one leaf — byte fidelity lands in H5's
    digest work)."""
    out: Dict[str, Any] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = value
    return out


def _leaves_equal(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b if isinstance(a, bool) and isinstance(b, bool) else a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == b:
            return True
        try:
            return abs(a - b) <= _REL_TOL * max(abs(a), abs(b), 1.0)
        except (TypeError, OverflowError):
            return False
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    return a == b


def compare_key_views(
    gold_value: Any, other_value: Any, other_side: str = "silver"
) -> Dict[str, Any]:
    """Leaf-census one structure key between gold and the other side.

    Counts (never field-level projections — that is the H2-H5 work):
    - `matched` leaves (name-canonical match on both sides)
    - `value_diffs` among the matched
    - `missing_<other_side>`: gold leaves the other side lacks
    - `missing_gold`: other-side leaves gold lacks (projection noise)
    - `samples`: the first few diffing leaf names, for eyeballing
    """
    if gold_value is None and other_value is None:
        return {"status": "absent_both"}
    if gold_value is None:
        return {
            "status": "missing_gold",
            "other_leaves": len(flatten(other_value)),
        }
    if other_value is None:
        return {
            "status": f"missing_{other_side}",
            "gold_leaves": len(flatten(gold_value)),
        }
    g = flatten(gold_value)
    o = flatten(other_value)
    o_by_canon: Dict[str, Tuple[str, Any]] = {}
    for k, v in o.items():
        o_by_canon.setdefault(_canon(k), (k, v))
    g_by_canon: Dict[str, Tuple[str, Any]] = {}
    for k, v in g.items():
        g_by_canon.setdefault(_canon(k), (k, v))

    matched = 0
    value_diffs = 0
    missing_other = 0
    missing_gold = 0
    samples: List[str] = []
    for k, v in g.items():
        hit = o_by_canon.get(_canon(k))
        if hit is None:
            missing_other += 1
            continue
        matched += 1
        if not _leaves_equal(v, hit[1]):
            value_diffs += 1
            if len(samples) < _MAX_SAMPLES:
                # Trim each repr: sample leaves can be multi-KB hex blobs
                # (thumbnails, AppInfo unknown_bits) that would bloat every
                # per-file census artifact.
                entry = f"{k}: gold={v!r} vs {other_side}={hit[1]!r}"
                if len(entry) > _MAX_SAMPLE_CHARS:
                    entry = entry[:_MAX_SAMPLE_CHARS] + "…"
                samples.append(entry)
    for k in o:
        if _canon(k) not in g_by_canon:
            missing_gold += 1

    return {
        "status": "present_both",
        "gold_leaves": len(g),
        "other_leaves": len(o),
        "matched": matched,
        "value_diffs": value_diffs,
        f"missing_{other_side}": missing_other,
        "missing_gold": missing_gold,
        "samples": samples,
    }


def compare_structure(
    gold_data: Dict[str, Any],
    other_data: Dict[str, Any],
    other_side: str = "silver",
    other_is_gold_dump: bool = False,
) -> Dict[str, Any]:
    """The per-file census: every observed key compared (or accounted
    absent/missing), exclusions recorded, undeclared keys surfaced."""
    gold_views, undeclared = gold_structure_views(gold_data)
    if other_is_gold_dump:
        # The write-preservation axis: the other side is gold's own read
        # of the rewritten file — same view extraction, no silver mapping.
        other_views, _ = gold_structure_views(other_data)
    else:
        other_views = silver_structure_views(other_data)

    per_key: Dict[str, Any] = {}
    leaf_sum_read_axis = 0
    for key in OBSERVED_KEYS:
        r = compare_key_views(gold_views.get(key), other_views.get(key), other_side)
        per_key[key] = r
        if r.get("status") == "present_both":
            leaf_sum_read_axis += r["value_diffs"] + r[f"missing_{other_side}"]
        elif r.get("status") == f"missing_{other_side}":
            leaf_sum_read_axis += r["gold_leaves"]

    absent_notes: Dict[str, str] = {}
    for key, reason in DECLARED_ABSENT.items():
        if gold_data.get(key) is not None:
            absent_notes[key] = f"PRESENT on gold (expected absent: {reason})"
        else:
            absent_notes[key] = "absent as declared"

    return {
        "axis": "read" if other_side == "silver" else "write-target",
        "per_key": per_key,
        "undeclared_keys": undeclared,
        "declared_absent": absent_notes,
        "excluded": dict(EXCLUDED_KEYS),
        "totals": {
            # The attack-order number: projection work needed per file
            "key_gap_sum": leaf_sum_read_axis,
            "keys_missing_other": sum(
                1 for r in per_key.values() if r.get("status") == f"missing_{other_side}"
            ),
            "keys_present_both": sum(
                1 for r in per_key.values() if r.get("status") == "present_both"
            ),
        },
    }


def census_from_files(
    gold_path: Path, other_path: Path, other_side: str = "auto"
) -> Dict[str, Any]:
    """Load both raw dumps and run the census.

    `other_side` must be `"silver"` (the read axis: silver's dwg2json
    projection) or `"gold_rt"` (the write-preservation axis: gold's own
    read of the rewritten file, same view extraction as gold_orig).
    The sides differ in VIEW EXTRACTION, not just parsing: a gold dump
    that happens to parse as plain JSON (no -nan tokens) must still be
    extracted gold-style — so callers that know the side pass it, and
    `"auto"` (the CLI fallback) guesses by parse behavior only.
    """
    gold_doc = load_gold_json(gold_path)
    if other_side == "auto":
        _, detected = load_auto(other_path)
        other_side = "gold_rt" if detected == "gold" else "silver"
    if other_side == "silver":
        other_doc = load_silver_json(other_path)
        other_is_gold = False
    else:
        other_doc = load_gold_json(other_path)
        other_is_gold = True
    comparison = compare_structure(
        gold_doc,
        other_doc,
        other_side="gold_rt" if other_is_gold else "silver",
        other_is_gold_dump=other_is_gold,
    )
    comparison["gold_file"] = str(gold_path)
    comparison["other_file"] = str(other_path)
    return comparison


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "Usage: struct_axis.py <gold.json> <silver_or_gold2.json> [silver|gold_rt|auto]\n"
            "  The other side: 'silver' (read axis), 'gold_rt' (the write-\n"
            "  preservation axis: gold's read of the rewrite), or 'auto'\n"
            "  (guess by parse behavior).",
            file=sys.stderr,
        )
        return 2
    side = sys.argv[3] if len(sys.argv) >= 4 else "auto"
    result = census_from_files(Path(sys.argv[1]), Path(sys.argv[2]), side)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
