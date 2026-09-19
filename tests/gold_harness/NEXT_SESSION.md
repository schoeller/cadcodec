# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Delete this file when the packet it names completes (fold the outcome into
> IMPLEMENTATION.md §8.1.6).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. Drive the remaining
read/write fidelity diffs down. The current target (read AND write) is **below
1 000** (raised 12 000 → 8 000 → 5 000 → 3 000 → 1 000 on 2026-09-19; current
read 5 942 / write 5 562). At that level the target requires the silver Rust
reader campaign (the ~55% of rows where silver never stores the data) plus
the writer-fix batch and the remaining structural classes.
Land packets until both sides are under 1 000.

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — the durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec`, version-gate every conditional, handle-
   identity uses `(code, resolved_target)`, the differ/ignore-list are frozen,
   the regression gates, and the commit conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — the living plan. Read:
   - §7 "How to start cold" (entry point + current baseline + the 3
     "looks broken but isn't" traps),
   - §8.1.6 (work queue — the next packet is named there with its full
     diagnosis),
   - §8.1.6a (coverage audit — what's known vs covered, the nested-macro map,
     the exhaustive cluster census),
   - §8.1.0 (environment verification).

## Current state (2026-09-19, session handoff)

- Baseline: read-fidelity **5 942**, write-fidelity **5 562** (125 corpus
  files). Target: read AND write **below 1 000**.
- `cargo test --features serde` = 1556/0; `gold_roundtrip` = ok.
- Session 2026-09-19 landed: audit + MULTILEADER ctx + 3DSOLID ACIS +
  ACSH_HISTORY + EVALUATION_GRAPH retype + BLOCK_HEADER
  (flags/name-strip/inserts/first-last) + POLYLINE_PFACE/TABLE renames +
  control handles (BLOCK/LTYPE_CONTROL) + MLINESTYLE.lines degenerate +
  PLACEHOLDER.dxfname + SECTION/DETAILVIEWSTYLE retype + MTEXT.style
  resolve + LTYPE.dashes degenerate + underlay per-kind renames +
  TABLESTYLE.borders degenerate + DICTIONARYWDFLT.defaultid null-form +
  the DIMENSION family projection + the ASSOC family retype + the
  polyline VERTEX/SEQEND emission. All pushed on `gold-vs-silver`.
- **What the remaining ~4 950 read / ~4 560 write rows are (the next
  campaign):**
  1. **Silver Rust reader-side gaps (~55%)** — silver never *stores* the
     data, so no normalizer can project it: the xdic family on table
     entries (LAYER.xdicobjhandle/is_xdic_missing 191 + LAYER_CONTROL 235 +
     BLOCK_HEADER 150), LAYER.visualstyle 212(+202 write), SOLID.elevation
     161, LAYOUT.has_ds_data 97, LINE.linewt 74 + LAYER.linewt 66 (raw
     lweights), SORTENTSTABLE.block_owner 144, APPID.name 68 (an
     AcadAnnotative existence divergence), MLINE/MLINEm/SEQENDENTSTABLE
     tails, the VERTEX_MESH flag-64 (12), ConstraintGroup node shortfall,
     BLOCK_HEADER.entities target naming for unmodeled classes. These
     need src/io/dwg reader work in cadcodec, then their normalizer
     projections.
  2. **The unknown_bits floor (~400 rows)** — gold-only raw remainders
     (TABLESTYLE 121, DIMASSOC 62, EVALUATION_GRAPH 56,
     ASSOCDEPENDENCY 36, plus per-record unknown_bits/graphic_data of
     every unmodeled class) — irreducible unless the silver reader starts
     keeping raw remainders.
  3. **Smaller writer-side bugs**: the REGION `[ -nan ]` point bug that
     excludes example_2013/2018 from the write side entirely (~950 hidden
     rows surface once fixed), the silver ML writer flags/arrow_size
     corruption, DICTIONARYWDFLT.defaultid value rows, the DIMENSION/DIM*
     block-name ambiguity (silver's table uniquifies *D blocks),
     INSERT-owned SEQENDs, the 3DSOLID R2013+ prologue divergence (~63),
     the ACSH geometry family retype (net-0) + RENDER* classes.
- Approach for the next session: start with (1) in Rust (one reader PR
  covering the table-entry xdic/visualstyle storage), re-project, then
  the writer-fix batch (2) — the mid-rank smalls — then re-evaluate the
  floor.
- The reusable probes exist: `tests/gold_harness/` — `run_roundtrip.py`,
  `run_corpus.py`, `diff_fields.py`, `normalize_gold.py`, `normalize_silver.py`,
  `type_diff.py` (per-type diff via the frozen pipeline), `audit_type.py`
  (deep leaf-diff). Use them.

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
commands through `wsl.exe -d Ubuntu-24.04 -- bash -lc '...'`.)

## Workflow (per packet)

1. Pick the packet from §8.1.6's queue (largest remaining type first).
2. Grep the gold spec: BOTH `~/work/libredwg/src/dwg.spec` and `dwg2.spec`.
   Use the §8.1.6a nested-macro map for dotted fields. Read the full spec block
   (FIELD_* macro + version predicate + conditional guards like
   `if (dataflags & 0x02)`).
3. Locate the silver side: the reader
   (`src/io/dwg/dwg_stream_readers/object_reader/{entities,objects,tables,
   associative}.rs`) and the struct (`src/entities/<type>.rs`,
   `src/objects/<type>.rs`). Confirm silver actually stores the data (check the
   serde dump: `target/gold_harness_corpus/<file>/<file>_silver_orig.json`).
4. Make the minimal, version-gated fix in `tests/gold_harness/
   normalize_silver.py` (projection) or `normalize_gold.py` (gold-side
   canonicalization). Do NOT touch the frozen differ (`diff_fields.py`) or
   `ignore_fields.toml`.
5. Build: `cargo build --features serde --bins`.
6. Verify on all 6 versions (2000/2004/2007/2010/2013/2018) + the corpus:
   `python3 tests/gold_harness/run_corpus.py` (uses `target/audit_type.py` and
   `target/type_diff.py` for per-type checks first if the corpus run is slow).
7. Pass the gates: `cargo test --features serde` (1556/0) and
   `cargo test --features gold-harness --test gold_roundtrip` (ok).
8. Commit with the format
   `fix(harness): <packet> — <gold spec ref> + before→after counts`.
9. Update the plan (§8.1.6 queue + §8.1.6a audit) and the §7 baseline numbers.

## Hard-won lessons (do not repeat)

- **The differ compares the resolved handle-target TYPE name**, not the raw
  handle. Gold's unmodeled objects are `UNKNOWN_OBJ` (objects) / `UNKNOWN_ENT`
  (entities); silver must emit those exact names (see the `Unknown`/object-loop
  maps in `normalize_silver.py`).
- **CMC color method byte** (gold `field_cmc` / `bits.c bit_downconvert_CMC`
  4061): the `rgb` high byte is the method — `c0` = ByLayer (256), `c1` =
  ByBlock (0), `c2` = truecolor, `c3` = indexed (low byte is the index). Silver
  reads the bytes but defaults ByBlock→0; the gold normalizer collapses the
  dict. Do NOT invert c0/c1 again (that was a real bug, fixed in `77474f2`).
- **`dataflags` / `num_*` absence-bitmask** (ATTDEF/TEXT, dwg.spec 491): each
  bit means the field is ABSENT (has the default). Derive the mask from silver's
  stored values; emit the conditional fields only when their bit is clear.
- **Ref-array slot position** (DIMASSOC): gold's `ref` array is indexed by the
  associativity BIT position; silver's `references` is already slot-keyed.
  Project in place — never flatten-then-repack.
- **Version gating is value-dependent too**: a field can be version-gated AND
  conditionally present (e.g. MTEXT `bg_fill_*` only when `bg_fill_flag & 1`;
  `column_*` only when `column_type != 0`; ATTDEF conditionals on dataflags).
  Gate on BOTH the version predicate AND the value condition.
- **When a "silver gap" looks wrong, check the gold normalizer against gold's
  own spec/decoder** — the bug may be on the gold side (the c0/c1 inversion was).

## The commit / push convention

- Branch: `gold-vs-silver` (tracks `origin/gold-vs-silver`).
- Commit message: `fix(harness): <packet> — <gold spec ref> + before→after
  counts` (read and write totals from the corpus report).
- Push after each packet: `git push`.
