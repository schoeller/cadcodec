# Zero-context prompt — Phase B: the blob autopsy (Phase A is COMPLETE at 0/0)

> Campaign state 2026-09-23 ~21:30Z. **Phase A is COMPLETE: the corpus
> stands at 180 files, read 0, write 0** — the strict-load gold tree and
> the entire 56-fixture `sh_history/` tree (the seven Phase C families
> landed and qualified) are at zero (`f368fce` → `e1dff05`). Every
> fixture-backed SH class (HISTORY, SWEEP, EXTRUSION, LOFT, REVOLVE,
> SPHERE, BOX, BOOLEAN, plus the typed reads of WEDGE, CYLINDER, CONE,
> TORUS, PYRAMID, FILLET, CHAMFER) round-trips at zero with its
> record behavior verified; the wires/point 3DSOLID packets are
> closed. This
> brief opens **Phase B: the blob autopsy** — decoding the raw-retained
> node tails into semantic model fields. Read `tests/gold_harness/
> AGENTS.md` first, then §F2.1–F2.3 and §18.5 in `IMPLEMENTATION.md`
> (especially the Phase A completion record and the skeleton/wire
> knowledge base), then this file top to bottom.

## Task

**Phase B**: determine the internal structure of the four raw-retained
tails — the payloads captured verbatim on `SolidHistorySweep`
(`shsw_raw_tail`, serving both SWEEP and EXTRUSION), plus
`SolidHistoryLoft` and `SolidHistoryRevolve` (`raw_tail` each) —
and implement the typed fields behind them.
Phase B ends when the blob content round-trips across all 4 versions
per family with semantic field parity in the normalize projections.

### Why the tails exist (do not re-litigate)

The classes are `DEBUGGING_CLASS` in gold — there is NO oracle walk
for their tails; gold stops after `history_node.color.flag` and dumps
the rest as `unknown_bits`. The guessed field walks were disproven
(§18.5: the sweep blob-size model, the REVOLVE 192-bit budget proof).
Phase A retained the bytes verbatim; Phase B now DECODES them, using
two non-oracle instruments:
1. **Cross-specimen comparison**: 56 fixtures, 4 DWG versions; the
   same operation's records are bit-identical across versions except
   handle tails (verified in Phase A) — so the payload structure is
   version-portable and derivable from the specimens alone.
2. **The R2010 live-oracle fragment**: on R2010 (AC1024) files, gold's
   3DSOLID wireframe walk reads the ds-era modeler data cleanly (see
   the Revolve_2010 trace in the step-6 record); where a retained
   tail's bits OVERLAP data gold parses elsewhere (the 3DSOLID
   wireframe block reads from the SAME modeler backing!), the
   gold-parsed values name the semantics.

### Phase B method (one family at a time; SWEEP first)

1. **Assemble the specimen set**: for each family regenerate the
   captured tails (`dwg2json` on the fixture; the model carries
   `shsw_raw_tail`/`raw_tail` as byte arrays plus `bit_len`). Start
   with the 4 Polysolid records + the 4 Extrude records.
2. **Map the anchor structure**: the tails are captured from just
   after `op.minor`, so byte 0 is the direction 3BD (Polysolid:
   `'10'×3` = three zero pairs; Extrude: `'10','10','00'+raw64` —
   raw little-endian) followed by option BD runs, `BD('01')` scale,
   and raw BD entries (the sweep autopsy). Use the bitcode tables
   in the knowledge base; compose field walks that land exactly at
   each record's `bit_len - text_flag` boundary; cross-check across
   versions.
3. **Hypothesize semantics from the operation**: the Polysolid's
   sweep = rectangle profile swept along a segment: expect a
   profile transform (4×4), sweep options (draft/twist/align flags),
   and the align/miter bits; the Extrude = circle extrusion: the
   direction vector already parsed verbatim.
4. **Extend the model per family**: promote the decoded fields onto
   `SolidHistorySweep/Loft/Revolve` (named typed fields) while
   KEEPING the raw tail as the write authority (write the raw tail
   verbatim unless a decoded field changed — Phase B's write rule:
   re-encode ONLY when the model was programmatically modified, else
   verbatim).
5. **Gates per family**: hermetic tests; the family's four smokes
   (must stay 0/0); the corpus must stay 180 files 0/0; any writer
   re-encode path additionally needs the layer-4 byte-walk.

### Phase C fixture state (2026-09-23 review, complete)

Seven families authored and qualified (all 0/0, `.txt` companions
landed): `Wedge_`, `Cylinder_`, `Cone_`, `Torus_`, `Pyramid_`,
`Fillet_`, `Chamfer_` (the latter two with their parent
`ACSH_BOX_CLASS` chains — good edge-chain specimens). The review
also fixed the last retype gap: `ACSH_PYRAMID_CLASS` joined
`_DYNBLOCK_RETYPE` with its height/sides/radius/topradius
projection. **BREP is DEFERRED** per the maintainer's decision:
seven authored attempts never produced an `ACSH_BREP_CLASS` record
(SLICE mints empty fresh roots; paste-grafts stay fully
parametric; SOLIDEDIT face edits strip the history outright) —
the class has no user-facing production path in current AutoCAD;
the row re-opens if an authentic specimen surfaces. Each landed
class's un-elide is the step-5 recipe (trace-calibrate with
gold `-v9`, un-elide via the shared list, four gates).

## The wire knowledge base (condensed; §18.5 has the full records)

- SH skeleton: parentid `BLd(-1)` = `'00'+LE32(0xFFFFFFFF)`, eval
  33/427, value_code BSd −9999, nodeid, hist 33/427, 16 BD transform,
  CMC (44 bits: index 0, rgb c0000000, ByLayer), step_id BL, material
  → handle stream, op major/minor 33/427. Class tails after that are
  the Phase B subject.
- Class fields oracle-verified: sphere = BD radius; box =
  length/width/height BDs; boolean = RC operation + BL operand1/2;
  history = 2 BLs + handle + BL + 2 Bs. Wireframe block (R2010 clean):
  [wireframe_data_present B][point_present B][point 3BD][isoline BL]
  [isoline_present B][num_wires BL][per wire: RC type + BLd marker + BL
  color + BLd acis_index + BL point count + 3BD points + B transform].
- Frames: R2018 = 40 bits, R2010 = 39, R2007 = [MS][BOT]. Data ends
  `Size×8 − frame − Hdlsize − 1` (the −1 = text-present flag). Record
  tail capture = [post-op.minor .. min(main_end_bits, record_end)].
- Wire primitives: raw short/long/double LITTLE-endian; BD
  `00`/`01`/`10` = raw64 / 1.0 / 0.0 (`11` reserved→0.0); BL
  `00`/`01`/`10`/`11` = LE32 / RC / 0 / 256. Silver reader positions
  ≡ window bits (frame-inclusive); `unknown_bits_by_handle` ≡ gold's
  `unknown_bits` bit-for-bit.
- The owner-handle form delta (silver `(4,2,abs)` vs authored
  `(6,0,+1)`) is pre-existing, corpus-wide, identity-equal.
- Phase A facts: the R2013+/R2018 ds-backed 3DSOLID wireframe walk in
  gold derails on a phantom bit (records gold-emit no wires/
  silhouettes/point there; the drop branch in normalize_silver handles
  it); the 3DSOLID wireframe anchor is verbatim (never swap for the
  geometry centre).

## Environment (complete)

The repo lives in WSL. From Windows:
`\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`.
Shell commands run via
`wsl.exe -d Ubuntu-24.04 -- bash <script>` — write scripts with the
write tool and run by absolute path (PowerShell quoting caveats:
inline `&&`, `$var`, pipes, and multi-word grep alternations are all
broken; ONE COMMAND PER LINE; `sleep` is capped at 120 s — use the
tracked background process for the corpus).

```bash
# Environment (source this):
export PATH="$HOME/.cargo/bin:$PATH"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

## Verification gate (unchanged; the zero-keeping rule now applies to 0/0)

```bash
# 1. Build gates
cargo test --features serde

# 2. Family smokes (must stay 0/0)
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (must stay 180 files 0/0)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 byte-walk for any writer re-encode path
target/debug/dump_section_bytes <file> <A> <N>
```

## Commit inventory (this halt)

```
e1dff05  docs(harness): Phase C fixture review closure — seven families landed, BREP deferred
9cf8e0f  test(harness): Phase C fixture families — seven new genus families, qualified
7757724  fix(harness): land the pyramid retype and projection — the last retype gap
bc230a3  docs(harness): Phase B handover — NEXT_SESSION replaced (the blob autopsy)
14bca7e  docs(harness): Phase A COMPLETE — corpus 152 files at 0/0; Phase C authoring list
f368fce  fix(harness): the last two 3DSOLID packets — Phase A step 6, fixtures 0/0
bf5f299  docs(harness): step-5 review pass — R2010 sphere L4 closes the version matrix
19308ee  fix(harness): land the sphere projection and un-elide Box/Boolean/Sphere — Phase A step 5
14f9a4a  docs(harness): Phase A step-5 closure — primitives record + 3DSOLID packet queue
df551cb  fix(docs): drop a leftover placeholder line from the step-6 inventory
78f5838  docs(harness): step-6 handover — NEXT_SESSION replaced (the last two 3DSOLID packets)
91c6cd3  docs(harness): review corrections — step-4 autopsy phrasing and position-bookkeeping note
36af6fb  docs(harness): Phase A step-4 closure — LOFT/REVOLVE record + primitives queue
20d472b  fix(dwg): un-elide ACSH_LOFT/REVOLVE_CLASS — Phase A step 4, shared raw-tail helpers
2ed92ae  refactor(dwg): share the SH elide exception list between guard and nuller
48ca14a  docs(harness): Phase A step-3 closure — §18.5 record + step-4 queue
8c41aa6  fix(dwg): un-elide ACSH_EXTRUSION_CLASS — Phase A step 3
c96355f  fix(dwg): clamp sweep raw-tail capture and emit bounds (review)
```

The branch head is this handover-refresh commit (this file); the
Phase B content above it is the brief itself. `1f06d9d` was the last
push to `origin/gold-vs-silver` (push only when asked).
