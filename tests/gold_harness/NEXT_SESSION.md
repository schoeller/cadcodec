# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Delete this file when the packets it names complete (fold the outcomes into
> IMPLEMENTATION.md §7 + §8.1.6).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target is
read AND write below **1 000** on BOTH sides (interim milestone: below
**2 000** — you should reach and pass it this session). Current baseline
(2026-09-20): read **3 425** / write **3 292**, and the two sides now
**MIRROR family-for-family** — every family you fix pays double (its rows die
on both totals). Work the packet queue below in order; iterate
diagnose → fix → verify → gates → commit → docs until you halt.

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec`, **verify class-block liveness
   (preprocessor frames) before any retype** (§8.1.1), version-gate every
   conditional, the differ/ignore-list are frozen, regression gates, commit
   conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — the living plan. Read §7 (entry
   point; the current baseline block ends with the "**Next packets (2026-09-20
   halt…)**" list — that IS the handoff), §8.1.0 (environment verification),
   §8.1.1 (liveness rule + frame map), §8.1.6 (queue; the newest DONE entries
   carry per-packet recipes), §8.1.6a (coverage audit).

## Current state (2026-09-20, session handoff)

- Baseline: read-fidelity **3 425**, write-fidelity **3 292** (124 corpus
  files; gh44-error.dwg explicitly out of scope via
  `run_corpus.in_scope_files`). `cargo test --features serde` = 1556/0;
  `gold_roundtrip` = ok. All work pushed on `gold-vs-silver` (HEAD ~`9c2594a`).
- Last sessions landed: R2013+ AcDs 3DSOLID-family writer payload,
  is_xref_ref/phantom-DIMSTYLE, 3DSOLID prologue projection, MTEXT R2018
  redundant extents, DIMENSION block handle, **pre-R2013 classes-verbatim
  roundtrip** (same-version rewrites must keep doc.classes verbatim — the
  old legacy path renumbered class tables and re-typed every pruned-class
  record to ACDBDICTIONARYWDFLT), UNKNOWN_OBJ/UNKNOWN_ENT unmodeled-class
  projections.

## Packet queue (in this order)

1. **U2 — dynamic-block-class retype map** (~380/side, largest family):
   silver's `DynamicBlock` wrapper bucket swallows records gold types BY LIVE
   CLASS NAME. Dynblocks census (pooled: `target/gold_harness_corpus/Dynblocks/`):
   gold has BLOCKGRIPLOCATIONCOMPONENT 34 / BLOCKSTRETCHACTION 9 /
   BLOCKREPRESENTATION 7 / DYNAMICBLOCKPURGEPREVENTER 6 / the BLOCK*GRIP,
   *PARAMETER, *ACTION classes ≈ 92 records vs silver's 92 UNKNOWN_OBJ (gold
   has only 1 true UNKNOWN_OBJ there); ATMOS carries 112 the same way.
   Fix: in `normalize_silver.py`'s object loop (the DynamicBlock retype site
   where `ACSH_HISTORY_CLASS` and `EVALUATION_GRAPH` already work), retype by
   `payload["dxf_name"]` → the gold class block name — **after checking each
   class block is live in dwg2.spec** (they are plain `DWG_OBJECT(BLOCK…)`
   blocks; PROXY_OBJECT lives at dwg.spec 5752). Then land per-class field
   projections from silver's `data.<Kind>` payloads (gold's flattened shapes
   are in the gold-orig `.norm.json` records; the ACSH_HISTORY_CLASS +
   viewstyle projections are the precedents).
2. **unknown_bits floor** (~260/side in the tops alone: TABLESTYLE 121,
   DIMASSOC 62, EVALUATION_GRAPH 56, ASSOCDEPENDENCY 36, ASSOCVARIABLE 22):
   needs a new raw-remainder side-channel in silver's reader (keep the
   undecoded bit ranges verbatim per record, like the `xdic_by_handle`
   precedent) so the normalizer can emit gold's `unknown_bits` hex.
3. **Small mixed families** (~150/side total): VIEWPORT.named_ucs 29,
   ATTDEF.style 26 / TEXT.style 21 (style-handle resolution),
   UNKNOWN_OBJ.ownerhandle 28-44 (wrapper owner codes), ATTRIB._missing 18,
   MTEXT column shapes ~5, BLOCK_HEADER.name 3, PROXY_OBJECT._missing 30.

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
commands through `wsl.exe -d Ubuntu-24.04 -- bash <script>` — wsl.exe strips
embedded quotes/pipes, so put non-trivial shell and ALL probe python into
script files under `target/probes/` and execute those.)

## Workflow (per packet)

1. Pick the packet from the queue above (order matters: U2 first — its rows
   are the biggest single lever).
2. Grep the gold spec: BOTH `dwg.spec` and `dwg2.spec`; check the enclosing
   preprocessor frame for liveness (§8.1.1) BEFORE any retype; read the full
   spec block (macro + version predicate + value guards).
3. Locate the silver side: reader
   (`src/io/dwg/dwg_stream_readers/object_reader/{entities,objects}.rs`),
   writer (`src/io/dwg/dwg_stream_writers/object_writer/*.rs`),
   struct (`src/entities|objects|tables/<type>.rs`), builder
   (`src/io/dwg/dwg_document_builder.rs`). Confirm silver stores the data in
   the dump (check a per-version `<stem>_silver_orig.json` — run
   `run_roundtrip.py` into a FRESH dir; NEVER trust pooled
   `target/gold_harness_corpus/<stem>/` artifacts for field shapes — they are
   stale last-wins on stem collisions, use them only for ranking).
4. Minimal, version-gated fix in `normalize_silver.py`/`normalize_gold.py`
   (projection) or the codec (only when the data is not stored). NEVER touch
   `diff_fields.py` / `ignore_fields.toml`.
5. `cargo build --features serde --bins`.
6. Verify per-file on all versions the family touches via `run_roundtrip.py`
   into fresh `target/probe_wip/<v>` dirs; then `run_corpus.py` for totals.
7. Gates: `cargo test --features serde` (1556/0) and
   `cargo test --features gold-harness --test gold_roundtrip` (ok).
8. Commit: `fix(harness): <packet> — <gold spec ref> + before→after counts`,
   push, update §7 baseline + §8.1.6 queue.

## Hard-won lessons (do not repeat)

- **Retype by dxf_name ONLY for LIVE class blocks** — check the
  preprocessor frame first. And: the UNKNOWN-family payload-clear in
  normalize_silver must run LAST (after every payload-keyed retype branch —
  viewstyles/assoc read `payload["data"]`/`["dxf_name"]`); a first-pass clear
  destroyed the SECTIONVIEWSTYLE/DETAILVIEWSTYLE projections and cost +639
  rows (`0be4d76` has the full story).
- **Same-version DWG roundtrips keep `document.classes` verbatim** — the
  writer already gates the legacy prune on `dwg_source_version != target`;
  do not reintroduce class-table renumbering for pre-R2013 files.
- **Entity-common storage fields the crate serde-skips ride in the dump's
  `_common_dwg` map** (keyed by hex handle) and enter records via
  `merge_common` — payload pop lists cannot see them (the UNKNOWN_ENT
  graphic_data incident). `ignore_fields.toml` ignores
  `raw_dwg_data`/`raw_dwg_handle_bits` globally, so raw fields are
  diff-neutral.
- **Gold's 3DSOLID-family spec reads a phantom leading `acis_empty` bit on
  R2013+ AcDs-backed records** and derails — silver's reader is bit-true
  there (verified against raw wire via `dump_section_bytes`); the divergent
  fields are dropped symmetrically in both normalizers. The same
  irreducible-garbage pattern justified the UNKNOWN-record projections:
  gold's `unknown_bits` hex cannot be derived from silver's typed payloads.
- **normalize_gold must be fed defensively**: it already byte-scans/re-escapes
  gold's raw-SAB `acis_data` first element, loads with `strict=False`,
  and shims `-nan` → NaN. gh44-error.dwg stays explicitly excluded from the
  corpus scope (the shim would otherwise re-include it).
- **DWG record frame for raw dumps**: MS size + UMC handlestream-size (R2010+,
  not counted in size) sit in the 3 bytes BEFORE the trace "Address"; gold's
  `@byte.bit` positions are relative to the BOT start. Bit codes
  (`bits.c`): BS `'00'→RS16 '01'→RC8 '10'→0 '11'→256`; BL
  `'00'→RL32 '01'→RC8 '10'→0 '11'→ERR`; BD `'00'→raw f64 '01'→1.0
  '10'→0.0 '11'→NaN`; RS/RL/RD are little-endian per bytes. Use
  `cargo run --bin dump_section_bytes -- <dwg> <addr> <size>` for hex+bits.
- **The differ compares the RESOLVED handle-target TYPE NAME** (identity =
  `(code, resolved_target)`), so record RETYPES shift resolved-target names
  everywhere — a renames ripple can add rows on other records' handle fields
  (the DICTIONARY.ownerhandle lesson); always re-run the corpus after
  type-map changes.
- **CMC color method byte, dataflags/num_* absence-bitmasks, REPEAT/REPEAT_CN
  degenerate `[0]*n` JSON, LineWeight `{"Value": mm*100}`, side channels
  (`xdic_by_handle`/`reactors_by_handle`/`dwg_data_store_handles`), stem
  collisions, value-dependent version gating** — all still apply; the queue's
  DONE entries carry their details.

## The commit / push convention

- Branch: `gold-vs-silver` (tracks `origin/gold-vs-silver`).
- Commit: `fix(harness): <packet> — <gold spec ref> + before→after counts`.
- Push after each packet: `git push`.
- After each packet: update IMPLEMENTATION.md §7 baseline (read/write totals
  + the "Next packets" list) — the totals in THIS brief go stale by design;
  §7 is authoritative.
