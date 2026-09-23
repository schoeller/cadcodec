# Zero-context prompt — the ACS/SH campaign halt: all three phases COMPLETE

> Campaign state 2026-09-23 (late). **The three-phase ACS/SH campaign is
> COMPLETE at 0/0: the corpus stands at 188 files, read 0, write 0**
> (180 + the landed §18.7 differential quads RevolveA/R ×4 versions
> each). Phase A (typed SH wire layouts, raw-tail retention) closed at
> `f368fce`→`e1dff05`; Phase C (the seven fixture families) closed at
> `9cf8e0f`→`e1dff05`; **Phase B (the blob autopsy) closed at this
> halt** — the four raw-retained node tails carry typed semantic views
> with the captured bits still the write authority, and the §18.7
> differential pipeline is now landing follow-up decode rows live
> (RevolveA/R processed: the structural profile block +
> `profile_center`/`profile_radius`/`trailing_triple` on the model).
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

- **Sweep/Extrusion** (`SolidHistorySweepTail`): the direction 3BD
  head, the all-short BD option run whose `BD('01')` member is the
  scale factor, the mid-region raw BD entries (the Polysolid's path
  unit direction `[+u_y, -u_x, -u_x, -u_y]`, twice), the byte-aligned
  profile corner pairs (the Polysolid rectangle
  `[(±2.5, {0,2})]`), and the final segment-end pair
  `(3065.007936309483, 1463.5113930448078)` — gold's R2010
  3DSOLID wireframe anchor is exactly its half (the live-oracle
  overlap that names the semantics).
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

1. **The differential queue, re-designed after the revolve closure.**
   The 2026-09-23 full-tree libredwg scan (§18.6) closed the
   revolve grammar completely (axis pair / angle / options /
   CALL-embedded profile circle / flags — every tail bit
   accounted) and rewired the recipe. **Still owed by the recipe**
   (author per §18.7, land in `sh_history/`): the revolve stems
   **RevolveC** (circle `4,0,0` r 0.8 — grammar regression
   anchor), **RevolveW** (the typed mirror `1,0,0` r 0.2, angle
   270 — predicted BIT-IDENTICAL to the original), **RevolveO**
   (axis `2.375,0,0` → `2.375,5,0` — the axis_point raw),
   **RevolveT** (axis `0,0,0` → `3.75,2.5,0` — the axis_vector
   raws), **RevolveF** (angle 360), **RevolveM** (the SURFACE-twin
   anchor: `MOde Surface` — gold parses the REVOLVEDSURFACE typed
   r2007+ and the ASSOC body's named parameters even in R2004);
   DEAD stems: RevolveI (crossing refused), RevolveP
   (perpendicular-plane refused), RevolveN/S (targets closed by
   the scan). Plus the sweep/extrude/loft stems: **PolysolidX/D**,
   **ExtrudeH/R/P/T/M**, **Loft3/H/R/M** (the M-rows = the
   surface-twin anchors for their families — the SWEEPOPTIONS
   macro's named fields + the ASSOC bodies give typed semantic
   anchors for their still-opaque regions, §18.6). Each landing
   runs the pipeline: dump, quartet identity, wire-ladder check,
   decode, position-diff, extend `sh_tail_decode.rs`, pin, four
   gates.
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

# 3. Full corpus (must stay 188 files 0/0, growing with each landed pair)
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
<this-halt docs + review pass>
<prev>  7f2a77f docs(harness): Phase B COMPLETE — the blob autopsy record + halt refresh
<prev>  9a260ae fix(dwg): Phase B blob autopsy — SH tail decoders, typed views, re-encode rule
<prev>  aeb59ed docs(harness): handover refresh — counts, tail-anchor precision, commit inventory
e1dff05  docs(harness): Phase C fixture review closure — seven families landed, BREP deferred
```

(The review-pass commit fixes two writer defects found on re-read —
the undecodable-tail verbatim fallback and the revolve span
alignment — and lands the §18.7 recipe with the closure docs; see
§18.6's "Review pass" note. Push only when asked; `1f06d9d`
remains the last remote head.)
