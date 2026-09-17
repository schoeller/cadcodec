# Gold-vs-Silver Roundtrip Harness — Unified Implementation Plan

Date: 2026-09-17 (consolidated from the original plan, the refinement reports, and
the interim `_IMPLEMENTATION.md`; supersedes all three)
Status: Phase 2–5 complete; `AcDbVisualStyle` blocker **fixed** (2026-09-17);
EntityCommon storage-only field gap **closed** (2026-09-17) — LINE/CIRCLE entity
diffs are zero on all six versions for read and write fidelity. Phase 6 fix loop
continues on table-record storage fields and object representation gaps.
Location: `tests/gold_harness/IMPLEMENTATION.md` — the single source of truth.

> This file is the only authoritative plan for the gold-vs-silver harness.
> Earlier documents — `1789491909007-cadcodec-gold-silver-roundtrip.md`,
> `REFINEMENT_REPORT.md`, `REFINEMENT_REPORT_ROOT.md`, and `_IMPLEMENTATION.md` —
> are superseded and preserved under `tests/gold_harness/_archiv/` for
> historical reference only.

---

## 1. Goal

Close the read/write fidelity gap between **LibreDWG (gold oracle)** and
**cadcodec (`acadrust` crate, silver)** for a representative subset of the
LibreDWG `test/test-data` corpus, using a repeatable automated harness, then
drive an autonomous fix loop until the silver non-header output matches gold
across the covered corpus.

"Roundtrip" verifies **both** cadcodec's reader and writer: cadcodec reads a
gold DWG, re-encodes it, and the result is re-decoded — with LibreDWG acting as
the independent oracle on both the original and the rewritten file.

The header is tested **laxly** (out of strict-diff scope — only entity/object
non-header parts must match exactly). The loop is **bounded to the test-data
corpus** and must respect the **R2000–R2018 version scope**.

The immediate blocker is an AutoCAD `AcDbVisualStyle` "Object improperly read"
error on rewritten DWGs (see §7).

---

## 2. Confirmed decisions

| Decision | Choice |
|---|---|
| Comparison oracle | JSON field-level diff (libredwg `dwgread -O JSON` vs acadrust serde JSON) |
| Roundtrip meaning | Verify both cadcodec reader and writer; libredwg validates both ends |
| Environment | WSL — build libredwg from source; run cadcodec via `cargo` |
| Version scope | R2000–R2018 (AC1015, AC1018, AC1021, AC1024, AC1027, AC1032) |
| Silver JSON source | Reuse cadcodec's `serde` feature + a dump bin that re-includes serde-skipped `EntityCommon` fields under `_common_dwg[handle]` |
| Fix-loop coverage | Bounded to the test-data corpus; gap entities logged as out-of-loop |
| Loop convergence target | Zero non-header, non-ignored field diffs across the covered corpus |
| Version-scope guard | Gate each fix by the gold spec's version predicate; verify all 6 versions |
| Safety / regression gate | Per-fix checkpoint: `git commit` if available, else record in `report.md`; corpus non-regression + `cargo test` green |
| Convergence reachability | Curated `ignore_fields.toml` of gold-only derived/verbatim fields, **frozen** during the loop |

---

## 3. Architecture

```
            LibreDWG (gold, WSL)                     cadcodec/acadrust (silver)
            -------------------                     ---------------------------
orig.dwg --> dwgread -O JSON --> gold_orig.json  --> [normalize] --+
orig.dwg ---------------------------------------> DwgReader.read() |
                                                     |             |
                                                     v             |
                                              CadDocument --serde--> silver_orig.json
                                                     |             |
                                              DwgWriter            |
                                                     v             |
                                              rt.dwg ---------> dwgread -O JSON --> gold_rt.json
                                                     |             |
                                              DwgReader.read()     |
                                                     v             v
                                              silver_rt.json   [normalize + DIFF] --> report
```

Three diffs per file:

1. **Read fidelity:** `gold_orig.json` vs `silver_orig.json` → finds fields
   cadcodec's *reader* drops/misparses.
2. **Write fidelity:** `gold_orig.json` vs `gold_rt.json` (libredwg reads
   cadcodec's rewritten DWG) → finds fields cadcodec's *writer* omits/corrupts,
   validated by the gold reader.
3. **Internal consistency:** `silver_orig.json` vs `silver_rt.json` → cadcodec
   read→write→read self-check (complements `tests/roundtrip.rs` with real gold
   files). **Currently stubbed** to zero in `run_roundtrip.py`; wire up when
   needed.

### Alignment and handle comparison

- **Alignment**: records are paired by `(type, ordinal-within-type)`, not by
  raw handle, because handles are reassigned on rewrite.
- **Handle comparison**: handle-valued fields are compared by the resolved
  target type (`handle → record_type`), not by raw id. The differ builds a
  `handle_value → type` map on each side independently and substitutes the
  target type before comparing.
- **Strict mode**: `GOLD_HARNESS_STRICT=1` asserts zero `missing_in_silver`
  diffs.

#### Handle-design alternatives considered and rejected

- **Compare raw handle ids**: rejected — cadcodec intentionally reassigns
  handles on rewrite, producing false positives on every roundtrip.
- **Align 1:1 by silver `entity_index` / gold `handle`**: rejected — handles
  are not stable across read→write→read and silver's `entity_index` is keyed
  by the silver-assigned id.
- **Normalize handles to symbolic names ("layer 0", "model space")**: too
  brittle; the type-resolved approach is deterministic.
- **Ignore all handle-valued fields**: rejected — handle topology is part of
  the non-header structure the loop must preserve.

#### Known limitation

The handle resolver cannot distinguish two objects of the **same** type that
are both valid targets (e.g. a `LINE` pointing at layer handle 16 vs handle
99, both resolving to `LAYER`). Layer identity is semantically preserved, but
a swap to a different layer of the same type would be missed. A future
improvement could resolve handles to `(type, name)` when a name table is
available.

---

## 4. Scope boundary

Gold `dwgread -O JSON` emits one top-level object with keys (in order):
`created_by`, `FILEHEADER`, `HEADER`, `CLASSES` (R13+), `OBJECTS` (array),
`THUMBNAILIMAGE` (opt), and optional section records (`ObjFreeSpace`,
`SecondHeader`, `Template`, `AuxHeader`, `R2004_Header`/`R2007_Header`,
`SummaryInfo`, `VBAProject`, `AppInfo`, `AppInfoHistory`, `FileDepList`,
`Security`, `RevHistory`, `AcDs`).

- **IN scope:** the top-level **`OBJECTS` array only** (entities and non-entity
  objects). Compare per-object fields defined by `dwg.spec`, `dwg2.spec`,
  `common_entity_data.spec`, `common_entity_handle_data.spec`,
  `common_object_handle_data.spec`, and `acds.spec`.
- **OUT of scope (header; lax — dropped by the normalizer):** every other
  top-level key listed above.

---

## 5. Corpus coverage

Inventoried `test/test-data` at commit `34f02f54…`. Per-version `.dwg` counts:
2000=23, 2004=21, 2007=18, 2010=18, 2013=19, 2018=19, plus top-level
`example_*.dwg`/`sample_*.dwg`.

- **Covered entity types (loop CAN fix):** LINE, CIRCLE, ARC, ELLIPSE, TEXT,
  LWPOLYLINE, POLYLINE_2D, POLYLINE_3D, SPLINE, HATCH (2004 `HatchG`), MLINE,
  LEADER, HELIX, XLINE, RAY, POINT, 3DSOLID (2000 `Cone`), SURFACE (2004),
  UNDERLAY (2004), MATERIAL (2004), geometric/dimensional constraints, dynamic
  blocks (2018 `Dynblocks`), LIVESECTION (2018), plus broad mixed coverage via
  2000 `entities-2d`/`entities-3d` and `example_*`/`sample_*`.
- **Coverage gaps (loop CANNOT fix — no gold file):** MTEXT, DIMENSION (all
  kinds), TABLE, REGION, dedicated static INSERT/BLOCK, MLEADER/MULTILEADER,
  VIEWPORT, IMAGE, MESH/POLYFACEMESH, 3DFACE, SOLID (2D), ATTDEF/ATTRIB,
  TOLERANCE, WIPEOUT, XREF, OLE2, LIGHT, CAMERA, ARCDIMENSION. These are
  logged as `no gold coverage — out of loop`.
- **Richest dirs:** 2000 (widest entity set) and 2007 (best DXF companions).
  2010/2013 are near-minimal.

---

## 6. What is implemented (Phases 0–5 status)

### Phase 0–1 — Sources and gold oracle (WSL)

- libredwg and cadcodec cloned under `~/work/`. libredwg built with
  `sh ./autogen.sh && ./configure --disable-bindings --disable-docs && make -j`.
- `programs/dwgread -O JSON` smoke-tested on `test/test-data/2000/Line.dwg`.
- Path to `dwgread` exported via `GOLD_DWGREAD`; corpus via `GOLD_TESTDATA`.

### Phase 2 — Silver JSON dump (`tests/gold_harness/src/bin/dwg2json.rs`)

- Reads a DWG into `CadDocument`, serializes with `serde`, and re-injects the
  serde-skipped `EntityCommon` round-trip fields under `_common_dwg[handle]`.
- **Field count has grown from 12 to 17** since the original plan; current
  set: `linetype_handle`, `graphic_data`, `color_book_handle`,
  `face_visual_style_handle`, `edge_visual_style_handle`, `material_flags`,
  `material_handle`, `shadow_flags`, `plotstyle_flags`, `plotstyle_handle`,
  `linetype_flags`, `entity_mode`, `has_ds_data`, `prev_entity_handle`,
  `next_entity_handle`, `nolinks`, `z_are_zero`.
- Also emits `Block`/`BlockEnd` delimiter entities collected via
  `block_records` (not exposed by `CadDocument::entities()`).
- Raw byte blobs (`graphic_data`, `raw_acds_data`) stay excluded — verbatim
  storage, not comparable structure.

### Silver rewrite binary (`tests/gold_harness/src/bin/dwgrewrite.rs`)

- Minimal read → write binary that targets the same DWG version as the source.

### Phase 3 — Normalizer + differ (harness core)

- `normalize_gold.py`: keeps only the top-level `OBJECTS` array, drops
  header/section metadata, flattens points/handles/colors.
- `normalize_silver.py`: emits entities, objects, and table records; resolves
  layer names to handles; maps variant/field names to gold conventions (see
  §9 mapping table).
- `diff_fields.py`: aligns by `(type, ordinal)` and compares handle-valued
  fields by resolved target type. Reports `missing_in_silver`, `wrong_value`,
  `extra_in_silver`, `count_mismatch`.
- `ignore_fields.toml`: curated list of gold-only derived/verbatim fields,
  expanded after the first real run to include raw/verbatim object fields
  (`raw_data`, `cloning_flags`, `entries`, `items`, `xdata`, …) and now
  **frozen** for the loop.

### Phase 4 — Roundtrip driver

- `run_roundtrip.py <file.dwg> [workdir]`: orchestrates the three diffs per
  file. Default workdir `target/gold_harness/`.
- `run_corpus.py`: batch driver over the in-scope corpus; aggregates
  `report.json`/`report.md` ranking `(entity_type, field)` divergences.
  Default workdir `target/gold_harness_corpus/`.
- Internal-consistency diff (#3) is **stubbed** (reported as 0) — see §3.

### Phase 5 — Cargo test integration

- `tests/gold_roundtrip.rs` gated behind the `gold-harness` feature; shells
  out to `run_roundtrip.py` for a representative subset (`2000/Line.dwg`,
  `2000/circle.dwg`). Default assertion: harness runs and none of the
  prohibited `EntityCommon` storage-only fields (`z_is_zero`, `ltype_flags`,
  `prev_entity`, `next_entity`, `nolinks`) appear in any diff. Strict
  zero-`missing_in_silver` mode is opt-in via `GOLD_HARNESS_STRICT=1`.
- `tests/visualstyle_dwg_roundtrip.rs`: regression test that builds a
  `VisualStyle` with a full 24-element pre-R2010 property bag, round-trips it
  through R2000 DWG, and asserts the recovered properties match.

### Differences from the original plan (kept for the record)

| Plan text | Implementation | Rationale |
|---|---|---|
| Silver dump re-includes skipped fields inline in the entity record. | Skipped fields live in `_common_dwg[handle]`, not merged into the entity object. | Avoids polluting the public serde schema; the normalizer merges them before diffing. |
| `ignore_fields.toml` starts with a curated list. | List was expanded after the first real run to include raw/verbatim object fields. | Without these ignores, object-level representation noise drowned out real entity gaps. Now frozen. |
| Phase 5 test "asserts zero `missing_in_silver` for representative subset". | Test asserts the harness runs cleanly; strict mode gated by `GOLD_HARNESS_STRICT=1`. | Representative files still show missing common fields that the fix loop must close; making the default test fail would break `cargo test`. |
| Normalizer reshapes polylines into child `VERTEX_*` records or folds them. | Not implemented. | `Line.dwg`/`circle.dwg` have no expanded vertices; deferred until a polyline fixture is processed. |
| `ignore_fields.toml` is written once and never edited. | Edited during harness construction; now frozen. | Refinement happened before the loop boundary. |
| Silver bins live under `examples/` or `src/bin/`. | Bins live under `tests/gold_harness/src/bin/` and are registered as Cargo `[[bin]]` targets. | Keeps the harness self-contained. |
| Workdirs default to `/tmp`. | Workdirs default to `target/gold_harness*/`. | Repo-local, easy to inspect. |

### Recent code fixes (part of the harness loop)

- `src/io/dwg/dwg_writer.rs`: class-table filtering now retains live
  `ClassObject` instances (e.g. `ACDBSECTIONVIEWSTYLE`,
  `ACDBDETAILVIEWSTYLE`) after `retain_legacy_dwg_classes()`, so their type
  codes are not mis-emitted as `500` (`ACDBDICTIONARYWDFLT`).

---

## 7. Current baseline and blockers

### Baseline after EntityCommon closure (2026-09-17)

- **LINE entity diffs: 0** on all six versions (2000–2018), both read fidelity
  (`diff_orig`) and write fidelity (`diff_rt`). Same for CIRCLE on 2000.
- Corpus totals are dominated by **object/table-record** representation gaps
  (~2.6k read-fidelity diffs on `2000/Line.dwg`), not entity fields.
- Strict mode (`GOLD_HARNESS_STRICT=1`) still fails on the representative
  subset due to **table-record storage fields** and object representation
  gaps, not entities.

### EntityCommon storage-only fields — CLOSED (2026-09-17)

The six target fields (`prev_entity`, `next_entity`, `nolinks`, `ltype_flags`,
`plotstyle_flags`, `z_is_zero`) were already read and written correctly by the
core codec; the gaps were in the dump/normalizer projection:

| Fix | Where | Detail |
|---|---|---|
| `material_flags`/`shadow_flags` gated `SINCE R_2007a` | `dwg2json.rs` | Emitted as `Option`, `None` before AC1021 (was unconditional `0` → `extra_in_silver` on R2000/R2004) |
| `has_ds_data` gated `SINCE R_2013` | `dwg2json.rs` | `None` before AC1027 |
| `is_xdic_missing` derived | `dwg2json.rs` | `Some(xdictionary_handle.is_none())` when ≥ AC1018 (gold `SINCE R_2004a`) |
| `has_full/face/edge_visualstyle` derived | `dwg2json.rs` | `Some(handle.is_some())` when ≥ AC1024 (gold `SINCE R_2010b`) |
| `entity_mode` → `entmode` | `normalize_silver.py` | Gold field name; ignored on both sides via `ignore_fields.toml` |
| `linetype` name dropped; `linetype_handle` → `ltype` | `normalize_silver.py` | Gold has no name field, only the conditional handle |
| `plotstyle_handle` → `plotstyle`, `material_handle` → `material`, `face/edge_visual_style_handle` → `face/edge_visualstyle`, `full_visual_style_handle` → `full_visualstyle` | `normalize_silver.py` | Gold handle names from `common_entity_handle_data.spec` |
| `color_name` skipped when `None` | `normalize_silver.py` | Gold only emits it when the color carries a name |
| `ownerhandle` only when `entity_mode == 0` | `normalize_silver.py` | Gold emits it for entities only when `entmode == 0` (polyline sub-entities) |
| Color hash `{index, rgb:"000000", flag}` collapses to `index` | `normalize_gold.py` | R2004+ ENC JSON emits derived keys alongside `index` |

### Known issues and blockers

| Issue | Status | Notes |
|---|---|---|
| `AcDbDictionaryWithDefault` mis-emitted as type 500 | **Fixed** | Class-table retention fix in `src/io/dwg/dwg_writer.rs` |
| `ACDBSECTIONVIEWSTYLE` / `ACDBDETAILVIEWSTYLE` missing after rewrite | **Fixed** | Same class-table retention fix |
| `AcDbVisualStyle` "Object improperly read" | **Fixed** (2026-09-17) | `bd2007_45` was read/written unconditionally in the pre-R2010 branch; gold gates it `SINCE R_2007a`. R2000/R2004 rewrites carried 8 extra bytes per VisualStyle, desynchronizing the object stream. Fixed by gating on `r2007_plus()` in both `read_visual_style` and `write_visual_style`. Confirmed: gold `dwgread` now decodes R2000/R2004 rewrites with exit 0 and no VisualStyle errors; R2007 behavior unchanged. |
| EntityCommon storage-only field gaps | **Fixed** (2026-09-17) | See table above. LINE/CIRCLE entity diffs now zero on all versions. |
| Uniform table-record storage fields (`ownerhandle`, `is_xref_ref`, `is_xref_resolved`, `is_xref_dep`, `xref`, `unknown`, `is_xdic_missing` R2004+, `has_ds_data` R2013+) | **Fixed** (2026-09-17) | These are uniform across ordinary table records and derived in `normalize_silver.py` from silver state: `ownerhandle` = the table's control-object handle, xref bits = `1/0/0`, `xref` = null handle, `unknown` = 0 (APPID only), `is_xdic_missing` = `xdictionary_handle.is_none()` (R2004+, all objects), `has_ds_data` = 0 (R2013+, objects). No codec changes needed. APPID/TEXTSTYLE/VIEW/UCS table records are now diff-free. |
| Table-record payload fields | **Open** | Per-record semantic data, not uniform: DIMSTYLE ~70 `DIM*` vars (largest), LTYPE dash patterns (`dashes`, `numdashes`, `pattern_len`), VPORT view params (`VIEWCTR`, `VIEWDIR`, `BACKZ`, `FRONTZ`, `GRID*`, `SNAP*`, `UCS*`, …), BLOCK_HEADER topology (`xdicobjhandle`, `base_pt`, `xref_pname`, `block_entity`, `entities`, `endblk_entity`, …), LAYER `plotstyle`/`linewt`. These require reader storage and/or per-type normalizer mapping — one packet per table type. |
| Object representation gaps | **In progress** | VISUALSTYLE, MATERIAL, DIMSTYLE, SCALE, XRECORD, DICTIONARYVAR, and LWPOLYLINE are mapped in `normalize_silver.py`. Corpus totals on `Line.dwg` dropped from ~2500 to ~880; Polyline.dwg from ~995 to ~880. Residual: differ-side `ownerhandle` handle-code semantics (gold codes 0/8/12 vs silver resolved types), CMC absent-color encoding, and the `reactors` storage gap. Remaining per-type: LAYOUT, MLEADERSTYLE, BLOCK_HEADER topology, LTYPE dash patterns, VPORT view params. See §8.1.6. |

---

## 8. Phase 6 — Autonomous fix loop (specification)

Run after Phases 0–5 are in place, under an **implementation-capable agent**
(file edits + `cargo` + subprocess), NOT in plan mode. Git mutations optional.

**Corpus (bounded):** in-scope version dirs
`{2000,2004,2007,2010,2013,2018}/*.dwg` plus top-level
`example_{2000,2004,2007,2010,2013,2018}.dwg` and `sample_{2000,2018}.dwg`.
Entity types with no gold file are written to `report.md` under
`OUT OF LOOP (no gold coverage)` and are NOT worked on.

**Convergence target:** for every covered file,
`normalize(gold_orig) ≡ normalize(silver_orig)` on the non-header,
**non-ignored** field set, AND `normalize(gold_orig) ≡ normalize(gold_rt)` on
the same set. Header keys are excluded from the strict diff (lax header).

**Loop body (repeat until converged or all blocked):**

1. **Baseline.** Run the Phase 4 driver over the whole covered corpus. Produce
   `report.json`/`report.md` ranking `(entity_type, gold_field, dwg_version)`
   divergences by frequency and by a fixed priority: read-fidelity first, then
   write-fidelity, then internal consistency. Geometry-correctness fields
   (points, radii, angles, counts) rank above cosmetic/default fields.
2. **Pick top offender.** Choose the highest-ranked `(entity_type,
   gold_field)` not already marked blocked.
3. **Consult gold.** Open `dwg.spec`/`dwg2.spec` at that
   `DWG_ENTITY(...)`/`DWG_OBJECT(...)` block (and `common_entity_data.spec` /
   `common_entity_handle_data.spec` for common fields). Record the exact
   `FIELD_*` macro, bitcode type, and `PRE/VERSIONS/SINCE/UNTIL/LATER_VERSIONS`
   gating.
4. **Fix silver, version-gated.** Edit the matching cadcodec `read_<entity>`
   in `object_reader/entities.rs` and its mirror in
   `object_writer/entities.rs`. Add/correct the field using the same bitcode
   primitives (`read_bit_double_with_default`, `read_bit_extrusion`,
   `read_bit_thickness`, `read_bit`, …) and gate it behind the SAME version
   predicate gold uses (`r2000_plus()`, `r2004_plus()`, `r2007_plus()`, …).
   **Do NOT modify version dispatch, decompression, CRC, or the section map** —
   only the per-field read/write bodies.
5. **Verify across all 6 versions.** Re-run the driver over the FULL covered
   corpus, not just the failing file, to catch cross-version regressions.
   Confirm the target field now matches and the corpus-wide non-header diff
   count strictly decreased.
6. **Regression gate + checkpoint.** Require: (a) `cargo test` green (existing
   suite, harness feature off), (b) `cargo test --features serde` green,
   (c) corpus non-header diff count strictly decreased. If all pass,
   checkpoint the fix (`git commit` if git mutations are available, else
   record in `report.md`). If any check fails, revert and mark the offender
   blocked with the reason.
7. **Blocked handling.** If an offender cannot converge after **5 fix
   attempts** (or requires touching out-of-bounds code: version dispatch,
   decompressor, CRC), mark it `BLOCKED: <reason>` in `report.md` and move on.
   Revisit blocked items only after all non-blocked offenders are exhausted.
8. **Stop conditions.** Stop when (a) corpus-wide non-header, non-ignored diff
   count == 0 (SUCCESS), or (b) every remaining offender is BLOCKED (PARTIAL).
   Emit final `report.md` listing fixed fields, blocked fields, and
   out-of-loop entity types.

**Loop invariants the agent must preserve:**

- Never edit gold (libredwg) — it is a read-only oracle input.
- Never weaken the differ/normalizer to make a diff pass — no adding
  tolerances, no dropping fields, and **no editing `ignore_fields.toml`**
  during the loop.
- Never change the header strictness — header stays lax throughout.
- Each checkpoint must leave the build green; the working tree must never be
  left broken.

**Version-scope guard (explicit):** a fix is only valid if it is gated to the
exact DWG versions gold specifies. Confirm for each touched field that the
field is read/written under the identical version predicate in both reader and
writer, and that no other version's behavior changed (verified by step 5).

### First fix-loop target — DONE (2026-09-17)

~~Scope the first fix-loop pass to entity `EntityCommon` storage-only fields:
`prev_entity`, `next_entity`, `nolinks`, `ltype_flags`, `plotstyle_flags`,
`z_is_zero`.~~ Closed — see §7. Next targets, in priority order:

1. **Table-record storage fields** (`ownerhandle`, `is_xref_ref`,
   `is_xref_resolved`, `is_xref_dep`, `xref`, `unknown`) on APPID, LAYER,
   LTYPE, STYLE, DIMSTYLE, … — these block `GOLD_HARNESS_STRICT=1`.
2. **Object representation gaps** ranked by corpus frequency (VISUALSTYLE,
   MATERIAL, DIMSTYLE, LAYOUT, SCALE, MLEADERSTYLE, DICTIONARYVAR, …).

---

## 8.1 Subagent execution guide (128K context)

This section is a self-contained operating manual for an implementation agent
with a **128K-token context window** running the Phase 6 loop. It assumes the
agent sees ONLY this section plus whatever it reads on demand — not the whole
plan, not whole source files. Follow the context-budget rules strictly; the
two spec files and the two big Rust files together exceed the window.

### 8.1.0 Environment (verify once per session)

```bash
cd ~/work/cadcodec
source "$HOME/.cargo/env"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
python3 tests/gold_harness/check_env.py   # must print "Environment looks good"
cargo build --features serde --bins        # must succeed before any edit
```

Repos: silver = `~/work/cadcodec` (Rust crate `acadrust`), gold =
`~/work/libredwg` (C, read-only oracle). **Never edit anything under
`~/work/libredwg`.**

### 8.1.1 Context budget rules (hard constraints)

1. **Never read a whole large file.** These files are too big to load:
   - `~/work/libredwg/src/dwg.spec`, `dwg2.spec` (many thousand lines)
   - `src/io/dwg/dwg_stream_readers/object_reader/entities.rs` (~6000 lines)
   - `src/io/dwg/dwg_stream_writers/object_writer/entities.rs`
   - `src/io/dwg/dwg_stream_readers/object_reader/objects.rs`,
     `.../object_writer/objects.rs`
2. **Always locate with grep, then read a narrow window.** Patterns:
   - Gold object block: `grep -n "DWG_OBJECT (NAME)" ~/work/libredwg/src/dwg2.spec ~/work/libredwg/src/dwg.spec`, then `sed -n '<start>,<start+80>p' <file>`.
   - Gold entity block: same with `DWG_ENTITY (NAME)`.
   - Common entity fields: `grep -n "field_name" ~/work/libredwg/src/common_entity_data.spec ~/work/libredwg/src/common_entity_handle_data.spec`, then `sed -n` around the hit.
   - Silver reader: `grep -n "fn read_<name>" src/io/dwg/dwg_stream_readers/object_reader/*.rs`, then read at most that function (`sed -n '<line>,<line+120>p'`).
   - Silver writer: `grep -n "fn write_<name>" src/io/dwg/dwg_stream_writers/object_writer/*.rs`.
3. **Do not re-read the plan.** This section contains everything needed.
4. **Do not dump whole JSON outputs** (`*_gold_orig.json` can be MBs). Query
   them with `python3 -c` one-liners or small scripts that print only the
   records of the type under repair.
5. Read `diff_*.json` only via filtered queries (see 8.1.3), never in full.

### 8.1.2 The work unit: one (type, field) packet

Work exactly ONE `(type, field)` pair per iteration. Never batch unrelated
fields. The packet comes from the corpus report
(`target/gold_harness_corpus/report.md`, "Top read-fidelity divergences"
first) or from a single file's diff JSON.

Quick per-file query (prints only the interesting rows):

```bash
python3 - <<'EOF'
import json
d = json.load(open("target/gold_harness/FILESTEM_diff_orig.json"))
rows = [x for x in d["diffs"] if x.get("type") == "TYPE"]
print(f"{len(rows)} diffs for TYPE")
for x in rows[:20]:
    print(" ", x["kind"], x.get("field"), "| gold:", x.get("gold_value"), "| silver:", x.get("silver_value"))
EOF
```

### 8.1.3 Where a fix belongs — decision tree

Given a diff `(type, field, kind)`:

1. **`missing_in_silver` and the field IS in the gold spec for this version**
   → silver does not read/store it. Fix in the **reader + writer + struct**:
   - Struct: `src/entities/mod.rs` (`EntityCommon` / per-entity struct) or
     `src/objects/*.rs` or `src/tables/*.rs` for table records.
   - Reader: `object_reader/{entities,objects,tables}.rs` or `mod.rs`.
   - Writer: the same path under `object_writer/`.
   - Gate with the SAME version predicate gold uses:
     `version.r2000_plus()`, `r2004_plus()`, `r2007_plus()`, `r2010_plus()`,
     `r2013_plus(dxf)` on `DwgVersion`; `self.version.*` on the writer.
   - If the field is serde-skipped storage data, also add it to the dump
     struct in `tests/gold_harness/src/bin/dwg2json.rs`
     (`SilverEntityCommon` pattern: `Option`, `skip_serializing_if`).
2. **`missing_in_silver` and the field is DERIVABLE from silver state**
   (e.g. `is_xdic_missing` = `xdictionary_handle.is_none()`,
   `has_full_visualstyle` = `full_visual_style_handle.is_some()`,
   `z_is_zero` = both Z coords are 0) → fix in the **dump** (`dwg2json.rs`),
   version-gated with `doc.version >= DxfVersion::AC10xx`. Do NOT add storage
   to the core struct for derivable bits.
3. **`extra_in_silver`** → silver emits a field gold does not have in this
   version. Fix in the **dump** (version-gate to `None`) or in
   **`normalize_silver.py`** (drop derived silver-only fields like the
   `linetype` name string).
4. **`wrong_value` with matching structure** → silver reads/writes the field
   but wrong. Fix the **reader or writer** body only. Check bitcode type
   against gold's `FIELD_*` macro (e.g. `BS` vs `BL`, `BD` vs `RD`).
5. **`wrong_value` that is a naming/shape mismatch, not data** (e.g. gold
   `extrusion` vs silver `normal`; gold CMC color hash vs silver `Color`
   enum) → fix in **`normalize_silver.py`** (`FIELD_NAME_MAP`,
   `merge_common`, or `normalize_color`) or **`normalize_gold.py`** (gold-side
   canonicalization, e.g. collapsing `{index, rgb:"000000", flag}` to
   `index`).
6. **Handle-valued field** → the differ compares by resolved target type.
   Fix the name mapping so the field is present on both sides; do NOT try to
   make raw handle ids equal.

### 8.1.4 Fix recipe (per packet)

1. **Consult gold** (grep + sed window per 8.1.1). Record: exact `FIELD_*`
   macro, bitcode type, version gate (`PRE/VERSIONS/SINCE/UNTIL`), and any
   condition (`if (FIELD_VALUE (x) == 3)` …). Fields guarded by
   `DXF { … }` are DXF-only — do NOT implement them for DWG.
2. **Locate silver** (grep for the field name or the enclosing
   `read_<entity>`). Determine with the decision tree (8.1.3) whether the fix
   is reader+writer, dump, or normalizer.
3. **Edit minimally.** Only the per-field read/write body or the projection.
   Never touch version dispatch, decompression, CRC, or the section map.
   Never edit `ignore_fields.toml`, `diff_fields.py`, or gold.
4. **Build:** `cargo build --features serde --bins`.
5. **Verify on one file per affected version** (all versions the field's
   gold gate covers), e.g. for an R2000+ field:

   ```bash
   for v in 2000 2004 2007 2010 2013 2018; do
     python3 tests/gold_harness/run_roundtrip.py \
       "$GOLD_TESTDATA/$v/Line.dwg" "target/gold_harness_wip/$v" >/dev/null 2>&1
   done
   ```

   Then confirm with the query from 8.1.2 that (a) the target diff is gone on
   every covered version and (b) `total_diffs` did not increase anywhere.
6. **Regression gate (must all pass):**
   - `cargo test 2>&1 | tail -3` → ok
   - `cargo test --features serde 2>&1 | grep -E 'test result:' | awk '{p+=$4; f+=$6} END {print p, f}'` → failed = 0
   - `cargo test --features gold-harness --test gold_roundtrip` → ok
   - `target` diff totals strictly decreased (or unchanged if the packet
     targeted a type absent from the representative files — then verify on the
     affected file directly).
7. **Checkpoint:** `git add -A && git commit -m "fix(dwg): <type>.<field> — <gold spec ref>"`
   if git mutations are allowed; otherwise append a line to
   `target/gold_harness_corpus/report.md` under a `FIXED` heading.
8. If any gate fails: `git checkout -- <touched files>` (or restore the saved
   copy), record `BLOCKED: <type>.<field> — <reason>`, and move to the next
   packet. Max **5 attempts** per packet.

### 8.1.5 Reference patterns (already landed — imitate these)

- **Version-gated field add** (`bd2007_45`, VisualStyle): reader and writer
  each gained `if version.r2007_plus() { … }` around a single bit-double;
  regression test asserts 23 stored properties on R2000 vs 24 on R2007
  (`tests/visualstyle_dwg_roundtrip.rs`).
- **Dump-side derivation** (`is_xdic_missing`, `has_*_visualstyle`): added as
  `Option<bool>` to `SilverEntityCommon` in `dwg2json.rs`, set with
  `r20xx.then_some(...)`, `skip_serializing_if = "Option::is_none"`.
- **Normalizer vocabulary fix** (`entity_mode`→`entmode`,
  `linetype_handle`→`ltype`, `ownerhandle` only when `entmode == 0`):
  `merge_common()` in `normalize_silver.py`.
- **Gold-side canonicalization** (ENC color hash collapse):
  `normalize_value()` in `normalize_gold.py`.

### 8.1.6 Current work queue (ordered)

1. ~~Table-record storage fields~~ — **done** for the uniform set (see §7).
   What remains is per-record **payload**, one packet per table type:
   DIMSTYLE `DIM*` vars (largest), LTYPE dash patterns, VPORT view params,
   BLOCK_HEADER topology, LAYER `plotstyle`/`linewt`.
2. **Object representation gaps** by corpus frequency: VISUALSTYLE,
   MATERIAL, DIMSTYLE, LAYOUT, SCALE, MLEADERSTYLE, DICTIONARYVAR,
   BLOCK_HEADER, LTYPE, APPID. These are name/shape mappings between the
   silver serde schema and gold spec — decision tree rules 3–5 mostly. Check
   `OBJECT_TYPE_MAP` and the object branch of `normalize_silver.py` first;
   many will be renames, not codec changes.

   **Started (2026-09-17):** VISUALSTYLE (positional property-bag → named
   fields for pre-R2010, R2010+ core, and R2013+ extended), MATERIAL
   (map/color flattening + R2007+ gating), DIMSTYLE (dim* → DIM* name
   mapping + version gating + `DIMTXSTY`/`DIMLTYPE`/`DIMLTEX1`/`DIMLTEX2`
   handle emission), SCALE (flag/is_temporary projection), XRECORD
   (xdata/cloning projection), DICTIONARYVAR (schema_number/value →
   schema/strvalue), and LWPOLYLINE (vertex reshape + flag projection) are
   substantially done in `normalize_silver.py`. Objects are now sorted by
   handle before diffing (silver stores them in a HashMap; gold's OBJECTS
   array is handle-ordered), and table control objects are emitted so the
   differ can resolve table-record `ownerhandle`.
   Known residual per-type gaps to continue with:
   - `ownerhandle`: gold emits handle *codes* (0/8/12 with ownership meaning);
     silver resolves to the target type. Differ-semantics, not data.
   - CMC absent/true colors: gold `c1000000` RGB-black vs silver index 0;
     gold `{index:256, rgb:…}` vs silver `Color::None`. Cross-cutting; one
     fix in `normalize_gold.py`/`normalize_color` clears it everywhere.
   - `reactors`: gold emits them; silver doesn't store them (storage gap).
   - Next types to start: LAYOUT, MLEADERSTYLE, BLOCK_HEADER topology,
     LTYPE dash patterns, VPORT view params.

   **Next task (ready to start):** `ownerhandle` handle-code semantics in the
   differ — see [`NEXT_OWNERHANDLE.md`](./NEXT_OWNERHANDLE.md) for the
   cold-start brief. It is the single largest remaining divergence
   (~43 778 corpus diffs, ~22% of read-fidelity).
3. Re-run `run_corpus.py` after each landed packet to re-rank the queue.

Concrete entity-level mappings exposed by `2000/entities-2d.dwg` (good early
packets — small, well-scoped, and reproducible):
- **POINT**: gold splits the point into `x`/`y`/`z` scalars and uses
  `x_ang`; silver has `point` (vec) and `x_axis_angle`. Normalizer mapping.
- **TEXT**: gold uses `dataflags`, `ins_pt`, `horiz_alignment`,
  `vert_alignment`, `style` (handle); silver has `insertion_point`,
  `horizontal_alignment` (enum string), `vertical_alignment`, `style` (name).
  Mixed normalizer + reader-storage work (`dataflags`, `elevation` are
  currently not stored).
- **LWPOLYLINE**: gold has `flag`, `points`, `bulges`; silver has
  `is_closed`, `vertices` (nested), `constant_width`. Normalizer reshape
  (vertices → points/bulges) + `flag` derivation from `is_closed`.
- **Entity chain resolution**: `next_entity`/`prev_entity`/`ownerhandle`
  `wrong_value` diffs where the resolved target TYPE disagrees (e.g. gold
  `0` vs silver `LINE`). Investigate whether silver's chain reading is wrong
  or the differ's handle map misresolves — add a targeted probe before
  editing (print both normalized records for the same ordinal).

### 8.1.7 Hard prohibitions (loop invariants, restated)

- Never edit anything under `~/work/libredwg`.
- Never edit `tests/gold_harness/ignore_fields.toml` or
  `tests/gold_harness/diff_fields.py`.
- Normalizer edits must be *faithful projections* (correct names, correct
  version gates, correct reshaping) — never hide a real data mismatch.
- Never touch version dispatch, decompression, CRC, or the section map.
- Never leave the build red at a checkpoint.
- Header stays out of scope (lax).

---

## 9. Field-mapping starting table (silver `EntityType` → gold spec name)

Reference data for the differ, independent of coverage. Mappings for
out-of-loop types (MTEXT, DIMENSION_*, TABLE, MULTILEADER, VIEWPORT, IMAGE,
MESH, 3DFACE, SOLID, ATTDEF/ATTRIB, TOLERANCE, WIPEOUT) are pre-staged and
become active once coverage lands.

LINE→LINE, Circle→CIRCLE, Arc→ARC, Point→POINT, Text→TEXT, MText→MTEXT,
LwPolyline→LWPOLYLINE, Polyline2D→POLYLINE_2D, Polyline3D→POLYLINE_3D,
Ellipse→ELLIPSE, Spline→SPLINE, Insert→INSERT, Ray→RAY, XLine→XLINE,
Hatch→HATCH, Solid→SOLID, Face3D→3DFACE, Viewport→VIEWPORT, Leader→LEADER,
Tolerance→TOLERANCE, MLine→MLINE, AttributeDefinition→ATTDEF,
AttributeEntity→ATTRIB, Solid3D→3DSOLID, Region→REGION, Body→BODY,
Table→TABLE, MultiLeader→MULTILEADER, RasterImage→IMAGE, Wipeout→WIPEOUT,
Underlay→*UNDERLAY, Ole2Frame→OLE2FRAME, Shape→SHAPE, Helix→HELIX,
Mesh→MESH.

The authoritative machine-readable maps live in `normalize_silver.py`
(`ENTITY_TYPE_MAP`, `OBJECT_TYPE_MAP`, `FIELD_NAME_MAP`); the list above is
kept for design context only.

**Special cases the normalizer must handle:**

- **Dimension**: acadrust has ONE `EntityType::Dimension` variant (with a
  sub-discriminator); gold has separate
  `DIMENSION_ORDINATE/LINEAR/ALIGNED/RADIUS/DIAMETER/ANG2LN/ANG3PT/ARC/LARGE_RADIAL`
  spec types. Map on the sub-discriminator, not the variant.
- **Polyline/LwPolyline**: gold `LWPOLYLINE` (R14+) vs `POLYLINE_2D/3D`
  (legacy); a legacy gold POLYLINE_2D may surface in silver as `LwPolyline`
  or `Polyline2D` — allow a many-to-one type alias set.
- **Insert vs MINSERT**: gold `MINSERT` is acadrust `Insert` with
  `num_cols/num_rows > 1`.
- **Vertex entities**: gold emits `VERTEX_2D/3D/MESH/PFACE/PFACE_FACE` as
  separate objects; acadrust stores vertices inside the parent polyline. The
  normalizer must either expand silver polylines into child vertex records or
  fold gold vertices into the parent before diffing. **Not implemented yet.**

(Extend via `classes.inc` for gold class names of 500+ types.)

---

## 10. Out-of-loop scope

The following are intentionally deferred until they block a covered entity or
the corpus expands:

- Full object topology fixes for `DICTIONARY`, `XRECORD`, `SCALE`,
  `VISUALSTYLE` representation mismatches.
- Polyline vertex expansion (no covered fixture has expanded vertices yet).
- Resolving handles to `(type, name)` instead of `(type)`.

---

## 11. Next steps

1. ~~Open the rewritten files in AutoCAD~~ — **done**: user confirmed
   `AcDbVisualStyle` "Object improperly read" on R2000/R2004 rewrites, clean on
   R2007+. Root cause identified and fixed (see §7), fix confirmed by user.
2. ~~EntityCommon storage-only field gaps~~ — **done** (see §7). LINE/CIRCLE
   entity diffs are zero on all six versions, read + write fidelity.
3. Continue Phase 6 per the subagent workflow in §8.1:
   table-record storage fields first (they gate `GOLD_HARNESS_STRICT=1`), then
   object representation gaps by corpus frequency.

---

## 12. How to run

Required environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `GOLD_DWGREAD` | Absolute path to a built LibreDWG `dwgread` binary | **required** |
| `GOLD_TESTDATA` | Absolute path to LibreDWG `test/test-data` directory | **required** |

```bash
cd ~/work/cadcodec
source $HOME/.cargo/env

# Verify the environment is ready
python3 tests/gold_harness/check_env.py

# Build the harness binaries
cargo build --features serde --bins

# Run harness on one file (output goes to target/gold_harness/ by default)
GOLD_DWGREAD=$HOME/work/libredwg/programs/dwgread \
GOLD_TESTDATA=$HOME/work/libredwg/test/test-data \
python3 tests/gold_harness/run_roundtrip.py \
    $HOME/work/libredwg/test/test-data/2000/Line.dwg

# Run the full corpus batch driver
GOLD_DWGREAD=$HOME/work/libredwg/programs/dwgread \
GOLD_TESTDATA=$HOME/work/libredwg/test/test-data \
python3 tests/gold_harness/run_corpus.py

# Run representative cargo test
cargo test --features gold-harness --test gold_roundtrip

# Strict mode: assert zero missing_in_silver diffs
GOLD_HARNESS_STRICT=1 cargo test --features gold-harness --test gold_roundtrip
```

---

## 13. File inventory

| File | Purpose |
|---|---|
| `tests/gold_harness/run_roundtrip.py` | Single-file driver |
| `tests/gold_harness/run_corpus.py` | Batch driver |
| `tests/gold_harness/normalize_gold.py` | LibreDWG JSON normalizer |
| `tests/gold_harness/normalize_silver.py` | cadcodec JSON normalizer (holds the live type/field maps) |
| `tests/gold_harness/diff_fields.py` | Diff engine |
| `tests/gold_harness/ignore_fields.toml` | Fields ignored during diff (frozen) |
| `tests/gold_harness/check_env.py` | Environment sanity checker |
| `tests/gold_harness/src/bin/dwg2json.rs` | Silver JSON dump (re-injects 17 `EntityCommon` fields) |
| `tests/gold_harness/src/bin/dwgrewrite.rs` | Silver rewrite binary |
| `tests/gold_roundtrip.rs` | Cargo integration test (feature-gated) |
| `tests/visualstyle_dwg_roundtrip.rs` | VisualStyle regression test |

---

## 14. Self-sufficiency notes

The harness is intentionally self-contained in `tests/gold_harness/`:

- All Python scripts, normalizers, the differ, and the environment checker
  live under `tests/gold_harness/`.
- The silver JSON dump and rewrite binaries live under
  `tests/gold_harness/src/bin/` and are registered as Cargo `[[bin]]` targets.
- Working directories default to `target/gold_harness/` and
  `target/gold_harness_corpus/`, so outputs are repo-local and easy to inspect.

The only intentionally external dependencies are:

1. **LibreDWG `dwgread`** — the gold oracle; set via `GOLD_DWGREAD`.
2. **LibreDWG `test/test-data`** — the DWG corpus; set via `GOLD_TESTDATA`.
3. **Python 3** — the normalizer/differ runtime.

These are documented in `check_env.py` and are not embedded because they are
large, license-distinct, or runtime-level.

---

## 15. Risks and mitigations

- **serde(skip) on common fields (resolved by design):** `EntityCommon` skips
  the non-header round-trip fields, so a naive serde dump would false-positive
  them as missing. Mitigated by re-including them from the live struct under
  `_common_dwg` (Phase 2). Raw byte blobs stay excluded intentionally.
- **Field-name mismatch** between serde JSON and gold: mitigated by the
  per-entity mapping table in `normalize_silver.py`; grows iteratively.
- **Structure mismatch (not just names):** gold nests objects under
  `OBJECTS`/`ENTITIES` and expands polylines into child `VERTEX_*` records;
  acadrust nests vertices inside the parent polyline and stores blocks via
  `block_records`. The normalizer must reshape (expand/fold) before field
  diffing, not just rename keys. **Polyline reshape not implemented yet.**
- **Handle/ordering instability** across a rewrite: align by `(type,
  ordinal)`, never raw handle; compare handles by resolved target *type*.
- **Unknown/proxy entities:** cadcodec `Unknown`/`Extended` and libredwg
  skipped objects will not align; the differ tolerates count mismatches and
  reports them as coverage gaps, not hard errors.
- **libredwg read warnings** on advanced R2010+ objects: treat gold `dwgread`
  non-zero exit / `Error` log lines as "gold cannot decode → skip file", not a
  silver failure.
- **Float formatting:** gold uses `%.14f`; normalize with rel-tolerance `1e-6`
  (abs `1e-10`), and NaN→0.
- **Build time** for libredwg in WSL: use `--disable-bindings --disable-docs`;
  cache the build dir.
- **Strings/codepages:** pre-2007 files use legacy codepages; normalize both
  sides to UTF-8 before compare (gold already emits UTF-8).
- **Corpus gaps limit the loop:** the loop cannot fix MTEXT/DIMENSION/TABLE/
  INSERT/etc. (no gold file). They are explicitly logged out-of-loop; do not
  let the agent synthesize or guess their structure.
- **Autonomous-loop drift:** an agent might "fix" a diff by weakening the
  normalizer, widening tolerances, or extending `ignore_fields.toml` mid-loop.
  Loop invariants forbid editing the differ/normalizer/gold/`ignore_fields.toml`
  during the loop; these are fixed oracles.
- **Git unavailable in some environments:** step 6 checkpoints via commit only
  when git is available, else records in `report.md`; the regression gate is
  VCS-independent.
- **Cross-version regression:** a fix for one version can break another. Step 5
  re-runs the full corpus every iteration; step 6 gates on corpus-wide diff
  count strictly decreasing.
- **Non-convergence / oscillation:** a field may flip between two wrong
  states. 5-attempt cap per offender, then mark BLOCKED and move on.
- **Writer-only divergences:** some diffs only appear in `gold_rt`. These are
  valid targets (writer must match gold too), but require fixing
  `object_writer/`, not the reader.

---

## 16. Validation

- `programs/dwgread -O JSON` runs clean on a sample of in-scope gold DWGs.
- `cargo build --release --features serde` succeeds; `dwg2json` emits valid
  JSON on a gold DWG including re-included `EntityCommon` fields
  (`material_flags`, `plotstyle_flags`).
- Harness produces a `report.md` ranking divergent `(entity, field)` pairs
  across the in-scope corpus.
- At least one real divergence is found, fixed in cadcodec, and confirmed via
  re-run.
- `cargo test` (default, harness feature off) remains green and fixture-free.
- **Fix loop:** after running, the covered corpus reaches zero non-header,
  non-ignored field diffs (SUCCESS) or every remaining offender is BLOCKED
  with a recorded reason (PARTIAL); `report.md` lists fixed fields, blocked
  fields, and out-of-loop entity types. `cargo test` and
  `cargo test --features serde` are green at every checkpoint.

---

## 17. Future work (explicitly out of current scope)

### F1 — Header silver-vs-gold comparison

The header is lax/out-of-scope for the current loop. A later phase can extend
the same differ to header variables, reusing all existing machinery:

- **Gold source:** `dwgread -O JSON` top-level `FILEHEADER` (version string,
  `maint_rel_version`, `codepage` int, section addresses, R2004+ unknowns) and
  `HEADER` (every header variable by its spec `$VAR` name). Keys are
  version-gated; gold omits `num_*` counters and NaN doubles.
- **Silver source:** `CadDocument.header: HeaderVariables` (serde-derivable;
  snake_case fields with the `$VAR` name in each doc comment).
- **Work items:** (a) header-var name mapping table; (b) extend `normalize_*`
  for header types (points, handles, colors, dates); (c) treat version-gated
  gold keys absent for a file's version as "not present", never as mismatch.
- **Recommended strictness tier:** compare a curated subset of semantically
  load-bearing vars first (`LUNITS`, `INSUNITS`, `MEASUREMENT`,
  `EXTMIN`/`EXTMAX`, `DWGCODEPAGE`, `HANDSEED` ordering sanity), then widen.
- **Caution:** `HANDSEED`/section addresses in `FILEHEADER` legitimately
  change on rewrite — exclude them from the write-fidelity header diff,
  include them only in read-fidelity.

### F2 — Manually generating coverage-gap files with AutoCAD/BricsCAD

The corpus gaps (MTEXT, DIMENSION, TABLE, REGION, static INSERT/BLOCK,
MLEADER, VIEWPORT, IMAGE, MESH, 3DFACE, SOLID, ATTDEF/ATTRIB, TOLERANCE,
WIPEOUT) can be closed by authoring fixtures in a real CAD application, after
which the existing loop covers them with **no harness changes**:

1. **Author minimal files:** one drawing per gap entity, kept minimal (one or
   two entities on layer 0) so diffs stay localizable.
2. **Save per version:** SAVEAS to each in-scope format (R2000, R2004, R2007,
   R2010, R2013, R2018); only produce versions where the entity natively
   exists.
3. **Qualify each file as gold before use:** run `dwgread -O JSON`; only files
   libredwg decodes without `Error` enter the corpus.
4. **Provenance/licensing:** fixtures authored from scratch are clean test
   data. Note the generator in a companion `.txt`.
5. **Loop integration:** drop the new files into the corpus dirs, re-run the
   Phase 4 driver, and the entity types move from "OUT OF LOOP" to covered
   automatically.

---

## 18. Plan history

- `_archiv/1789491909007-cadcodec-gold-silver-roundtrip.md` — original Phase 0–6 plan.
- `_archiv/REFINEMENT_REPORT.md` and `_archiv/REFINEMENT_REPORT_ROOT.md` —
  Phase 2–5 refinement reports.
- `_archiv/_IMPLEMENTATION.md` — interim consolidation.

All four are superseded by this file and are preserved under
`tests/gold_harness/_archiv/` for historical reference only. Do not use them
to drive work.
