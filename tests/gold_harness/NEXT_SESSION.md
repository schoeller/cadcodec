# Zero-context prompt — ACS/SH Phase A: the last two fixture packets (step 6)

> Campaign state 2026-09-23 ~20:00Z. The strict-load campaign is closed
> at zero (2026-09-21, user-verified round seven; see IMPLEMENTATION.md
> §18.4). The F2 fixture tree lives in
> `tests/gold_harness/tests/sh_history/` (28 qualified .dwg + .txt,
> `fc9f235`). Phase A steps 1–5 are DONE: every fixture-backed SH class
> now round-trips byte-faithfully — HISTORY and the typed Box/Sphere/
> Boolean arms, and SWEEP/EXTRUSION/LOFT/REVOLVE under raw-tail
> retention. **The corpus stands at fixtures 10/8 and the gold tree at
> 0/0.** This brief covers step 6: the two remaining fixture-diff
> packets, both on the 3DSOLID side. Read
> `tests/gold_harness/AGENTS.md` first (durable rules), then §F2.1–F2.3
> and §18.5 in `IMPLEMENTATION.md`, then this file top to bottom.

## Task

**Step 6**: drive the fixture tree from 10/8 toward 0/0 by fixing the
two constructed-genus 3DSOLID packets:

| packet | rows | files | symptom |
|---|---|---|---|
| `3DSOLID.wires` stub | 8 read + 8 write | Extrude/Loft/Revolve/Sphere, R2013+R2018 only | silver's 3DSOLID carries a zero-index wire cache (`wires: [0, 0, 0, 0, ...]`, `extra_in_silver`) where gold's wire list is empty |
| `3DSOLID.point` wrong-value | 2 read | Revolve_2007/2010 only | silver reads the modeler point at (0.6, 0, 0.6); gold reads (0, 0, 0) |

Both live on the 3DSOLID model-construction defaults (the
constructed-genus stances of `b9211d0` and the wireframe guard
`33ce739`), NOT on the SH node records — those are proven (L4
bit-identical across every fixture family).

### What already landed (do not redo)

- Steps 1–4 (`b926053`, `ba7d112`+`c96355f`, `8c41aa6`, `20d472b`),
  step 5 (`19308ee`): all SH lands. Shared machinery:
  `elided_solid_history_class` (one authority for the write guard and
  pointer nuller — still-elided: Wedge, Cylinder, Cone, Torus,
  Pyramid, BREP — NO fixtures exist for these classes; do not un-elide
  without one), `capture_undocumented_tail` /
  `write_undocumented_tail` (raw-tail retention), the sphere retype +
  projection in normalize_silver.py.
- Doc records: `d36e553` (step-2 autopsy + skeleton), `14f9a4a`
  (step-5 record + this queue).

### Step 6 method

1. **Wires stub** (the 16-row packet): on a smoke of, say,
   `Extrude_2018`, inspect silver's 3DSOLID vs gold's — silver's
   `wires` array is a zero-index cache (extra_in_silver means gold
   has NO wires field content the differ recognizes; gold's wire
   list for these SH-driven solids is empty). Find silver's
   constructor path that fabricates the wire cache for this genus
   (`33ce739` guarded other shape inputs — this one slipped
   through), and align the constructed stance: the SH-driven solids
   should construct an EMPTY wire list (or whatever gold's original
   parse shows for these files) — check both the read-time model
   construction and the DXF/constructed-genus code paths. The fix
   must not regress the gold tree (grep the wires construction
   users; the R2007/R2010 files do NOT stub — version- or
   shape-triggered difference worth pinning first).
2. **Point wrong-value** (2 rows, read-side): silver reads
   `(0.6, 0, 0.6)` for the 3DSOLID's modeler point on the
   Revolve_2007/2010 originals where gold reads (0, 0, 0) — again a
   constructed-genus default applied at read-construction. The
   rewrite already matches gold (the write diff is clean), so this
   is silver's model-construction stance on the ORIGINAL read.
   Pin where (0.6, 0, 0.6) enters (grep `0.6` in
   `src/document/… / src/entities` constructed defaults), verify
   against gold's -v9 trace of that 3DSOLID record's point field,
   and fix the default.
3. Gates after each packet: hermetic tests, the affected smokes
   (Extrude/Loft/Revolve/Sphere for wires; Revolve_2007/2010 for
   point), full corpus (gold 0/0 + expect fixtures → 0/0 when both
   land).
4. When the fixtures reach 0/0, that closes Phase A end to end:
   record the state in §18.5, and the NEXT_SESSION becomes Phase B
   (the blob/tail autopsy — decoding the retained raw tails, the
   SAT/SAB relationship to the wire cache, and the strict-load
   certification of the rewrite).

## The wire knowledge base (condensed; §18.5 has the full records)

- SH skeleton (verified via gold's live traces): parentid `BLd(-1)`,
  eval 33/427, value_code −9999, nodeid, hist 33/427, 16 BD
  transform, CMC (44 bits), step_id BL, material → handle stream,
  op major/minor 33/427. Class tails after that: sphere = BD radius;
  box = length/width/height BDs; boolean = RC operation + BL
  operand1/2; the sweep-family tails are raw-retained.
- Frames: R2018 = 40 bits, R2010 = 39, R2007 = [MS][BOT] (no UMC —
  hdlsize inside the record). Data ends at
  `Size×8 − frame − Hdlsize − 1` (the −1 = the text-present flag).
  Anchor comparisons on the parentid bit pattern.
- Wire primitives: raw short/long/double LITTLE-endian; BD
  `00`/`01`/`10` = raw64 / 1.0 / 0.0; BL `00`/`01`/`10`/`11` =
  LE32 / RC / 0 / 256. Silver reader positions ≡ window bits;
  `unknown_bits_by_handle` ≡ gold's `unknown_bits`.
- The owner-handle form delta (silver `(4,2,abs)` vs authored
  `(6,0,+1)`) is pre-existing, corpus-wide, and identity-equal —
  tolerate it in L4 comparisons.
- The retained raw tails are the Phase B entry point: the sweep/
  extrusion/loft/revolve records' captured bits decode to real
  option/transform/flag content (the wires stub may even relate:
  gold's empty wire list for SH-driven solids vs silver's stub
  suggests the SAT/SAB wire cache derivation differs for this
  genus).

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

## Verification gate

```bash
# 1. Build gates
cargo test --features serde

# 2. Single-fixture smokes
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (writes target/gold_harness_corpus/report.md)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 bytewise checks on any codec write-path change
target/debug/dump_section_bytes <file> <A> <N>
```

## Commit inventory (this halt)

```
<step-6 commits: code, plan, this handover>
14f9a4a  docs(harness): Phase A step-5 closure — primitives record + 3DSOLID packet queue
19308ee  fix(harness): land the sphere projection and un-elide Box/Boolean/Sphere — Phase A step 5
91c6cd3  docs(harness): review corrections — step-4 autopsy phrasing and position-bookkeeping note
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
b926053  fix(dwg): un-elide ACSH_HISTORY_CLASS — Phase A step 1
fc9f235  test(harness): F2 in-repo fixture tree — sh_history campaign
```

The branch head is this handover commit (this file); the commits
above are its parents. `1f06d9d` was the last push to
`origin/gold-vs-silver` (push only when asked).
