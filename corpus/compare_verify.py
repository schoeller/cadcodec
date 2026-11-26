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
    "assembly": "AeccDbAssembly", "corridor": "AeccDbCorridor",
    "profile_view": "AeccDbGraphProfile", "sample_line_group": "AeccDbSampleLineGroup",
    "sample_line": "AeccDbSampleLine", "section": "AeccDbSection",
    "section_view": "AeccDbGraphCrossSection",
}
DERIVED_FIELDS = {"curve_radii", "triangles", "origin", "stations", "elevations"}

# Handle-valued fields of a corridor definition: compared as family
# ordinals (the builder remaps oracle handles onto the rebuilt records in
# analyze order; ordinal equality is topology equality).
CORRIDOR_REF_FIELDS = {"alignment", "profile", "assembly", "subassembly", "objects"}

def family_handles(manifest, fam_name, side):
    f = next((x for x in manifest.get("families", []) if x.get("family") == fam_name), None)
    if not f:
        return {}
    hs = f.get("handles") or []
    return {v: i for i, v in enumerate(hs) if isinstance(v, int)}

def normalize_corridor_ref(v, field, maps):
    # v is a handle value (or list of them for "objects"); map to the
    # family ordinal, or to -1 when unknown (dangling on either side).
    def one(x):
        if not isinstance(x, int) or x == 0:
            return x
        for m in maps:
            if x in m:
                return m[x]
        return -1
    if field == "objects":
        return [one(x) for x in v] if isinstance(v, list) else v
    return one(v)

def normalize_corridor_items(items, maps):
    out = []
    for it in items:
        it = json.loads(json.dumps(it))  # deep copy
        d = it.get("definition")
        if isinstance(d, dict):
            for b in d.get("baselines", []):
                for fld in ("alignment", "profile"):
                    if fld in b:
                        b[fld] = normalize_corridor_ref(b[fld], fld, maps)
                for r in b.get("regions", []):
                    if "assembly" in r:
                        r["assembly"] = normalize_corridor_ref(r["assembly"], "assembly", maps)
                    for t in r.get("targets", []):
                        if "objects" in t:
                            t["objects"] = normalize_corridor_ref(t["objects"], "objects", maps)
        out.append(it)
    return out

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
            a_items, b_items = f["items"], g["items"]
            if fam == "corridor":
                amaps = [family_handles(manifest, n, "oracle") for n in ("alignment", "profile", "assembly", "tin_surface")]
                bmaps = [family_handles(built, n, "built") for n in ("alignment", "profile", "assembly", "tin_surface")]
                a_items = normalize_corridor_items(a_items, amaps)
                b_items = normalize_corridor_items(b_items, bmaps)
            diff(fam, a_items, b_items, diffs)
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
