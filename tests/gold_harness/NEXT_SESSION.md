# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Delete this file when the packet it names completes (fold the outcome into
> IMPLEMENTATION.md §8.1.6).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. Drive the remaining
read/write fidelity diffs down. The current target (read AND write) is **below
12 000**; both are already there (read 11 900, write 10 904), so the goal is to
keep pushing toward the next milestone or hold the line while landing packets.

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

## Current state (2026-09-19)

- Baseline: read-fidelity **11 900**, write-fidelity **10 904** (125 corpus
  files).
- `cargo test --features serde` = 1556/0; `gold_roundtrip` = ok.
- The normalizer-only projection work for the common entities/objects is done.
  The remaining backlog is: MULTILEADER `ctx.*` nested projection, 3DSOLID
  (ACIS + unknown_bits), the UNKNOWN_OBJ unmodeled-object class, BLOCK_HEADER
  name/first/last_entity, and the MTEXT/XRECORD residuals (reader-coverage).
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
