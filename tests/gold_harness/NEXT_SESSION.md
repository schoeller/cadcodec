# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Delete this file when the packet it names completes (fold the outcome into
> IMPLEMENTATION.md §8.1.6).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. Drive the remaining
read/write fidelity diffs down to **below 1 000 on BOTH sides** (current:
read **4 001** / write **3 835**; raised 12 000 → … → 1 000 on 2026-09-19).
At this level the remaining mass is: the writer-fix batch (led by the REGION
NaN bug that currently excludes example_2013/2018 from the write side
entirely), the unmodeled-class coverage (`UNKNOWN_OBJ._missing` 264), the
mesh/SEQEND/vertex families, and the **unknown_bits floor (~450)** — the
floor is irreducible until silver's reader keeps raw remainders, and
reaching < 1 000 *requires* that plus the UNKNOWN rows; budget accordingly
(likely more than one session).

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec`, version-gate every conditional,
   handle-identity uses `(code, resolved_target)`, the differ/ignore-list
   are frozen, regression gates, commit conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — the living plan. Read §7
   (entry point, baseline, "looks broken but isn't" traps), §8.1.0
   (environment verification), §8.1.6 (queue — the newest DONE entries
   from 2026-09-19 carry the live remaining-campaign list and the
   **linewt-28 preservation recipe**), §8.1.6a (coverage audit).

## Current state (2026-09-19, session handoff)

- Baseline: read-fidelity **4 001**, write-fidelity **3 835** (125 corpus
  files; report counts are stem-collision inflated — rank only).
  `cargo test --features serde` = 1556/0; `gold_roundtrip` = ok.
- Last session landed 3 packets (all pushed on `gold-vs-silver`):
  xdic family + LAYER.visualstyle (`3cff463`), mid-rank batch
  (`5c75b1d`), SOLID.elevation + linewt index projections (`8653303`).
- **Remaining mass, in recommended packet order:**
  1. **Writer-fix batch**: the REGION `[ -nan ]` point bug (silver's REGION
     writer emits NaN; it excludes example_2013/2018 from the write side —
     ~950 hidden rows surface once fixed, so fix FIRST and re-baseline),
     then the smalls: APPID/BLOCK/LTYPE/LAYER write-side `is_xref_ref`
     (~200), the DIMENSION/DIM* block-name ambiguity (silver's table
     uniquifies `*D` blocks), INSERT-owned SEQENDs (entity-common fields on
     synthesized SEQENDs: ownerhandle/plotstyle/shadow/plotstyle_flags +
     counts), the 3DSOLID R2013+ prologue divergence (~63), ML writer
     flags/arrow_size, DICTIONARYWDFLT.defaultid value rows.
  2. **linewt-28 preservation** (~37 orig rows, reader+writer, full recipe
     in §8.1.6 — preserve the raw entity-common linewt byte that
     `from_dwg_index(28)` ligates away).
  3. **UNKNOWN_OBJ._missing 264** — unmodeled-class reader coverage
     (TABLE entity, BLOCKGRIPLOCATIONCOMPONENT._missing 34, ACSH family,
     ConstraintGroup node shortfall, BLOCK_HEADER.entities target naming).
  4. **Mesh/SEQEND/vertex families** (~250): POLYLINE_MESH/VERTEX_MESH
     retypes+counts (TS1), MESH flags/M_vertex_count, MLINE/MLINEm tails,
     VERTEX_MESH flag-64, SEQENDENTSTABLE tails.
  5. **The unknown_bits floor** (~450: TABLESTYLE 121, DIMASSOC 62,
     EVALUATION_GRAPH 56, ASSOCDEPENDENCY 36, plus per-record
     unknown_bits/graphic_data of unmodeled classes) — needs raw-remainder
     storage in silver's reader (new side-channel feature, see the
     xdic_by_handle precedent).

## Environment

```
cd ~/work/cadcodec
source "$HOME/.cargo/env"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
python3 tests/gold_harness/check_env.py   # must print "Environment looks good"
cargo build --features serde --bins        # must succeed before any edit
```

(If running from Windows, the repo lives in WSL; reach it via
`\\wsl$\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec` and run shell
commands through `wsl.exe -d Ubuntu-24.04 -- bash <script>` — wsl.exe
strips embedded quotes/pipes, so put non-trivial shell and all probe
python into script files under `target/probes/` and execute those.)

## Workflow (per packet)

1. Pick the packet from §8.1.6's queue (or the order above).
2. Grep the gold spec: BOTH `dwg.spec` and `dwg2.spec`; use §8.1.6a's
   nested-macro map for dotted fields; read the full spec block
   (macro + version predicate + value guards).
3. Locate the silver side: reader
   (`src/io/dwg/dwg_stream_readers/object_reader/{entities,objects,tables}.rs`),
   writer (`src/io/dwg/dwg_stream_writers/object_writer/*.rs`),
   struct (`src/entities|objects|tables/<type>.rs`). Confirm silver stores
   the data (check `<stem>_silver_orig.json` — but on FRESH per-version
   runs, see the stem-collision lesson below).
4. Minimal, version-gated fix in `normalize_silver.py` (projection) or
   `normalize_gold.py`; reader/struct/writer changes only when the data
   isn't stored (never touch `diff_fields.py`/`ignore_fields.toml`).
5. `cargo build --features serde --bins`.
6. Verify on all 6 versions (2000/2004/2007/2010/2013/2018) + affected
   corpus files via `run_roundtrip.py` into fresh `target/probe_wip/<v>`
   dirs; then `run_corpus.py` for the full numbers.
7. Gates: `cargo test --features serde` (1556/0) and `cargo test
   --features gold-harness --test gold_roundtrip` (ok).
8. Commit: `fix(harness): <packet> — <gold spec ref> + before→after counts`.
9. Update §7 baseline + §8.1.6 queue (and §8.1.6a when classes change).

## Hard-won lessons (do not repeat)

- **The differ compares the resolved handle-target TYPE name**, not the
  raw handle. Unmodeled objects are gold `UNKNOWN_OBJ`/`UNKNOWN_ENT`;
  silver must emit those exact names.
- **CMC color method byte** (bits.c 4061): high byte is the method —
  `c0` = ByLayer (256), `c1` = ByBlock (0), `c2` = truecolor, `c3` =
  indexed. Do NOT invert c0/c1 again (fixed in `77474f2`).
- **`dataflags`/`num_*` absence-bitmask**: each bit means the field is
  ABSENT (default). Emit conditionals only when their bit is clear.
- **Gold's REPEAT/REPEAT_CN JSON collapses every sub-struct to a bare 0**
  (`[0]*n`): TABLESTYLE.borders, LTYPE.dashes, MLINESTYLE.lines /
  MLINEm, MULTILEADER ctx.leaders, DIMASSOC.ref (all six slots `[0]*6`
  even when the wire holds real OsnapPointRefs — verified 2026-09-19).
  Never build full-dict projections for these; check gold's degenerate
  shape FIRST.
- **Silver's `LineWeight` enum** serializes as `{"Value": <mm*100>}` for
  concrete weights and strings ("ByLayer"/"ByBlock"/"Default") for the
  named variants; gold's `linewt` is the lweights[] index 0..23 plus
  29/30/31 for the named three — invert via `_lineweight_to_gold`
  (normalizer). The raw byte 28 (ByLayer alias) still gets ligated away —
  see the §8.1.6 preservation recipe.
- **Side channels are the projection route** for records whose structs
  lack a field: silver's dump (`dwg2json.rs`) flattens the whole
  `CadDocument`, so document-level maps are serde-visible —
  `xdic_by_handle`/`reactors_by_handle` (decimal-string keys) and
  `dwg_data_store_handles` (handle list, un-skipped `5c75b1d`). Emit
  + gate per gold's versioned shapes (xdicobjhandle on ALL versions when
  present; is_xdic_missing bit R2004+; has_ds_data R2013+).
- **Stem collisions contaminate the pooled corpus artifacts** (five
  `Line.dwg` versions share `target/gold_harness_corpus/Line/`; last-wins).
  NEVER derive field shapes from those files — use them for ranking only,
  and run fresh `run_roundtrip.py` probes per version first (the earlier
  R2000 "material on LAYER" scare was just the R2018 survivor).
- **Version gating is value-dependent too**: gate on BOTH the version
  predicate AND the value condition (MTEXT bg_fill only when
  `bg_fill_flag & 1`, ATTDEF dataflags, etc.).
- **When a "silver gap" looks wrong, check the gold normalizer against
  gold's own spec/decoder** — the bug may be gold-side (CMC c0/c1 was).
- **Silver's writer reference types**: `DwgReferenceType` codes are
  2 softowner, 3 hardowner, 4 softpointer, 5 hardpointer per this
  codebase's enum — gold's FIELD_HANDLE 2nd arg is that wire code.

## The commit / push convention

- Branch: `gold-vs-silver` (tracks `origin/gold-vs-silver`).
- Commit: `fix(harness): <packet> — <gold spec ref> + before→after counts`.
- Push after each packet: `git push`.
