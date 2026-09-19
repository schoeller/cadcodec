#!/usr/bin/env python3
"""Normalize LibreDWG `dwgread -O JSON` output to a canonical object list.

Keeps only the top-level OBJECTS array, drops all header/section keys, and
flattens values to a simple, diffable form:
  - handles become dicts with keys code/size/value/absref (or a plain int when
    the handle resolves to 0 / NULL)
  - 2D/3D points become [x, y] or [x, y, z]
  - colors become simple ints or dicts only if they carry RGB/name data
"""

import json
import re
import sys
from typing import Any, Dict, List, Optional

HEADER_KEYS = {
    "created_by",
    "FILEHEADER",
    "HEADER",
    "CLASSES",
    "THUMBNAILIMAGE",
    "ObjFreeSpace",
    "SecondHeader",
    "Template",
    "AuxHeader",
    "R2004_Header",
    "R2007_Header",
    "SummaryInfo",
    "VBAProject",
    "AppInfo",
    "AppInfoHistory",
    "FileDepList",
    "Security",
    "RevHistory",
    "AcDs",
}


def load_ignore_fields(path: str) -> Dict[str, Any]:
    try:
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)
    except ImportError:
        import tomli as tomllib  # type: ignore

        with open(path, "rb") as f:
            data = tomllib.load(f)
    return data


def is_ignored(name: str, ignore_set: set, ignore_patterns: List[str]) -> bool:
    if name in ignore_set:
        return True
    for pat in ignore_patterns:
        if pat.endswith("*") and name.startswith(pat[:-1]):
            return True
        if pat.startswith("*") and name.endswith(pat[1:]):
            return True
    return False


def normalize_handle(value: Any) -> Any:
    """LibreDWG emits handles as [code, size, value, absref?]."""
    if isinstance(value, list) and len(value) >= 3:
        return {
            "code": value[0],
            "size": value[1],
            "value": value[2],
            "absref": value[3] if len(value) > 3 else value[2],
        }
    return value


def normalize_value(value: Any) -> Any:
    if isinstance(value, list):
        # Heuristic: 2/3 numeric elements are a point; 3/4-element int-only
        # arrays are handles (LibreDWG emits both 3- and 4-element forms).
        if len(value) in (2, 3) and all(isinstance(v, (int, float)) for v in value):
            # Distinguish point from handle: points contain floats.
            if any(isinstance(v, float) for v in value):
                return [round(v, 14) if isinstance(v, float) else v for v in value]
            if len(value) == 3 and all(isinstance(v, int) for v in value):
                return normalize_handle(value)
        if len(value) in (3, 4) and all(isinstance(v, int) for v in value):
            return normalize_handle(value)
        return [normalize_value(v) for v in value]
    if isinstance(value, dict):
        # CMC color hash? Collapse to the index when the rgb payload is absent
        # or zero (ByLayer/ByBlock/indexed colors). R2004+ ENC output includes
        # derived keys (`rgb`, `flag`) alongside `index`; the index is the
        # semantic value silver stores. True-color entities keep their dict.
        if set(value.keys()) == {"index"}:
            return value["index"]
        if "index" in value and value.get("rgb") in (None, "000000", 0):
            return value["index"]
        # ByBlock-with-transparency: gold's field_cmc omits `index` when it
        # resolves to 0 (the `index > 0 && index < 256` check in out_json.c),
        # leaving {"rgb":"000000", flag:32, alpha_type:1, ...}. alpha_type 1 is
        # ByBlock transparency; rgb 000000 + no index = ByBlock color. Silver
        # stores this as Color::ByBlock -> 0. Collapse so the dict doesn't diff
        # against silver's scalar. (Only when there is no `index` key at all —
        # a present index is the semantic value and is handled above.)
        if "index" not in value and value.get("rgb") in (None, "000000", 0):
            return 0
        # CMC `rgb` high byte is the color METHOD (bits.c bit_downconvert_CMC
        # 4061 / include/dwg.h DWG_COLOR_METHOD): c0 = ByLayer, c1 = ByBlock,
        # c2 = ACI/entity color (low 24 bits hold the rgb), c3 = truecolor
        # (indexed variant holds the real index in the low byte), c8 = "none".
        # Collapse to silver's scalar convention.
        rgb = value.get("rgb")
        if isinstance(rgb, str) and len(rgb) == 8:
            flag = rgb[:2]
            if flag == "c3":
                try:
                    return int(rgb[6:8], 16)
                except ValueError:
                    pass
            if flag == "c0":
                return 256      # ByLayer
            if flag == "c1":
                return 0        # ByBlock
            if flag == "c8":
                return 257      # none
        return {k: normalize_value(v) for k, v in value.items()}
    if isinstance(value, float):
        # Normalize -0.0 and NaN the same way gold release build does.
        if value != value:
            return 0.0
        if value == 0.0:
            return 0.0
        return round(value, 14)
    return value


def object_type(obj: Dict[str, Any]) -> str:
    return obj.get("entity") or obj.get("object") or "UNKNOWN"


def normalize_gold(data: Dict[str, Any], ignore: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    ignore_set: set = set()
    ignore_patterns: List[str] = []
    if ignore:
        ignore_set.update(ignore.get("global", {}).get("ignore", []))
        for pat in ignore.get("global", {}).get("ignore", []):
            if "*" in pat:
                ignore_patterns.append(pat)

    objects = data.get("OBJECTS", [])
    out: List[Dict[str, Any]] = []
    for obj in objects:
        typ = object_type(obj)
        fields: Dict[str, Any] = {}
        for k, v in obj.items():
            if k in ("entity", "object"):
                continue
            if is_ignored(k, ignore_set, ignore_patterns):
                continue
            # LibreDWG prints a code-0 null handle as the bare 2-tuple
            # [0, 0] (absolute, no offset counter) while code-3 nulls print
            # as the full 4-tuple. In the corpus only `history_id`
            # (3DSOLID/REGION, dwg_spec_shared.h COMMON_3DSOLID) hits the
            # 2-tuple form as a handle; 2-tuple points elsewhere must stay
            # lists, so gate strictly on the field name. Canonicalize the
            # null to gold's absref-0 dict so it compares equal against
            # silver's null dict (its code is None — tolerated by the
            # differ). ATTRIB.style's matching [0, 0] form is untouched.
            if k == "history_id" and v == [0, 0]:
                fields[k] = {"code": 0, "size": 0, "value": 0, "absref": 0}
                continue
            fields[k] = normalize_value(v)
        out.append({"type": typ, "fields": fields})
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: normalize_gold.py <gold.json> [ignore_fields.toml]", file=sys.stderr)
        sys.exit(1)
    ignore: Optional[Dict[str, Any]] = None
    if len(sys.argv) >= 3:
        ignore = load_ignore_fields(sys.argv[2])
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    norm = normalize_gold(data, ignore)
    json.dump(norm, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
