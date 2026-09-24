# Zero-context prompt — the ACS/SH campaign halt: all three phases COMPLETE

> Campaign state 2026-09-24. **The three-phase ACS/SH campaign is
> COMPLETE at 0/0: the corpus stands at 244 files, read 0, write 0**
> (the 180 campaign baseline + the landed §18.7 differential quads —
> RevolveA/R and the 14 solid stems of the 2026-09-24 set; the 3
> M-stem quads are quarantined pending the surface-parser row).
> Phase A (typed SH wire layouts, raw-tail retention) closed at
> `f368fce`→`e1dff05`; Phase C (the seven fixture families) closed at
> `9cf8e0f`→`e1dff05`; **Phase B (the blob autopsy) closed** — the
> four raw-retained node tails carry typed semantic views with the
> captured bits still the write authority, and the §18.7
> differential pipeline delivered the family closures:
> **REVOLVE fully decoded** (the CALL grammar — axis pair, angle,
> options, embedded OBJ_CIRCLE profile, flags; §18.6) and
> **SWEEP/EXTRUSION decoded through the spine + the profile CALL**
> (the six SweepOptions slots named; the extrusion's embedded
> OBJ_CIRCLE/OBJ_LWPOLYLINE profile; §18.6).
> Read `tests/gold_harness/AGENTS.md` first, then §F2.1–F2.3 and
> §18.5–18.7 in `IMPLEMENTATION.md` (§18.6 is the Phase B record,
> §18.7 the differential recipe + its live outcomes), then this file
> top to bottom.

## What this halt landed (Phase B in one paragraph)

Each of the four raw-retained tails — `SolidHistorySweep::shsw_raw_tail`
(serving SWEEP and EXTRUSION) plus `SolidHistoryLoft::raw_tail` and
`SolidHistoryRevolve::raw_tail` — now decodes into a typed view
(populated by `src/io/dwg/sh_tail_decode.rs` right after the Phase A
capture; `None` when the anchor layout doesn't hold):

- **Sweep/Extrusion** (`SolidHistorySweepTail`) — **DECODED through
  the §18.7 differential (2026-09-24)**: the direction 3BD head, the
  SIX NAMED SPINE SLOTS in the SweepOptions order
  `[draft_angle][draft_start_distance][draft_end_distance]
  [twist_angle][scale_factor][align_angle]` (ExtrudeT's 15° draft
  lands raw in slot 0; the 1.0 default is the scale), the sweep-only
  extras (the Polysolid's two trailing zeros), the mid-region raw BD
  frame entries (the Polysolid's path unit direction
  `[+u_y, -u_x, -u_x, -u_y]` — confirmed on three directions by
  PolysolidX/D), the byte-aligned profile corner pairs, the final
  segment-end pair (gold's R2010 wireframe anchor is exactly its
  half — the live-oracle overlap), and — on EXTRUSION tails — the
  embedded PROFILE CALL `[BL kind][BL bit-length][body]` closing at
  bit_len − 2: kind 18 = OBJ_CIRCLE with the body
  `[center 3BD][radius BD][normal 3BD]` (the landed/H/T quads:
  circle (0,0,0) r 1.0-short; ExtrudeR: r 3.125-raw, the CALL length
  16 → 80), kind 77 = OBJ_LWPOLYLINE (ExtrudeP, length 544; the
  packed vertex array awaits its header grammar). The pre-CALL
  region between the spine and the CALL stays opaque
  (profile-dependent, value-stable across the radius/height/taper
  differentials).
- **Loft** (`SolidHistoryLoftTail`): head `[1.0]` + raw run
  `[2.0, 2.0, 5.0, 0.3, π/2, π/2]` (positional).
- **Revolve** (`SolidHistoryRevolveTail`) — **CLOSED by the
  2026-09-23 full-tree libredwg scan** (§18.6): the grammar is
  `[axis_pt (0,0,0)][axis_vec (0,1,0)][revolve_angle raw][6
  BD0 options][CALL: BL 18 = OBJ_CIRCLE, BL bit-length][the
  embedded profile circle: center 3BD / radius BD / normal 3BD]
  [2 flag bits]` — every landed tail accounts bit-exactly. The
  original's circle = center (1.0, 0, 0) — the x stored in the
  two-bit short form, which is what the raw-scan misread —
  radius 0.2, normal (0,0,1): the as-drawn profile, no "different
  form" ever existed. The model carries axis_point/axis_vector/
  revolve_angle/option_doubles/profile_center/profile_radius/
  profile_normal, all splice-backed.

**The write rule holds**: the captured bits are the authority;
`render_*_tail` re-decodes the stored tail and splices ONLY the
differing raw spans when a decoded field was programmatically
modified — untouched records re-emit bit-identically (pinned), an
edit lands bit-locally (tail/record size never changes), and raw
LE64 spans accept any f64 while short spans splice only same-form
`0.0↔1.0` flips. Layer-4 evidence: an unmodified-vs-edited pair
differs at exactly two 16-byte rows in the objects section (the
splice + the section checksum).

## The open rows (what re-opens work — no defined phase remains)

1. **The differential queue: AUTHORED, QUALIFIED, and mostly DECODED.**
   The maintainer landed the full §18.7 set (2026-09-24): the 14
   solid stems (56 files) entered the corpus at 0/0 (244 files
   now, quads bit-identical per stem) and their differential
   outcomes are recorded per row in §18.7 — the sweep option
   spine is named (the draft_angle raw at bit 70; the
   SweepOptions order), the extrusion payload is the profile
   circle (radius raw / polyline), the height lives only in the
   direction head, the loft height/radius slots are named, the
   sweep frame direction entries are confirmed on a second
   direction, the revolve axis pair takes offset/tilt (world-X
   profile centers, normalized directions, the axis point = the
   perpendicular foot from the profile), 360° = plain 2π, and
   RevolveW came out BIT-IDENTICAL to the original. The 3 M-stems
   (12 files) are QUARANTINED in `tests_quarantine/sh_history/`
   pending the silver surface-parser row (the R2007+ surface
   entities + ASSOC surface action bodies; 14 diffs/file today).
   **Work state:** (a) DONE 2026-09-24 — the sweep spine is named
   (all six slots, splice-backed), the extrusion profile CALL
   decodes (the circle body fully; the polyline CALL recorded with
   its packed vertices pending the header grammar), pinned by four
   new hermetic tests + the rewritten module tests (the suite is
   15 green); the loft slots stay positional (the
   values are BD raws the marker scan reads fine; the strict BD
   walk from the head derails on the non-BD regions between them —
   the inter-value grammar is the unnamed part).
   PLUS the loft raw-run reading is now WIRE-VERIFIED (2026-09-24,
   z-separated silhouette fits of the landed original: bottom
   circle (0,0) r 1.0, top circle (2.006, 2.006) r 0.2996): the
   raws are [top center.x][top center.y][top z][top radius]
   [π/2][π/2] — the "drag residue" was the dragged top section.
   (b) OPEN — the surface-parser row (the ASSOC* SURFACEACTIONBODY
   classes + the R2007+ surface entities) to un-quarantine the
(c) NEAR-COMPLETE — the re-authored (MOde = Solid) ExtrudeC and
   LoftC LANDED in-corpus (corpus 248 -> 256 files, 0/0, quads
   bit-identical) with both predictions confirmed 100 PERCENT:
   ExtrudeC reads the profile CALL at length 16 -> 144 with the
   first nonzero profile center (2.0, 3.0, 0.0) — AND THE PRE-CALL
   REGION IS RESOLVED: it moved with the offset, carrying the
   profile center as its own raw-BD run (208 + 128 + 128 = 464
   bits exactly); LoftC reads [3.0, 4.0, 1.5, 3.0, 4.0, 7.0, 1.5,
   pi/2, pi/2] — THE LOFT RAW RUN IS FULLY NAMED: per-section
   [center.x][center.y][height][radius] runs (0.0/1.0 elided as
   shorts) + the [pi/2, pi/2] draft pair, the world reading (the
   offsets PRESENT), and the landed original retro-fits exactly.
   The surface-mode first attempts remain in the quarantine as
   offset-variant specimens. The ONLY remaining maintainer ask is
   **PolysolidL** (P2 — the 2.0109 path-length probe; the §18.7
   row stands). Agent rows: the post-corner singles walk, the loft
   container walk, the ExtrudeP polyline header, the
   surface-parser row (20 quarantined files). The loft slot
   NAMING (exposing the per-section fields on the model) needs the
   container walk first; the raw_doubles list stays positional
   until then.
2. **BREP stays deferred** (Phase C record): the row re-opens if an
   authentic `ACSH_BREP_CLASS` specimen surfaces.
3. Campaign closure prose (§18.5's phase map now fully checked):
   the next campaign is the maintainer's to set — the strict-load
   zero and parser-parity zero both held throughout.

## Environment (complete)

The repo lives in WSL. From Windows:
`\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`.
Shell commands run via
`wsl.exe -d Ubuntu-24.04 -- bash <script>` — write scripts with the
write tool and run by absolute path (PowerShell quoting caveats:
inline `&&`, `$var`, pipes, and multi-word grep alternations are all
broken; ONE COMMAND PER LINE in script files; `sleep` is capped at
120 s — use the tracked background process for the corpus).

```bash
# Environment (source this):
export PATH="$HOME/.cargo/bin:$PATH"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

## Verification gate (unchanged; the zero-keeping rule applies to 0/0)

```bash
# 1. Build gates
cargo test --features serde

# 2. Family smokes (24 fixtures: the 16 campaign quads + the landed
#    differential quads, all 0/0)
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (must stay 244 files 0/0, growing with each landed pair)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 byte-walk for any writer re-encode path
target/debug/dump_section_bytes <file> <A> <N>
```

Phase B's hermetic cover lives in
`tests/solid_history_tail_decode.rs` (decode pins from the real
fixture tails, full-stack round-trips, bit-local edit spans) plus
the render-rule tests inside `sh_tail_decode.rs` — these run under
gate 1.

## Commit inventory (this halt)

```
<this review pass>
5c89b59 fix(dwg): the sweep spine named + the extrusion profile CALL — §18.7 differential decode
57232a6 test(harness): the §18.7 differential set lands — 14 solid stems in-corpus, 3 M-stems quarantined
811b0d8 docs(harness): the two surface-twin §18.7 rows the queue already promised
804e892 test(harness): the scan-closure review pass — a dead test revived, the records re-unified
daedfb7 docs(harness): the full-tree scan record — §18.6 revolve closure + the re-designed §18.7 queue
05368b3 fix(dwg): the revolve tail fully decoded — the CALL grammar, closed by the libredwg scan
839012c docs(harness): the crossing-class theory dies — wire regression + the RevolveI refusal
a656f99 fix(harness): the revolve axis correction — Y by wire footprint, plan-view authoring constraint
9d08280 docs(harness): the §18.7 live pipeline record — RevolveA/R outcomes, remaining stems
ac547e7 test(harness): the §18.7 differential quads RevolveA/R — first matrix rows, qualified
86ce5a7 fix(dwg): the revolve structural profile block — §18.7 pipeline, RevolveA/R evidence
f2891b1 docs(harness): revolve sufficiency review — the pair grows to a seven-stem matrix
7f2a77f docs(harness): Phase B COMPLETE — the blob autopsy record + halt refresh
9a260ae fix(dwg): Phase B blob autopsy — SH tail decoders, typed views, re-encode rule
e1dff05 docs(harness): Phase C fixture review closure — seven families landed, BREP deferred
```

(The session's arc: the Phase B halt + review pass; the §18.7
differential recipe; the RevolveA/R quads landed and decoded; the
plan-view axis correction (all specimens +Y); the crossing-class
theory dead on the maintainer's refusal; the full-tree libredwg
scan CLOSING the revolve family (the CALL grammar); the maintainer
authoring the full 17-stem §18.7 set — 14 solid stems landing
in-corpus with their differential outcomes, 3 M-stems quarantined;
and the sweep spine + extrusion profile CALL decode. **This halt
PUSHES to `origin/gold-vs-silver`** (the first push since
`1f06d9d`; the branch tip becomes the pushed head).

