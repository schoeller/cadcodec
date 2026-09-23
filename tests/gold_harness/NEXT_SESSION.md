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
- **Revolve** (`SolidHistoryRevolveTail`): head
  `[0,0,0,0,1.0,0]` (evidence-led reading: `[axis_pt
  (0,0,0)][axis_dir (0,1,0)]` — every landed specimen is a +Y
  revolution, footprint-verified), then `revolve_angle` (confirmed
  on two values: the original's 3π/2 and the A/R quads' π), then
  the structural `[profile center 3BD][radius BD]` block — the
  original (0.2, 0, 0) r 1.0 (radius in the short BD form), the
  A/R tori (2, 0, 0) r 0.8/1.25 raw + the `(0,0,1)` trailing
  3BD the crossing class lacks.

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

1. **The opaque mid-regions — the differential queue is LIVE.** The
   §18.7 recipe's first two revolve stems (RevolveA/R) are LANDED,
   QUALIFIED and DECODED (2026-09-23): both quads are bit-identical
   across their four versions, the corpus took them at 0/0 (188 files
   now), they confirmed `revolve_angle` on a second value (π), and
   they resolved the old "0.2 entry": the revolve tail carries a
   structural `[profile center 3BD][profile radius BD]` block — the
   original's 0.2 is its profile center.x, and its radius 1.0 hides
   in the two-bit short BD form; the torus class (A/R) adds a
   `(0,0,1)` trailing 3BD the crossing class lacks. The model now
   exposes `profile_center`/`profile_radius`/`trailing_triple`
   (splice-backed, bit-locally edited). **The 2026-09-23 authoring
   constraint: the typed Z axis is NOT workable in the plan view —
   all revolve rows use Y-family axes (footprint-verified: A/R and
   the original are all +Y revolutions). Still owed by the recipe**
   (author per §18.7, land in `sh_history/`): the remaining revolve
   matrix stems **RevolveC** (center `4,0,0` r 0.8, Y axis —
   center-only: is the first raw really the center.x?),
   **RevolveI** (center `0.6,0,0` r 0.8 crossing the Y axis — the
   trailing-trio absence + the mid-region + the twice-named
   predictions: profile (0.6, 0.8) both raw, no trio), **RevolveO**
   (axis `2.375,0,0` → `2.375,5,0`, Y-PARALLEL offset — world-X vs
   axis-relative distance for the center + the head's raw-2.375
   test of the `[axis_pt][axis_dir]` reading), **RevolveT** (axis
   `0,0,0` → `3.75,2.5,0`, an in-plane tilt — the head GROWS ~128
   raw bits iff `[axis_pt][axis_dir]`, stays ~12 bits iff options:
   a size arbitration), **RevolveF** (Y axis, angle typed 360 —
   the full-turn encoding and the trailing flags); plus the
   sweep/extrude/loft stems **PolysolidX/D**, **ExtrudeH/R/T/P**,
   **Loft3/H/R** (§18.7 rows). The next session runs the same
   pipeline on each landing: dump, QUARTET-IDENTITY + the
   FOOTPRINT-AXIS CHECK (the A/R lesson), decode, position-diff,
   extend `sh_tail_decode.rs`, pin, four gates.
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
