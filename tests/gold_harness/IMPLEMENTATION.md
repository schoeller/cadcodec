# Gold-vs-Silver Roundtrip Harness — Implementation Plan

Date: 2026-09-16
Status: Phase 2–5 complete; Phase 6 fix loop pending user validation of `AcDbVisualStyle` in AutoCAD.
Location: `tests/gold_harness/IMPLEMENTATION.md`

> This file is the single source of truth for the harness plan. All earlier plans (`REFINEMENT_REPORT.md` in the repo root and `tests/gold_harness/REFINEMENT_REPORT.md`) are outdated and superseded by this document.

---

## 1. Goal

Close the read/write fidelity gap between LibreDWG (gold) and cadcodec (silver) for a representative subset of the LibreDWG `test/test-data` corpus, using a repeatable automated harness. The immediate blocker is an AutoCAD `AcDbVisualStyle` "Object improperly read" error on rewritten DWGs.

---

## 2. Architecture

```
DWG file
    ├─ dwgread -O JSON (LibreDWG) ──► gold_orig.json
    ├─ dwg2json (acadrust) ─────────► silver_orig.json
    └─ dwgrewrite (acadrust) ───────► rt.dwg
                                         ├─ dwgread -O JSON ──► gold_rt.json
                                         └─ dwg2json ─────────► silver_rt.json

normalize_gold.py  +  normalize_silver.py  ──► canonical records
                                      │
                                      ▼
                            diff_fields.py
                                      │
                                      ▼
                         diff_orig.json  (read fidelity)
                         diff_rt.json    (write fidelity)
```

- **Alignment**: records are paired by `(type, ordinal-within-type)`, not by handle, because handles are reassigned on rewrite.
- **Handle comparison**: handle-valued fields are compared by the resolved target type (`handle → record_type`), not by raw id.
- **Strict mode**: `GOLD_HARNESS_STRICT=1` asserts zero `missing_in_silver` diffs.

---

## 3. What is already implemented

### Silver JSON dump (`examples/dwg2json.rs`)
- Reads a DWG into `CadDocument`, serializes with `serde`, and re-injects the 12 serde-skipped `EntityCommon` round-trip fields under `_common_dwg[handle]`.
- Fields: `linetype_handle`, `graphic_data`, `color_book_handle`, `face_visual_style_handle`, `edge_visual_style_handle`, `material_flags`, `material_handle`, `shadow_flags`, `plotstyle_flags`, `plotstyle_handle`, `entity_mode`, `has_ds_data`.

### Silver rewrite binary (`examples/dwgrewrite.rs`)
- Minimal read → write binary that targets the same DWG version as the source.

### Normalizers
- `normalize_gold.py`: keeps the top-level `OBJECTS` array, drops header/section metadata, flattens points/handles/colors.
- `normalize_silver.py`: emits entities, objects, and table records; resolves layer names to handles; maps variant/field names to gold conventions.

### Differ (`diff_fields.py`)
- Aligns by `(type, ordinal)` and compares handle-valued fields by resolved target type.
- Reports `missing_in_silver`, `wrong_value`, `extra_in_silver`, `count_mismatch`.

### Driver / batch / cargo test
- `run_roundtrip.py`: orchestrates the three diffs per file.
- `run_corpus.py`: batch driver that aggregates `report.json`/`report.md`.
- `tests/gold_roundtrip.rs`: gated behind `gold-harness`; by default asserts the harness runs and that no prohibited `EntityCommon` fields appear; strict zero-missing mode is opt-in via `GOLD_HARNESS_STRICT=1`.

### Recent code fixes
- `src/io/dwg/dwg_writer.rs`: class-table filtering now retains live `ClassObject` instances (e.g. `ACDBSECTIONVIEWSTYLE`, `ACDBDETAILVIEWSTYLE`) after `retain_legacy_dwg_classes()`, so their type codes are not mis-emitted as `500` (`ACDBDICTIONARYWDFLT`).
- `tests/visualstyle_dwg_roundtrip.rs`: regression test that builds a `VisualStyle` with a full 24-element pre-R2010 property bag, round-trips it through R2000 DWG, and asserts the recovered properties match.

---

## 4. Current baseline on `2000/Line.dwg`

After refinement and ignore-field tuning:
- **Read-fidelity diffs**: ~2658
- **Entity-level diffs are small**: `LINE` has ~9 diffs, mostly in `EntityCommon` storage-only fields (`prev_entity`, `next_entity`, `nolinks`, `ltype_flags`, `plotstyle_flags`, `z_is_zero`) plus a few extra fields (`linetype`, `color_name`, `ownerhandle`).
- **Object-level diffs dominate**: `XRECORD`, `DICTIONARY`, `SCALE`, `VISUALSTYLE` representation mismatches. Many are silver-specific fields that do not exist in gold, or gold fields that silver does not store.

---

## 5. Known issues and blockers

| Issue | Status | Notes |
|---|---|---|
| `AcDbDictionaryWithDefault` mis-emitted as type 500 | Fixed | Class-table retention fix in `src/io/dwg/dwg_writer.rs` |
| `ACDBSECTIONVIEWSTYLE` / `ACDBDETAILVIEWSTYLE` missing after rewrite | Fixed | Same class-table retention fix |
| `AcDbVisualStyle` "Object improperly read" | Pending user validation | Internal R2000 round-trip test passes; need AutoCAD feedback on `/tmp/gold_harness_test/Line_*_rt.dwg` |

---

## 6. Out-of-loop scope

The following are intentionally deferred until they block a covered entity or the corpus expands:
- Full object topology fixes for `DICTIONARY`, `XRECORD`, `SCALE`, `VISUALSTYLE` representation mismatches.
- Polyline vertex expansion (no covered fixture has expanded vertices yet).
- Resolving handles to `(type, name)` instead of `(type)`.

---

## 7. Next steps

1. Open the rewritten files in AutoCAD:
   - `/tmp/gold_harness_test/Line_2000_rt.dwg`
   - `/tmp/gold_harness_test/Line_2004_rt.dwg`
   - `/tmp/gold_harness_test/Line_2007_rt.dwg`
   - `/tmp/gold_harness_test/Line_2010_rt.dwg`
   - `/tmp/gold_harness_test/Line_2013_rt.dwg`
   - `/tmp/gold_harness_test/Line_2018_rt.dwg`
2. Report which versions still show `AcDbVisualStyle` "Object improperly read".
3. If the error is version-specific, inspect the pre-R2010 VisualStyle writer for version-conditional fields (e.g. `bd2007_45` should only be emitted since R2007).
4. If the error is gone, proceed with Phase 6: close `EntityCommon` storage-only field gaps (`prev_entity`, `next_entity`, `nolinks`, `ltype_flags`, `plotstyle_flags`, `z_is_zero`).

---

## 8. How to run

```bash
# Build examples
cd ~/work/cadcodec
source $HOME/.cargo/env
cargo build --features serde --examples

# Run harness on one file
GOLD_DWGREAD=$HOME/work/libredwg/programs/dwgread \
GOLD_TESTDATA=$HOME/work/libredwg/test/test-data \
python3 tests/gold_harness/run_roundtrip.py \
    $HOME/work/libredwg/test/test-data/2000/Line.dwg \
    /tmp/harness_out

# Run representative cargo test
cargo test --features gold-harness --test gold_roundtrip

# Strict mode
cargo test --features gold-harness --test gold_roundtrip
```

---

## 9. File inventory

| File | Purpose |
|---|---|
| `tests/gold_harness/run_roundtrip.py` | Single-file driver |
| `tests/gold_harness/run_corpus.py` | Batch driver |
| `tests/gold_harness/normalize_gold.py` | LibreDWG JSON normalizer |
| `tests/gold_harness/normalize_silver.py` | cadcodec JSON normalizer |
| `tests/gold_harness/diff_fields.py` | Diff engine |
| `tests/gold_harness/ignore_fields.toml` | Fields ignored during diff |
| `tests/gold_roundtrip.rs` | Cargo integration test |
| `tests/visualstyle_dwg_roundtrip.rs` | VisualStyle regression test |
| `examples/dwg2json.rs` | Silver JSON dump |
| `examples/dwgrewrite.rs` | Silver rewrite binary |

---

## 10. Plan history

- `tests/gold_harness/REFINEMENT_REPORT.md` and repo-root `REFINEMENT_REPORT.md` documented Phase 2–5 refinement. They are now superseded by this file.
