#!/usr/bin/env python3
"""compare_verify.py — layer (a): compare a manifest (oracle) against the
codec re-analysis of the BUILT file. Exact f64 equality (JSON numbers carry
full round-trip precision). Classifies differing fields raw vs derived.
Usage: compare_verify.py <manifest.json> <built_analysis.json>"""
import json, sys

FAM2RX = {
    "polyline3d": "AcDb3dPolyline", "lwpolyline": "AcDbPolyline", "circle": "AcDbCircle", "arc": "AcDbArc", "line": "AcDbLine",
    "mtext": "AcDbMText", "tin_surface": "AeccDbSurfaceTin", "parcel": "AeccDbFace", "site": "AeccDbFace",
    "cogo_point": "AECC_COGO_POINT", "pipe": "AECC_PIPE", "structure": "AECC_STRUCTURE",
    "alignment": "AeccDbAlignment", "profile": "AeccDbVAlignment",
    "profile_view": "AeccDbGraphProfile", "sample_line_group": "AeccDbSampleLineGroup",
    "sample_line": "AeccDbSampleLine", "section": "AeccDbSection",
    "section_view": "AeccDbGraphCrossSection",
}
DERIVED_FIELDS = {"curve_radii", "triangles", "origin", "stations", "elevations"}

def diff(path, a, b, out):
    if type(a) != type(b):
        out.append((path, a, b)); return
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            diff(f"{path}.{k}", a.get(k), b.get(k), out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((f"{path}[]", f"len={len(a)}", f"len={len(b)}")); return
        for i, (x, y) in enumerate(zip(a, b)):
            diff(f"{path}[{i}]", x, y, out)
    else:
        if a != b:
            out.append((path, a, b))

def main():
    manifest = json.load(open(sys.argv[1]))
    built = json.load(open(sys.argv[2]))
    fails = 0
    print(f"== {manifest['source']}")
    mf = {f["family"]: f for f in manifest["families"]}
    bf = {f["family"]: f for f in built["families"]}
    for fam, f in mf.items():
        g = bf.get(fam)
        if f.get("write") is False:
            # decode-only family (no writer in the bin this round): the
            # built file cannot carry it — report the decode result, not a
            # failure.
            n = g["count"] if g else 0
            print(f"  {fam}: DECODE-ONLY (no writer) — oracle {f['count']}, built {n}")
            continue
        if g is None:
            print(f"  {fam}: MISSING in built"); fails += 1; continue
        if g["count"] != f["count"]:
            print(f"  {fam}: count {g['count']} != {f['count']}"); fails += 1; continue
        diffs = []
        if f["items"]:
            diff(fam, f["items"], g["items"], diffs)
        if not diffs:
            print(f"  {fam}: {f['count']} items BIT-EXACT")
        else:
            raw = [d for d in diffs if d[0].split(".")[-1].split("[")[0] not in DERIVED_FIELDS]
            der = [d for d in diffs if d[0].split(".")[-1].split("[")[0] in DERIVED_FIELDS]
            print(f"  {fam}: {f['count']} items, {len(raw)} RAW diffs, {len(der)} derived diffs")
            for p, a, b in raw[:5]:
                print(f"    RAW {p}: {a} != {b}")
            for p, a, b in der[:3]:
                print(f"    derived {p}: {a} != {b}")
            fails += len(raw)
    # census cross-check: built census counts for written families
    print("  census:", json.dumps(built["codec_census"]))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
