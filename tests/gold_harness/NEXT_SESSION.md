# Zero-context prompt — ACS/SH solid-history Phase A (in progress)

> Campaign state 2026-09-23 ~13:00Z. The strict-load campaign is closed
> at zero (2026-09-21, user-verified round seven; see IMPLEMENTATION.md
> §18.4). The F2 fixture tree landed (2026-09-23: 28 .dwg + 28 .txt in
> `tests/gold_harness/tests/sh_history/`, all qualified, committed as
> `fc9f235`). This brief covers the **ACS/AcDbSh solid-history Phase A**
> — implementing the SH wire layouts so the elided-at-save node classes
> round-trip. Read `tests/gold_harness/AGENTS.md` first (durable rules),
> then the §F2.1–F2.3 spec in `IMPLEMENTATION.md` (the fixture tree,
> its gates, and its provenance convention), then this file top to bottom.

## Task

**Phase A goal**: implement the ACSH_SWEEP_CLASS and ACSH_EXTRUSION_CLASS
wire layouts (the two classes with the opaque `shsw_text`/`shsw_text2`
blobs), un-elide them per calibre, and drive the sh_history fixture
diffs from 26/8 toward 0/0 while holding the gold baseline at 0/0.

Current state:
- **Step 1 DONE** (commit `b926053`): ACSH_HISTORY_CLASS un-elided. Its
  layout was already correct on both sides (6 fields: 2 BLs + handle +
  BL + 2 Bs); the elide guard and the `solid_history_handle_value`
  pointer-nuler now allow HISTORY records through while all node
  classes (EXTRUSION, SWEEP, primitives, BREP) stay elided. Verified:
  the Polysolid_2018 fixture round-trips the HISTORY root at handle
  0x2ED; the SWEEP record (261 bytes) stays elided; corpus 152 files,
  gold 0/0, fixtures 26/8 (unchanged — the HISTORY step adds nothing,
  the remaining diffs are all node-class).
- **Step 2 NEXT**: ACSH_SWEEP_CLASS — the reader currently guesses the
  field sequence but misses the two length-prefixed opaque binary
  blobs (`shsw_text_size` BL + `shsw_text` bytes + `shsw_bl93` BL +
  `shsw_text2_size` BL + `shsw_text2` bytes). The guess causes mid-record
  desync on native files (Polysolid_2018.dwg object 0x2EB = 261 bytes
  of UNKNOWN_OBJ — gold's own SWEEP decode falls back for this record).
- **Step 3**: ACSH_EXTRUSION_CLASS — the SWEEP layout plus the
  `SUBCLASS (AcDbShExtrusion)` prefix (`ACSH_SWEEP_CLASS is identical,
  plus SUBCLASS (AcDbShSweep) before the handle stream` per dwg2.spec
  ~4200). Calibrate against `sh_history/Extrude_2018.dwg`.

## The 26/8 fixture diffs decompose into three packets

From the 2026-09-23 corpus run (152 files, gold tree 124 at 0/0,
fixture tree 28 at 26 read / 8 write):

| packet | rows | files | route |
|---|---|---|---|
| `3DSOLID.wires` stub | 16 | Extrude/Loft/Revolve/Sphere (R2013+R2018) | the constructed-genus zero-index wire cache — `33ce739` addressed other shape inputs; these may share the same path or need the node-class blob bytes to produce real wires |
| `ACSH_SPHERE_CLASS` count + `UNKNOWN_OBJ` count | 8 | all 4 Sphere files | the sphere node-class ordinal alignment: silver produces a different record count than gold on the same drawing |
| `3DSOLID.point` wrong-value | 2 | Revolve_2007/2010 only | a genuine field divergence: silver reads the modeler point at (0.6, 0, 0.6) where gold reads (0, 0, 0) |

Step 2 (SWEEP) only directly affects the Polysolid family (whose
diffs are currently zero through the elide). The Sphere count and the
Extrude/Loft/Revolve wire stubs need the corresponding node classes
(Sphere primitive, Extrusion, Loft) in addition to the SWEEP blob
work — but the subsequent un-elides will follow the same per-class
pattern once the blob-byte model is proven on SWEEP first.

## The gold spec (wire layout source)

`~/work/libredwg/src/dwg2.spec` (read-only oracle):

```
DWG_OBJECT (ACSH_SWEEP_CLASS)   // line ~4175
  HANDLE_UNKNOWN_BITS;
  AcDbEvalExpr_fields;           // nodeid (BL) [DXF-only], parentid BLd,
                                 // major/minor BL, value_code BSd + union,
                                 // nodeid BL
  AcDbShHistoryNode_fields;      // major BL, minor BL, 16×BD transform, CMC,
                                 // step_id BL, material handle
  SUBCLASS (AcDbShPrimitive)
  SUBCLASS (AcDbShSweepBase)
  major BL                       // instance value 33
  minor BL                       // instance value 29
  direction 3BD                  // 0,0,0
  method BL                     // 77
  shsw_text_size BL             // 744  <-- opaque blob, NOT in DXF
  shsw_text BINARY              // blob bytes, size = shsw_text_size
  shsw_bl93 BL                  // 77
  shsw_text2_size BL            // 480  <-- opaque blob, NOT in DXF
  shsw_text2 BINARY            // blob bytes, size = shsw_text2_size
  draft_angle BD                // 0.0
  start_draft_dist BD          // 0.0
  end_draft_dist BD           // 0.0
  scale_factor BD             // 1.0
  twist_angle BD              // 0.0
  align_angle BD              // 0.0
  sweepentity_transform 16×BD
  pathentity_transform 16×BD
  align_option RC              // 2
  miter_option RC             // 2
  has_align_start B           // 1
  bank B                     // 1
  check_intersections B      // 0
  shsw_b294 B               // 1
  shsw_b295 B              // 1
  shsw_b296 B              // 1
  pt2 3BD                  // 0,0,0
  SUBCLASS (AcDbShSweep)
  START_OBJECT_HANDLE_STREAM;
DWG_OBJECT_END
```

(`ACSH_EXTRUSION_CLASS` ~4222 is identical plus the Extrusion subclass
marker before the handle stream. `AcDbEvalExpr_fields` and
`AcDbShHistoryNode_fields` macros — see spec ~1800 and ~1855.)

**Key deviation from the current guess**: the existing
`read_history_sweep` (in `src/io/dwg/dwg_stream_readers/object_reader/
dynamic_block.rs` line 240) reads `sweep_entity` / `path_entity` as
embedded enti�ties (with `sweep_entity_type` BL + `sweep_size` BL +
the `read_embedded_entity` call). **This is WRONG per the authored
wire** — the spec shows two opaque BLOB fields (`shsw_text` /
`shsw_text2`), not embedded entities. The blobs carry the serialized
sweep options and sweep/path profiles (they may contain an embedded
entity stream — Phase B autopsy determines that). For Phase A: retain
the blobs raw (`Vec<u8>` on the model), do NOT attempt to parse them.

## Code state (commit `b926053`)

- Model (`src/objects/dynamic_block.rs`): `SolidHistorySweep` has the
  current guess fields (sweep_entity, path_entity as
  `Option<EmbeddedEntity>`, etc.) — **lacks** the blob retention fields
  (`shsw_text: Vec<u8>`, `shsw_text2: Vec<u8>`, `shsw_bl93: i32`).
  Extend, do not replace.
- Reader (`dynamic_block.rs` line ~288): `read_solid_history_data()`
  dispatches by dxf_name; `read_history_sweep()` (line ~240) reads the
  current guess. **The SWEEP path needs a rewrite per the spec block
  above**.
- Writer (`object_writer/dynamic_block.rs` line ~172):
  `write_solid_history_sweep()` mirrors the current guess. **Same
  rewrite needed**.
- Elide: `objects.rs::write_object` (line ~310) — the guard now allows
  `ACSH_HISTORY_CLASS` through; all other `ACSH_*` stay elided. For
  step 2: add `ACSH_SWEEP_CLASS` to the allowed set once the layout is
  calibrated.
- Pointer-nuler: `entities.rs::solid_history_handle_value` (~line 5175)
  — same: allow HISTORY, null the rest.

## Calibration specimens (all qualified + landed)

All 28 fixtures in `tests/gold_harness/tests/sh_history/` —
one operation per file, 4 versions (2007/2010/2013/2018) per operation,
142–207 objects per file, zero gold Error lines, zero AECC/AEC
template junk. SWEEP target: `Polysolid_2018.dwg` object 0x2EB (261
bytes, gold's UNKNOWN_OBJ fallback). EXTRUSION target:
`Extrude_2018.dwg`. Wire-frame facts (envelope, MS/UMC/BOT, bitsize =
Size×8−Hds) in README "Oracles" + IMPLEMENTATION.md §18.4.

## Environment

Same as always: repo at `~/work/cadcodec` (WSL Ubuntu-24.04; from
Windows: `\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`),
gold tree at `~/work/libredwg` (read-only), oracles via env vars.

## Verification gate for every Phase A step

- `cargo test --features serde` (all segments green)
- One-fixture smoke: `run_roundtrip.py` on the calibration specimen
  (expect 0/0 with the record present in the rewrite)
- Full corpus: gold 0/0, fixture_count may improve (the SWEEP un-elide
  will change the Polysolid count but not yet the other families)
- `dump_section_bytes` on the calibration object for byte-walks
- `dump_proxy_graphics` unaffected (different common entity family)

## Commit inventory (this halt)

```
b926053  fix(dwg): un-elide ACSH_HISTORY_CLASS — Phase A step 1
fc9f235  test(harness): F2 in-repo fixture tree — sh_history campaign
459bc74  fix(dwg): elide SH modeler-history class records at save
33ce739  fix(dwg): constructed wireframe guard — drop stub zero-index wire caches
2c92b70  fix(acis): SAB restore-file record order
06756bf  fix(acis): SAB class-width completion
96d6707  fix(acis): SAB restore-file body declaration
b9211d0  fix(entities): constructed-genus constructor defaults
94533a3  fix(mleader): constructed-native stance in MultiLeader::new
21889f1  fix(build): plain cargo test clean (feature gates)
34bc702  docs(harness): zero-keeping regression gate
34a0ed9  docs(harness): specimen origin census
9dd2cd5  docs(harness): file-inventory completeness
5891cc1  chore(harness): retire stale scripts and pycache
```
