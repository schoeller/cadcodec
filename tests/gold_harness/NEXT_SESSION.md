# Zero-context prompt — ACS/SH solid-history Phase A (step 5: the primitives)

> Campaign state 2026-09-23 ~19:10Z. The strict-load campaign is closed
> at zero (2026-09-21, user-verified round seven; see IMPLEMENTATION.md
> §18.4). The F2 fixture tree landed (2026-09-23: 28 .dwg + 28 .txt in
> `tests/gold_harness/tests/sh_history/`, `fc9f235`). Phase A steps
> 1–4 are DONE: HISTORY, SWEEP, EXTRUSION, LOFT, and REVOLVE are
> un-elided — the four node classes with undocumented tails carry
> raw-tail retention. This brief covers step 5: the primitives
> (Box, Wedge, Cylinder, Cone, Torus, Pyramid, Sphere). Read
> `tests/gold_harness/AGENTS.md` first (durable rules), then §F2.1–F2.3
> and §18.5 in `IMPLEMENTATION.md`, then this file top to bottom.

## Task

**Phase A step 5**: un-elide the primitive node classes. Unlike the
sweep family, these are gold-LIVE classes — gold parses them with
typed fields, so silver's typed arms are CALIBRATABLE against
per-field `-v9` traces (the instrument that pinned the SH skeleton in
§18.5). The lead mystery is the Sphere step: the
`ACSH_SPHERE_CLASS` + `UNKNOWN_OBJ` count/missing packet (8 corpus
rows, all 4 Sphere files) says silver projects a different sphere
record COUNT than gold from the same drawing — a reader-side
duplication/dedup difference, not just a layout issue.

### What already landed (do not redo)

- `b926053` (step 1): ACSH_HISTORY_CLASS un-elided.
- `ba7d112`+`c96355f` (step 2 + review clamps), `8c41aa6` (step 3),
  `20d472b` (step 4): SWEEP, EXTRUSION, LOFT, REVOLVE un-elided
  under raw-tail retention. Shared helpers:
  `capture_undocumented_tail` (reader — clamps the declared split to
  the physical record window) and `write_undocumented_tail` (writer —
  byte-vector-authoritative, falls back to the modeled arm). The
  single elide authority is
  `elided_solid_history_class` in
  `object_writer/objects.rs`, consumed by both the write guard and
  the pointer nuller. All four retained-tail records round-trip
  bit-identically (L4-verified); corpus gold 0/0 held throughout.
- `2ed92ae`: the shared-list refactor (no second exception list
  exists — edit the one helper and its Phase A doc comment).

### Step 5 method (per primitive, Sphere first)

1. **Re-tune a fixture census first** (Sphere_2018): compare
   `gold_orig.json` vs `silver_orig.json` object counts for
   `ACSH_SPHERE_CLASS` (and the paired `UNKNOWN_OBJ`) — establish
   what the count/missing packet actually is before touching
   layouts: is silver duplicating a sphere record, missing one, or
   mis-labeling a sibling (e.g. a `Type 505` boilerplate triple
   object counted as a sphere)? The diff rows name the type and the
   side (count vs missing).
2. **Calibrate the typed arm** against gold's live trace:
   `$GOLD_DWGREAD -v9 <fixture>` prints the class walk field by
   field with bit positions (see the §18.5 skeleton trace for the
   sphere: eval+base+33/427+radius BD 1.0). Walk the record both
   ways (gold's fields vs bits in `unknown_bits_by_handle` —
   silver's side channel is bit-identical to gold's own dump) and
   fix any drifted field in silver's typed reader/writer arms
   (`read_solid_history_data` / the writer's
   `write_solid_history_operation` primitives arms). The primitives
   have NO undocumented tail to retain raw — their tails are typed
   and oracle-verifiable (radius, height, x/y/top radii, sides...).
3. **Un-elide via the shared list** (one class at a time; Box and
   Wedge share an arm/model — do them as one step), then the gates:
   per class — hermetic tests, the fixture smoke (no new rows
   expected except the Sphere count packet, whatever it turns out
   to be), layer-4 compare on the record (typed fields must
   reproduce the wire bits exactly — shortform/raw forms included:
   `write_bit_double` of 0.0/1.0/raw values is form-preserving),
   then the full corpus after each class or a small batch.
4. **Fixtures**: `Box_*`, `Polysolid_*` (Polysolid's SH node may be
   a Box/Wedge/Fillet genus — check its class table;
   `Boolean`/`Union_*` files carry ACSH_BOOLEAN_CLASS), `Sphere_*`,
   `Extrude_*` (Cylinder?), plus the corpus gold tree for
   regressions.

## The wire knowledge base (condensed; §18.5 has the full records)

- SH skeleton, verified via gold's live sphere `-v9` trace: parentid
  `BLd(-1)` = `'00'+LE32(0xFFFFFFFF)`, eval major `BL('01'+RC)` 33 /
  minor `BL('00'+LE32)` 427, `value_code BSd` −9999 (`LE16 0xD8F1`),
  nodeid 1, hist 33/427, 16 BD transform, CMC (44 bits: index 0, rgb
  c0000000, ByLayer), step_id `BL('01'+RC)` 1, material → handle
  stream, then `op.major/minor` 33/427; class fields after that
  (sphere: BD radius 1.0, then the 1-bit text-flag pad). The sphere
  record: Size 44, Hds 0x1D, data end = 44×8−40−29−1 = 282 bits.
- Frames: R2018 = 40 bits, R2010 = 39. Data ends at
  `Size×8 − frame − Hdlsize − 1` (the −1 = the text-present flag).
  Anchor comparisons on the parentid pattern, never on offsets.
- Wire primitives: raw-short/long/double are LITTLE-endian; BD
  prefixes `00`/`01`/`10` = raw64 / 1.0 / 0.0; BL `00`/`01`/`10`/`11`
  = LE32 / RC / 0 / 256. Position bookkeeping: silver reader
  positions are window bits (frame-inclusive, ≡ gold's `-v9`
  positions); `unknown_bits_by_handle` ≡ gold's `unknown_bits`
  bit-for-bit.
- Sweep-family tails are retained raw (`raw_tail`/`shsw_raw_tail`);
  the primitives will NOT need that — their fields are oracle-live.
- The remaining packets after step 4: `3DSOLID.wires` stub (16,
  R2013+R2018 — constructed-genus zero-index wire cache, likely
  Phase B with the retained tails in hand), `3DSOLID.point` (2,
  read-side only: silver's constructed-genus read default
  (0.6, 0, 0.6) vs gold (0, 0, 0); the rewrite matches gold —
  Phase B), `ACSH_SPHERE_CLASS`/`UNKNOWN_OBJ` counts (8 — step 5's
  first investigation).

## Environment (complete)

The repo lives in WSL. From Windows:
`\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`.
Shell commands run via
`wsl.exe -d Ubuntu-24.04 -- bash <script>` — write scripts with the
write tool and run by absolute path (PowerShell quoting caveats:
inline `&&`, `$var`, pipes, and multi-word grep alternations are all
broken; ONE COMMAND PER LINE; `sleep` is capped at 120 s — for the
corpus use the tracked background process).

```bash
# Environment (source this):
export PATH="$HOME/.cargo/bin:$PATH"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

## Verification gate for every step

```bash
# 1. Build gates (all segments green)
cargo test --features serde

# 2. Single-fixture smoke
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (writes target/gold_harness_corpus/report.md)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 bytewise check:
target/debug/dump_section_bytes <file> <A> <N>
# anchor on parentid; compare [data .. data end) bit-for-bit; the
# owner-handle form delta (silver `(4,2,abs)` vs authored `(6,0,+1)`)
# is pre-existing and corpus-wide.
```

## Commit inventory (this halt)

```
36af6fb  docs(harness): Phase A step-4 closure — LOFT/REVOLVE record + primitives queue
20d472b  fix(dwg): un-elide ACSH_LOFT/REVOLVE_CLASS — Phase A step 4, shared raw-tail helpers
2ed92ae  refactor(dwg): share the SH elide exception list between guard and nuller
48ca14a  docs(harness): Phase A step-3 closure — §18.5 record + step-4 queue
8c41aa6  fix(dwg): un-elide ACSH_EXTRUSION_CLASS — Phase A step 3
c96355f  fix(dwg): clamp sweep raw-tail capture and emit bounds (review)
2416022  fix(docs): NEXT_SESSION commit inventory — include the 14:00Z user doc commits
c1200a0  docs(harness): Phase A step-3 handover — NEXT_SESSION replaced
d36e553  docs(harness): Phase A step-2 closure — SWEEP layout autopsy + queue update
ba7d112  fix(dwg): un-elide ACSH_SWEEP_CLASS — Phase A step 2, raw-tail retention
1652af2  docs(harness): document the full Phase A/B/C plan — every phase defined
96673ec  docs(harness): zero-context completeness — full Phase A handover in NEXT_SESSION + §18.5 step-2 findings
1f06d9d  chore: retire first-session scratch — the ocs.lock rules and the cylinder example
e686903  docs(harness): Phase A step-2 probe findings — the SWEEP write path loses 113 bytes
b926053  fix(dwg): un-elide ACSH_HISTORY_CLASS — Phase A step 1
fc9f235  test(harness): F2 in-repo fixture tree — sh_history campaign
459bc74  fix(dwg): elide SH modeler-history class records at save
33ce739  fix(dwg): constructed wireframe guard
```

The branch head is this handover commit (this file); the commits
above are its parents. `1f06d9d` was the last push to
`origin/gold-vs-silver` (push only when asked).
