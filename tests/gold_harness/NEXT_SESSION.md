# Zero-context prompt — the post-H7a/H7b halt: the read axis at zero, the write-target axis at 13,653 + the three decoder walks

> Campaign state 2026-09-26 (the halt after the H7b row; the session
> ran the review → update → commit → push → continue loop from the
> H3 halt). **The ACS/SH campaign is COMPLETE at 0/0: the corpus
> stands at 280 files, read 0, write 0.** The §19 structure READ
> axis is at ZERO gaps corpus-wide (H3 landed + reviewed). The H7
> write-target axis is IN PROGRESS: **HEADER (H7a) and SummaryInfo
> (H7b) both landed at 0/0 — the write-target key-gap fell
> 21,822 → 13,653**. The maintainer's fixture surface is EMPTY.
> Read `tests/gold_harness/AGENTS.md` first, then §F2.1–F2.3 +
> §18.5–18.7 in `IMPLEMENTATION.md` (§18.6 carries the full decode
> record), then §19.1–19.3 (the structure campaign — §19.2's H3 row
> carries the read landing + review, the H7 row carries H7a/H7b),
> then this file top to bottom.

## What this session established (the load-bearing facts)

**H3 — the HEADER read row (landed `e7ead8f`, reviewed `a5ecf95`)**:
the gap was the predicted TOTAL NAMING SPLIT; the fix is
`DwgHeaderRaw` — a gold-JSON-mirror summary on the document (~300
`Option` fields, serde-renamed to gold's ALLCAPS keys, skip-if-none
so the version gates fall out of the reader walk's population),
retained by TWIN assignments in `read_header_fields` (every wire
read taken once, model + raw; the `let _ =` discards became
`raw.x = Some(..)`). struct_axis projects it key-for-key with gold's
CMC emitter shape (the embedded 256-entry gold palette — 222 entries
differ from silver's ACI table; index printed iff non-zero INCLUDING
256, rgb `%06x`, flag/name per the validated bits). The
print-exactness rules pinned in the libredwg re-analysis (all in
§19.2's H3 row): FORMAT_BS unsigned vs BSd signed (TREEDEPTH/
USERI1-5/DIMLWD/DIMLWE; the 8 FIELD_CAST fields cast to plain BS),
BL/BLx unsigned, TIMEZONE BLd, TIMEBLL [days,ms] unsigned, BD
%.14f+trim, every spec FIELD_VALUE transform ENCODER-gated, and the
CMC post-decode state (flag<4 gating, method validation to 0xC2,
the palette-derived index overwrite). **The review pass re-derived
`dwg_decode_handleref` with obj==NULL (the header walk): the
absolute ref is the RAW PAYLOAD for every code — the 6/8/A/C
base-relative arithmetic never applies in the header; the first
draft's object-relative branches were corpus-dead but wrong, fixed
(`absolute = value`).** Corpus: HEADER read 138,021+0+0; the whole
read axis at 0.

**H7a — the HEADER write row (landed `788d6f0`)**: the Phase B
write rule applied to the header — `write_header_with_encoding_opt`
splices the raw mirror into every slot the MODEL does not carry
(unmodeled fields re-emit wire values verbatim; `raw=None` keeps
the default-constant behaviour for programmatic documents); modeled
slots keep the model path (the `prepare_header` handle syncs stay
authoritative). Families fixed: the hardcoded unmodeled slots
(unknown_8..23, the 65535 trailing shorts, TSTACK, the R2007+ block,
the raw-only handles + CMCs); the INTERFERECOLOR copy-paste bug (was
written from `h.intersection_color`); the EXTMIN/EXTMAX recompute
(`prepare_header` overwrote the author's extents with silver's own
bounds — now gated on raw absence); the timespan/julian f64 roundtrip
truncating 1 ms per span (converters now round); the HANDSEED
correction overriding the author's seed (2000/PolyLine2D's own quirk
HANDSEED 975 < max 978 — gated on raw absence; entity additions
still grow the seed via the document API's `next_handle` bump).
Corpus: HEADER write-target 137,753+6,366+268 → **138,021+0+0**.

**H7b — the SummaryInfo write row (landed `9314b08`)**:
`build_summary_info` took only the version and emitted a static
all-empty block (the "times zeroed" row); it now writes the
document's `summary_info` (the H4 model) with the exact wire
grammar (8 fixed strings in order, u16-count-prefixed cp1252 on
AC1018 / UTF-16LE on AC1021+; the [days,ms] u32 pairs; the u16
property count + pairs; the two trailing u32s). Corpus: SummaryInfo
write-target 4,352+1,533+0 → **4,352+0+0**; the write-target
key-gap **21,822 → 13,653**.

**The remaining H7 rows (13,653, the write-target axis):**
CLASSES 3,246 (num_instances — silver writes its sane-parse values
where the original wire carries the desynced bytes; the gold-shadow
record is the write authority), ObjFreeSpace 2,453+30 (rebuilt
content), R2004_Header 1,771 (address/numsections shifts: silver
writes 15→17 sections), AppInfo 1,651 + AppInfoHistory 342
(rewritten blobs — the raw section bytes are already retained in the
H4 summaries), FILEHEADER 1,205 (address shifts + maint_rel 0→4),
R2007_Header 978, THUMBNAILIMAGE 442 (re-encoded — `preview.raw` is
retained; the row is ADDRESS-COUPLED: the container descriptors hold
absolute file offsets, so a byte-identical chain needs the section
at the original offset or gold-style address re-computation, which
itself changes the chain), the whole-section write drops FileDepList
1,055 + SecondHeader 386 (R2000, lives inside ObjFreeSpace),
AuxHeader 95. The verbatim-re-emit family follows the AcDs precedent
(raw section bytes + a fingerprint gate; see `acds_data` in
dwg_writer.rs). **Note: `gh44-error.dwg` is corpus-SKIPPED
(run_corpus.py:39) — its stale Sept-20 workdir is NOT
census-tracked; do not chase its diffs. A stray `h7_probe1.sh` in
the repo root is a parallel session's FileDepList probe — untracked,
not ours to commit.**

## The work: the three decoder walks (no new fixtures, interleaved per maintainer priority)

1. **The post-corner singles walk (sweep)**: the entries are
   CLASSIFIED (§18.7's Polysolid rows: the width single at bit
   1084, the record constant 4.00024414192312, the
   profile-derived 2.0109/@900/@1092, the path-derived segment
   end) but stay raw — extend `sh_tail_decode.rs` past the corner
   blocks with a proper BD walk and pin the spans.
2. **The loft container walk**: the raw-run reading is CLOSED
   (per-section `[center.x][center.y][height][radius]` runs + the
   `[π/2, π/2]` draft pair) but the model keeps `raw_doubles`
   positional — walk the inter-value regions so the per-section
   fields can be exposed as named model fields.
3. **The ExtrudeP polyline header**: the profile CALL kind 77
   body (length 544) holds the packed (x, y) vertex array; the
   grammar is ALREADY in-repo (`read_embedded_lwpolyline` in the
   object readers) — wire it into the CALL body decode.

**Dead / no-path rows (do not re-litigate)**: `LoftD` (no settings
path in the authoring release); the SH revolve option shorts +
flags through the REVOLVE command (the typed anchor is in-corpus
via RevolveM's bit-retained raw tail); **BREP stays deferred** —
only an external authentic `ACSH_BREP_CLASS` specimen re-opens it.

## The standing facts (the decode authority is §18.6)

- The four raw-retained SH tails decode to typed views with the
  captured bits as the write authority (the Phase B write rule:
  `render_*_tail` splices only differing same-form spans;
  untouched records re-emit bit-identically — pinned by the
  hermetic suite). The unknown-object records (the SURFACE twins,
  the ACSH node classes) re-emit verbatim through the raw
  passthrough arm.
- REVOLVE is fully closed (the CALL grammar); SWEEP/EXTRUSION
  through the spine + the profile CALL; LOFT through the
  per-section raw run. The hermetic cover is
  `tests/solid_history_tail_decode.rs` (15 tests) + the module
  tests in `sh_tail_decode.rs` — all run under gate 1.
- The un-quarantined C first attempts live as
  `ExtrudeCSurf_<v>`/`LoftCSurf_<v>` (their Solid re-authors
  kept the bare C names).

## Environment (complete)

The repo lives in WSL. From Windows:
`\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`.
Shell commands run via
`wsl.exe -d Ubuntu-24.04 -- bash <script>` — write scripts with the
write tool and run by absolute path (PowerShell quoting caveats:
inline `&&`, `$var`, pipes, and multi-word grep alternations are
all broken; ONE COMMAND PER LINE in script files; `sleep` is
capped at 120 s — use the tracked background process for the
corpus).

```bash
# Environment (source this):
export PATH="$HOME/.cargo/bin:$PATH"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

## Verification gate (the zero-keeping rule applies to 0/0)

```bash
# 1. Build gates
cargo test --features serde          # 1588 passed / 0 failed at this halt
cargo test --features gold-harness --test gold_roundtrip

# 2. Family smokes (any sh_history fixture must stay 0/0)
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (must stay 280 files 0/0; read key-gap 0;
#    write-target key-gap 13,653 at this halt)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 byte-walk for any writer re-encode path
target/debug/dump_section_bytes <file> <A> <N>
```

## Commit inventory (this halt — all PUSHED through `9314b08`)

```
9314b08 fix(dwg): the summary write from the model — the H7b SummaryInfo write-target row at zero (4,352 @ 0/0)   <- HEAD
788d6f0 fix(dwg): the header write splice — the H7a HEADER write-target row at zero (138,021 @ 0/0)
a5ecf95 fix(dwg): the H3 review pass — the header handle resolution pinned (absolute = raw value)
972a020 docs(harness): the halt refresh — the H3 HEADER landing, the structure read axis at zero, the H7 + decoder-walk queue
e7ead8f fix(dwg): the header raw mirror — the H3 HEADER read row at gold parity (138,021 @ 0/0)
... (the 2026-09-25/26 §19 arc below, oldest first: the plan-session
docs e1f75cd/0740827/bb73e72/3f490bd, the H0 axis skeleton + day-one
census d27c0c7 with the 15a4a01 review, the H2 header rows through
9e945fe + the 902eadc review, the H4 metadata rows 50c246d + the
745b7af review, the H5b CLASSES landing 5bbd79c, the H5c partial
35e3a9f, the H5a landing ea8e731 — the corpus held 280 files at 0/0
through every commit)
```

**PUSH STATE (2026-09-26)**: the `gold-vs-silver` branch is PUSHED
through `9314b08` (the remote tracks this halt's HEAD; push after
each landing per the maintainer's loop instruction:
`git push origin gold-vs-silver`).

**Session arc, for context**: the H3 scoping (the 280-file gold
harvest pinning the version-determined key sets) → the raw-mirror
design + the twin-assignment reader walk → the libredwg
print-exactness re-analysis (the maintainer's "ensure gold is
unique" pass: FORMAT_BS/BSd signedness, the CMC post-decode state,
the ENCODER-gated transforms) → the struct_axis projection → the
six-version probes at 0/0/0 → the corpus (read key-gap 128,489 → 0)
→ the halt docs → the review pass (the header handle resolution
fixed to `absolute = value`) → push → H7a (the write splice: the
unmodeled slots, the INTERFERECOLOR bug, the extents recompute
gate, the timespan rounding, the HANDSEED gate) → push → H7b (the
summary write from the model) → push. The corpus held 280 @ 0/0
and cargo test 1588/0 through every landing.
