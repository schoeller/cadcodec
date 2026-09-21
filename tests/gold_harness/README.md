# Gold-vs-Silver Roundtrip Harness

A repeatable test harness that closes the read/write fidelity gap between
**LibreDWG** (the *gold* oracle) and **cadcodec** (`acadrust`, the *silver*
implementation) for DWG files. It decodes a DWG with both libraries, rewrites
it with cadcodec, decodes the rewrite again, and reports field-level
differences in the non-header object data.

The full plan, architecture rationale, and the autonomous fix-loop
specification live in [`IMPLEMENTATION.md`](./IMPLEMENTATION.md). This README
is the practical entry point: install, run, interpret.

---

## Oracles — the four validation layers

| # | Oracle | What it catches | Needs the gold oracle? |
|---|---|---|---|
| 1 | Deep unit gates — `cargo test --features serde` (47 ok segments; roundtrip asserts `diffs <= max_known`) | model/retention regressions; a new raw-retention field without a `normalize_entity_for_comparison` arm trips the budget and the failing test names it | **no** — fully hermetic |
| 2 | Harness integration test — `cargo test --features gold-harness --test gold_roundtrip` | harness self-check + prohibited storage-only `EntityCommon` fields | **optional** — skips (with a notice written to `target/gold_harness_oracle_skipped.txt`) when `GOLD_DWGREAD`/`GOLD_TESTDATA` are absent; set `GOLD_HARNESS_REQUIRE=1` to make absence a hard failure (CI) |
| 3 | Full corpus — `run_corpus.py` → `report.json` + the residue dump (`pk18a_all_rows.py`) | non-header field divergences; read/write 0/0 is the campaign target (`per_file` is truth; the by-type tables truncate) | yes |
| 4 | Authored-wire byte-fidelity — byte-compare silver's *rewrite* of an authored file against the authored original, record by record | writer **form** defects both decoders tolerate (legal-but-different bitcode choices — a BS short form where the authored wire used the raw-16 form, BD shortforms vs raw doubles, alpha-method nibbles) that strict CAD consumers (BricsCAD, AutoCAD) reject | yes |

Layers 1–3 keep gold-vs-silver **parser parity** at 0/0. Layer 4 closes their
structural blind spot: the rt pair compares two lenient reads of the *same*
silver bytes, so it can never flag an encoding *form* — only byte-for-byte
comparison against the authored wire can. Full procedure and worked examples:
[`IMPLEMENTATION.md` §18](./IMPLEMENTATION.md).

Layer 4's wire facts for record walking: the R2000+ object frame is
`[MS size][R2010+ UMC hdlsize][BOT type][window]` where the window starts at
the BOT byte; `bitsize = Size*8 − Hdlsize` is the handle-stream start, and
gold's `-v9` trace prints per-field `@byte.bit` positions in window
coordinates to walk against. Two harness instruments implement it:

- `dump_section_bytes` — record-framed raw byte dumps for the pair compare.
- `dump_proxy_graphics [--verify] FILE [HANDLE]` — derives + dumps the
  entity-common proxy-graphics metafile (the ODA "Proxy Entity Graphics"
  stream; format + type census in `acadrust::entities::proxy_graphics`), and
  with `--verify` asserts decode→encode byte-equality against the wire
  bytes.

The layer-4 campaign result it instrumented (closed 2026-09-21): silver's
rewrite of `2018/Leader.dwg` reproduces the LEADER and MULTILEADER records
byte-identical to the authored wire, and the strict-load target
(`gen_all_entities_all_versions.dwg`, 30 entities, the LEADER warn-class and
the MULTILEADER fatal-class both rooted through form mismatches both decoders
tolerate) opens in BricsCAD via plain `_open` with zero warnings.

---

## What it does

For each DWG file the harness produces three diffs:

| Diff | Compares | Finds |
|---|---|---|
| **Read fidelity** (`*_diff_orig.json`) | gold's decode vs silver's decode of the original | fields cadcodec's *reader* drops or misparses |
| **Write fidelity** (`*_diff_rt.json`) | gold's decode of the original vs gold's decode of cadcodec's rewrite | fields cadcodec's *writer* omits or corrupts |
| **Internal consistency** (stubbed) | silver's decode of original vs rewrite | cadcodec read→write→read self-check |

Header data is **out of scope** (compared laxly); only the top-level `OBJECTS`
array (entities + non-entity objects) is diffed exactly.

---

## Requirements

| Dependency | Purpose | Provided via |
|---|---|---|
| Built LibreDWG `dwgread` | gold oracle (`-O JSON`) | `GOLD_DWGREAD` env var — **oracle-optional**: `cargo test` skips gold checks without it; fetch/build on demand with `bash tests/gold_harness/bootstrap_oracle.sh` |
| LibreDWG `test/test-data` | DWG corpus | `GOLD_TESTDATA` env var |
| Rust toolchain (`cargo`) | builds silver binaries | system |
| Python 3.11+ (with `tomllib`; 3.8–3.10 need `tomli`) | normalizers + differ | system |

The harness itself (normalizers, differ, drivers, the two Rust binaries under
`src/bin/`) is self-contained in this directory. Nothing else in the repo is
required to run it, and the default `cargo test` suite stays hermetic (the
harness is behind the off-by-default `gold-harness` feature).

---

## Installation

These steps build the gold oracle and the silver binaries. They assume a
Linux/WSL environment with a standard build toolchain.

### 1. Build LibreDWG (gold oracle)

```bash
cd ~/work
git clone https://github.com/LibreDWG/libredwg.git
cd libredwg
sudo apt install build-essential autoconf automake libtool texinfo perl python3 jq
sh ./autogen.sh
./configure --disable-bindings --disable-docs
make -j"$(nproc)"
# Smoke test:
programs/dwgread -O JSON test/test-data/2000/Line.dwg | jq .
```

`programs/dwgread` is the only artifact the harness needs. The corpus comes
with the clone under `test/test-data/`.

### 2. Point the harness at LibreDWG

```bash
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

### 3. Build the silver binaries

```bash
cd ~/work/cadcodec
cargo build --features serde --bins
```

This builds `dwg2json` (silver JSON dump) and `dwgrewrite` (read→write), both
registered as Cargo `[[bin]]` targets with sources in `src/bin/`.

### 4. Verify the environment

```bash
python3 tests/gold_harness/check_env.py
```

It confirms `GOLD_DWGREAD` is executable and supports `-O JSON`, that
`GOLD_TESTDATA` has the `2000`…`2018` version folders, and that `cargo` is on
`PATH`.

---

## Running — manual

All commands assume the env vars from step 2 are set and you are in the
cadcodec repo root.

### Single file

```bash
python3 tests/gold_harness/run_roundtrip.py \
    "$GOLD_TESTDATA/2000/Line.dwg"
```

Outputs land in `target/gold_harness/` (or a directory you pass as the second
argument): `*_gold_orig.json`, `*_silver_orig.json`, `*_rt.dwg`,
`*_gold_rt.json`, `*_silver_rt.json`, `*_diff_orig.json`, `*_diff_rt.json`,
and a human-readable `*_report.md`.

### Whole corpus (batch)

```bash
python3 tests/gold_harness/run_corpus.py
```

Iterates the in-scope corpus (`test/test-data/{2000,2004,2007,2010,2013,2018}/*.dwg`
plus top-level `example_*`/`sample_*`) and writes an aggregated
`target/gold_harness_corpus/report.json` + `report.md` ranking divergent
`(entity_type, field)` pairs by frequency.

### Cargo integration test

```bash
cargo test --features gold-harness --test gold_roundtrip
```

Oracle-optional: shells out to the driver for a representative subset
(`2000/Line.dwg`, `2000/circle.dwg`) and asserts the harness runs cleanly and
that no prohibited `EntityCommon` storage-only fields appear in the diffs.
Without a LibreDWG checkout the test skip-passes and writes
`target/gold_harness_oracle_skipped.txt`; `GOLD_HARNESS_REQUIRE=1` turns
absence into a hard failure (CI), and
`bash tests/gold_harness/bootstrap_oracle.sh` clones and builds the oracle
online when you want the real fidelity run.

**Strict mode** — assert zero `missing_in_silver` fields on the subset:

```bash
GOLD_HARNESS_STRICT=1 cargo test --features gold-harness --test gold_roundtrip
```

---

## Running — agentic (autonomous fix loop)

The harness is designed to be driven by an implementation-capable agent that
edits cadcodec until the covered corpus converges. The complete operating
manual — including context-budget rules for a 128K-token window, the per-field
decision tree, and the fix recipe — is
[`IMPLEMENTATION.md` §8.1](./IMPLEMENTATION.md#81-subagent-execution-guide-128k-context).

Minimal loop for an agent:

```bash
cd ~/work/cadcodec
source "$HOME/.cargo/env"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"

# 1. Baseline over the corpus
python3 tests/gold_harness/run_corpus.py

# 2. Pick the top (entity_type, field) offender from
#    target/gold_harness_corpus/report.md, consult the gold spec
#    (libredwg src/dwg.spec / dwg2.spec), fix silver version-gated.

# 3. Rebuild and re-verify on ALL covered versions
cargo build --features serde --bins
for v in 2000 2004 2007 2010 2013 2018; do
  python3 tests/gold_harness/run_roundtrip.py \
      "$GOLD_TESTDATA/$v/Line.dwg" "target/gold_harness_wip/$v"
done

# 4. Regression gate (must all pass, and corpus diff count must strictly drop)
cargo test
cargo test --features serde
cargo test --features gold-harness --test gold_roundtrip
```

**Loop invariants (hard rules):**

- Never edit LibreDWG — it is a read-only oracle.
- Never edit `ignore_fields.toml` or `diff_fields.py` to make a diff pass.
- Never touch version dispatch, decompression, CRC, or the section map.
- Gate every fix behind the exact version predicate gold uses.
- Each checkpoint must leave the build green.
- Header comparison stays lax.

See §8.1 for the full packet discipline, blocked-handling, and stop
conditions.

---

## File inventory

| Path | Role |
|---|---|
| `run_roundtrip.py` | Single-file driver (the three diffs) |
| `run_corpus.py` | Batch driver + aggregated report |
| `normalize_gold.py` | LibreDWG JSON → canonical records |
| `normalize_silver.py` | cadcodec JSON → canonical records (holds the live type/field maps) |
| `diff_fields.py` | Diff engine (`missing_in_silver`, `wrong_value`, `extra_in_silver`, `count_mismatch`) |
| `ignore_fields.toml` | Curated fields the differ skips (**frozen** during the fix loop) |
| `check_env.py` | Environment sanity checker |
| `bootstrap_oracle.sh` | On-demand LibreDWG checkout + build (the gold oracle), prints the env exports |
| `src/bin/dwg2json.rs` | Silver JSON dump (re-injects serde-skipped `EntityCommon` fields under `_common_dwg`) |
| `src/bin/dwgrewrite.rs` | Silver read→write binary |
| `src/bin/dump_section_bytes.rs` | Record-framed raw byte dumps (the layer-4 pair-compare instrument) |
| `src/bin/dump_proxy_graphics.rs` | Proxy-graphics metafile derivation + `--verify` byte-roundtrip proof |
| `IMPLEMENTATION.md` | The single source of truth for the plan |

## Output interpretation

- `missing_in_silver` — gold has a field silver lacks (reader gap or
  projection gap).
- `wrong_value` — both have the field but values differ (check bitcode type
  and version gating against the gold spec).
- `extra_in_silver` — silver emits a field gold doesn't have for this version
  (usually a dump/normalizer version-gating issue).
- `count_mismatch` — gold and silver decoded different numbers of a type
  (coverage gap, e.g. proxy/unknown objects).

Handles are compared by **resolved target type**, not raw id, because handles
are reassigned on rewrite. Records are aligned by `(type, ordinal-within-type)`.

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `GOLD_DWGREAD is not set` | env var missing | re-export per Installation step 2 |
| `dwgread` non-zero exit on a file | gold can't decode it (advanced R2010+ object) | treated as "skip file", not a silver failure |
| harness diff count jumps after an edit | cross-version regression | re-run all 6 versions; the version gating is wrong |
| `cargo test` fails with harness off | unrelated to harness | harness is feature-gated; check the core change |

---

For the design decisions, corpus coverage analysis, the Phase 6 loop
specification, and future work (header comparison, authoring coverage-gap
fixtures), see [`IMPLEMENTATION.md`](./IMPLEMENTATION.md).
