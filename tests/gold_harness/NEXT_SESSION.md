# Zero-context prompt — ACS/SH solid-history Phase A (in progress)

> Campaign state 2026-09-23 ~14:00Z. The strict-load campaign is closed
> at zero (2026-09-21, user-verified round seven; see IMPLEMENTATION.md
> §18.4). The F2 fixture tree landed (2026-09-23: 28 .dwg + 28 .txt in
> `tests/gold_harness/tests/sh_history/`, all qualified, committed as
> `fc9f235`). This brief covers the **ACS/AcDbSh solid-history Phase A**
> — implementing the SH wire layouts so the elided-at-save node classes
> round-trip. Read `tests/gold_harness/AGENTS.md` first (durable rules),
> then the §F2.1–F2.3 spec in `IMPLEMENTATION.md` (the fixture tree,
> its gates, and its provenance convention), then this file top to
> bottom. Read only these three files cold — everything routes from
> here.

## Task

**Phase A goal**: implement the ACSH_SWEEP_CLASS and ACSH_EXTRUSION_CLASS
wire layouts (the two classes with the opaque `shsw_text`/`shsw_text2`
blobs), un-elide them per calibration, and drive the sh_history fixture
diffs from 26/8 toward 0/0 while holding the gold baseline at 0/0.

### Current state

- **Step 1 DONE** (commit `b926053`): ACSH_HISTORY_CLASS un-elided.
  Its layout was already correct on both sides (6 fields: 2 BLs +
  handle + BL + 2 Bs); the elide guard and the
  `solid_history_handle_value` nuller now allow HISTORY records
  through while all node classes (EXTRUSION, SWEEP, the primitives,
  BREP) stay elided. Verified: the Polysolid_2018 fixture round-trips
  the HISTORY root at handle 0x2ED; the SWEEP record (261 bytes)
  stays elided; corpus 152 files, gold 0/0, fixtures 26/8.
- **Step 2 NEXT** (probe analysis 2026-09-23, resumed here):
  ACSH_SWEEP_CLASS. The READER is **proved correct** — the probe
  confirmed `read_embedded_entity` consumes exactly the right bytes
  and produces `EmbeddedEntity::Unknown { type_code, bit_count, bytes }`
  which preserves the blob bytes. The **WRITE path loses bytes**: the
  temporary un-elide probe on `Polysolid_2018.dwg` produced a record
  that gold decodes at 148 bytes vs the original's 261 bytes (−113).
  Layer-4 frame comparison:
  - original: Object 137, Size 261, Hdlsize 0x1D, Type 520, Address 33088
  - rewrite:  Object 137, Size 148, Hdlsize 0x29, Type 520, Address 33017
  **The fix**: the writer arm in `write_solid_history_sweep` calls
  `encode_embedded_entity` on `value.sweep_entity` and writes
  `type_code(BL) + bytes.len()(BL) + bytes`. The else-arm writes
  `write_bit_long(0); write_bit_long(0);` with NO bytes — dropping the
  blob content when the model carries `None`. The `safe_count` clamp
  and the `type_code == 0` early-exit in `decode_embedded_entity` can
  both produce `None` even though the reader consumed the bytes. The
  model must retain the consumed bytes: extend `SolidHistorySweep`
  with `shsw_method: i32`, `shsw_text: Vec<u8>`, `shsw_bl93: i32`,
  `shsw_text2: Vec<u8>` and have the reader/writer read/write them
  directly (not via the `EmbeddedEntity` wrapper). Then un-elide SWEEP
  (two one-liner elide-guard edits: add
  `&& d.dxf_name != "ACSH_SWEEP_CLASS"` to both
  `objects.rs::write_object` and
  `entities.rs::solid_history_handle_value`).
- **Step 3**: ACSH_EXTRUSION_CLASS — the SWEEP layout plus the
  Extrusion subclass marker. Calibrate against
  `sh_history/Extrude_2018.dwg`.

### Write-path byte-loss diagnosis (ready for the next session)

The probe confirmed the reader and writer consume the same blob bytes
through `EmbeddedEntity::Unknown` (which preserves them byte-for-byte).
The 113-byte loss comes from the write arms:

```rust
// src/io/dwg/dwg_stream_writers/object_writer/dynamic_block.rs,
// fn write_solid_history_sweep, ~line 177:
if let Some(entity) = &value.sweep_entity {
    let encoded = encode_embedded_entity(entity, self.version, self.dxf_version);
    self.writer.write_bit_long(encoded.type_code);
    self.writer.write_bit_long(encoded.bytes.len() as i32);
    write_embedded_bytes(&mut self.writer, &encoded);
} else {
    self.writer.write_bit_long(0);   // ← type_code=0
    self.writer.write_bit_long(0);   // ← size=0 (NO BYTES!)
}
```

If `sweep_entity` / `path_entity` are `None` (from `safe_count`
clamping the size to 0, or `decode_embedded_entity` returning `None`
on `type_code == 0 || bit_length == 0`), the writer produces
`BL(0) + BL(0)` and no bytes — a **113-byte hole** in the record.

**The byte-walk addresses for the next session**:

```bash
# dump the SWEEP record from both sides (Address−9 for margin):
target/debug/dump_section_bytes \
    tests/gold_harness/tests/sh_history/Polysolid_2018.dwg 33079 270
target/debug/dump_section_bytes \
    /tmp/f2_smoke/Polysolid_2018_rt.dwg 33008 157
# bitwalk from the first divergence: the original's record starts at
# Address 33088, the rewrite at 33017 — find where the 113 bytes vanish
```

## The 26/8 fixture diffs decompose into three packets

From the 2026-09-23 corpus run (152 files, gold tree 124 at 0/0,
fixture tree 28 at 26 read / 8 write):

| packet | rows | files | route |
|---|---|---|---|
| `3DSOLID.wires` stub | 16 | Extrude/Loft/Revolve/Sphere (R2013+R2018) | the constructed-genus zero-index wire cache — `33ce739` addressed other shape inputs; these may need the node-class blob bytes to produce real wires |
| `ACSH_SPHERE_CLASS` count + `UNKNOWN_OBJ` count | 8 | all 4 Sphere files | the sphere node-class ordinal alignment: silver produces a different record count than gold on the same drawing |
| `3DSOLID.point` wrong-value | 2 | Revolve_2007/2010 only | silver reads the modeler point at (0.6, 0, 0.6) where gold reads (0, 0, 0) — a constructed-genus default |

Step 2 (SWEEP) directly affects the Polysolid family (whose diffs are
currently zero through the elide). The subsequent un-elides (Sphere,
Extrusion, Loft, Revolve) follow once the SWEEP write-path fix is
proven.

## The gold spec (wire layout source — verbatim)

File: `~/work/libredwg/src/dwg2.spec` (read-only oracle; NEVER edit):

```
DWG_OBJECT (ACSH_SWEEP_CLASS)   // line ~4175 in dwg2.spec
  HANDLE_UNKNOWN_BITS;
  AcDbEvalExpr_fields;           // nodeid BC, parentid BLd, value_code BSd
                                  // + union, nodeid BL
  AcDbShHistoryNode_fields;      // major BL, minor BL, 16 BD transform,
                                  // CMC color, step_id BL, material handle
  SUBCLASS (AcDbShPrimitive)
  SUBCLASS (AcDbShSweepBase)
  major BL                        // instance value 33
  minor BL                        // instance value 29
  direction 3BD                   // 0, 0, 0
  method BL                       // 77
  shsw_text_size BL               // 744 <-- opaque blob, NOT in DXF
  shsw_text BINARY                // blob bytes, size = shsw_text_size
  shsw_bl93 BL                    // 77
  shsw_text2_size BL              // 480 <-- opaque blob, NOT in DXF
  shsw_text2 BINARY               // blob bytes, size = shsw_text2_size
  draft_angle BD                  // 0.0
  start_draft_dist BD             // 0.0
  end_draft_dist BD               // 0.0
  scale_factor BD                 // 1.0
  twist_angle BD                  // 0.0
  align_angle BD                  // 0.0
  sweepentity_transform 16 BD
  pathentity_transform 16 BD
  align_option RC                 // 2
  miter_option RC                 // 2
  has_align_start B               // 1
  bank B                          // 1
  check_intersections B           // 0
  shsw_b294 B                     // 1
  shsw_b295 B                     // 1
  shsw_b296 B                     // 1
  pt2 3BD                         // 0, 0, 0
  SUBCLASS (AcDbShSweep)
  START_OBJECT_HANDLE_STREAM;
DWG_OBJECT_END
```

(`ACSH_EXTRUSION_CLASS` at ~4222 is identical plus the Extrusion subclass
marker before the handle stream; `AcDbEvalExpr_fields` and
`AcDbShHistoryNode_fields` macros at ~1800 and ~1855. Gold's
classes.c registry: ACSH_HISTORY = 513, ACSH_SWEEP = 518, type 520 on
the wire = the fixture's dynamic mapping for SWEEP.)

**Blob interpretation note**: the two blob fields carry serialized sweep
options and sweep/path profiles. They MAY contain an embedded entity
stream internally, but Phase A **retains them raw** — do NOT attempt
to parse or interpret the blob content until the raw round-trip is
byte-faithful (Phase B autopsy determines internal structure).

## Code state (at HEAD)

| location | current state |
|---|---|
| model: `src/objects/dynamic_block.rs` line ~970 | `SolidHistorySweep` has the current-guess fields (`sweep_entity: Option<EmbeddedEntity>`, `path_entity: Option<EmbeddedEntity>`, etc.) — **lacks** dedicated blob fields; for the fix: add `shsw_method: i32`, `shsw_text: Vec<u8>`, `shsw_bl93: i32`, `shsw_text2: Vec<u8>` fields |
| reader: `src/io/dwg/dwg_stream_readers/object_reader/dynamic_block.rs` line ~240 | `read_history_sweep()` reads the current guess — `sweep_entity_type` BL, `sweep_size` BL, `sweep_entity` via `read_embedded_entity()`; **the blob bytes are consumed correctly** (aligned) but stored inside the `EmbeddedEntity::Unknown` wrapper; for the fix: replace the embedded-entity reads with direct `read_bit_long + read_bytes` for the 4-blob field set |
| writer: `src/io/dwg/dwg_stream_writers/object_writer/dynamic_block.rs` line ~172 | `write_solid_history_sweep()` calls `encode_embedded_entity` and writes `type_code(BL) + bytes.len()(BL) + bytes` — when sweep_entity is None the blob bytes are LOST (the −113); for the fix: write the 4-blob field set directly from the new model fields |
| elide: `src/io/dwg/dwg_stream_writers/object_writer/objects.rs` line ~310 | the write guard elides all `ACSH_*` except `ACSH_HISTORY_CLASS`; for step 2: add `&& d.dxf_name != "ACSH_SWEEP_CLASS"` to the guard |
| pointer nuller: `src/io/dwg/dwg_stream_writers/object_writer/entities.rs` line ~5175 | `solid_history_handle_value()` nulls pointers to elided SH records; for step 2: same one-liner — allow `ACSH_SWEEP_CLASS` through |
| embedded reader/writer: `src/io/dwg/embedded_entity.rs` | the `EmbeddedEntity::Unknown` encode/decode (lines ~99, ~246, ~331) preserves raw bytes; NOT modified — used by other entities too |

## Calibration specimens (all qualified and landed)

All 28 fixtures in `tests/gold_harness/tests/sh_history/` —
one operation per file, 4 versions (2007/2010/2013/2018) per operation,
142–207 objects per file, zero gold Error lines, zero AECC/AEC
template junk, each carrying a `.txt` provenance companion with
the gold-decode qualification receipts.

| calibration target | fixture file | wire object |
|---|---|---|
| ACSH_SWEEP_CLASS | `Polysolid_2018.dwg` | handle 0x2EB, 261 bytes, gold's UNKNOWN_OBJ fallback, Type 520 on the wire |
| ACSH_EXTRUSION_CLASS | `Extrude_2018.dwg` | (probe not yet done) |
| Wire-frame facts | README "Oracles" | record window [Address..Address+Size); bitsize = Size×8−Hds |

## Environment (complete)

The repo lives in WSL. From Windows:
`\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`.
Shell commands run via:
`wsl.exe -d Ubuntu-24.04 -- bash <script>` — write scripts with
the write tool and run by absolute path (PowerShell quoting caveats:
inline `&&`, heredocs via `wsl.exe -c`, `&&`, `$var`, pipes, and
multi-word grep alternations are all broken; ONE COMMAND PER LINE).

```bash
# Environment (source this):
export PATH="$HOME/.cargo/bin:$PATH"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

## Verification gate for every Phase A step

```bash
# 1. Build gates (all segments green)
cargo test --features serde

# 2. Single-fixture smoke (0/0 expected with record present)
GOLD_DWGREAD=... GOLD_TESTDATA=... \
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/Polysolid_2018.dwg /tmp/smoke

# 3. Full corpus (gold tree 0/0 must stay; fixture diffs may improve)
#    Detached launch (10+ min, use nohup):
nohup python3 tests/gold_harness/run_corpus.py > /tmp/corpus.log 2>&1 &

# 4. Layer-4 bytewise check (writer form changes only):
target/debug/dump_section_bytes <origin.dwg> <A> <N>
# Verify the rewrite's SWEEP record bit-walk matches the original's —
# this is the only instrument that catches "legal but different" forms.
```

## Commit inventory (this halt)

```
1f06d9d  chore: retire first-session scratch — the ocs.lock rules and the cylinder example
e686903  docs(harness): Phase A step-2 probe findings — the SWEEP write path loses 113 bytes
989860d  fix(docs): NEXT_SESSION encoding cleanup
086b1f1  docs(harness): ACS/SH Phase A handover — NEXT_SESSION replaced, §18.5 opens
b926053  fix(dwg): un-elide ACSH_HISTORY_CLASS — Phase A step 1
fc9f235  test(harness): F2 in-repo fixture tree — sh_history campaign
459bc74  fix(dwg): elide SH modeler-history class records at save
33ce739  fix(dwg): constructed wireframe guard
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

The branch is pushed to `origin/gold-vs-silver` at `1f06d9d`.
