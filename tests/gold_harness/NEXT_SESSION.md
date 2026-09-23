# Zero-context prompt — the ACS/SH campaign halt: all three phases COMPLETE

> Campaign state 2026-09-23 (late). **The three-phase ACS/SH campaign is
> COMPLETE at 0/0: the corpus stands at 180 files, read 0, write 0.**
> Phase A (typed SH wire layouts, raw-tail retention) closed at
> `f368fce`→`e1dff05`; Phase C (the seven fixture families) closed at
> `9cf8e0f`→`e1dff05`; **Phase B (the blob autopsy) closed at this
> halt** — the four raw-retained node tails now carry typed semantic
> views with the captured bits still the write authority. Read
> `tests/gold_harness/AGENTS.md` first, then §F2.1–F2.3 and §18.5–18.6
> in `IMPLEMENTATION.md` (§18.6 is the Phase B record), then this
> file top to bottom.

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
- **Revolve** (`SolidHistoryRevolveTail`): option spine
  `[0,0,0,0,1.0,0]`, then `revolve_angle = 3π/2` (270°, the one
  confirmed named angle), then raws `[0.2]`.

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

1. **The opaque mid-regions.** The sweep frame blocks' un-named
   remainder (the −0.9446…/−1689439.46-class entries), the
   Extrusion's 64-bit payload, and the Loft's leading 68-bit
   region round-trip verbatim and stay untouched; naming them
   needs the differential instrument the brief predicted — a
   second specimen per family with DIFFERENT geometry (the fixture
   tree has one distinct specimen per family; the strict-load gold
   tree carries no other sweep-family members). **A maintainer
   action:** author e.g. a slanted two-segment POLYSOLID, a
   tapered EXTRUDE, a three-section LOFT, a 180° REVOLVE (with
   .txt companions per §F2.2), land them in `sh_history/`, and the
   next session runs the differential decode off those pairs.
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

# 2. Family smokes (16: 4 families x 4 versions, all 0/0)
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (must stay 180 files 0/0)
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
<docs>  docs(harness): Phase B COMPLETE — the blob autopsy record + halt refresh
<code>  fix(dwg): Phase B blob autopsy — SH tail decoders, typed views, re-encode rule
```

(Push only when asked; `1f06d9d` remains the last remote head.)
