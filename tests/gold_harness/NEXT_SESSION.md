# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target
(2026-09-20, raised) is read AND write **0** on BOTH sides. Current baseline
(2026-09-20 evening halt, HEAD `5a25bf9`): read **53** / write **41**
(124 corpus files; gh44-error.dwg explicitly out of scope via
`run_corpus.in_scope_files`).

The morning session landed batches 7-23, the evening session landed
**batches 24-39**: `82f0225` (the big-family projection wave: FIELD/
FIELDLIST, PLOTSETTINGS, GEODATA, Underlay, MESH, PLANESURFACE reader,
SHAPE/TEXT raw dataflags, OLE2FRAME raw blob, encr_sat_data, entity-common
pair order + SEQEND flag truth), `078c119` (Dynblocks/PolyLine2D wave:
LwPolyline raw flag + vertexids, SPLINE ctrl_pts collapse, BLOCK_HEADER
xref_pname + dupe strip, POLYLINE_2D parent projection, LAYOUTPRINTCONFIG
retype, kid linetype inheritance), `5a25bf9` (SECTION trio retype).
Session total: read 479 → 53, write 455 → 41, **103 of 124 files at
0/0**. All recipes + before→after counts live in §8.1.6 and the commit
messages.

**State check first:** re-read `target/gold_harness_corpus/report.json`
(`read/write_fidelity_by_type_field` + per_file) after every landed batch;
families self-resolve as side effects.

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec` (plus `common_entity_data.spec` and
   `common_entity_handle_data.spec` — the entity-common flag pairs live
   there), verify class-block liveness (§8.1.1) before any retype,
   version-gate every conditional, differ/ignore-list frozen, gates,
   commit conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — §7 (baseline + the refreshed
   Next-packets queue — THIS file's inventory in long form), §8.1.0,
   §8.1.1, §8.1.6 (DONE entries batches 7-39).
3. `target/probes/` — this machine's probe scripts; `pk16a/b/c` census
   key-maps; the `pk17*` probes from the evening session (row dumpers,
   per-file lists, the L1-L16 family probes).
4. The remaining rows live in **21 files**; per-file probing on the
   named carriers is all that remains.

## The route to zero — current inventory (from the fresh post-`5a25bf9` corpus)

### R1. gh109_1.dwg — 16 read / 14 write (the biggest pocket)
- **RAPIDRTRENDERSETTINGS**: count_mismatch + _missing i0-i5 (7 gold
  records — handles 2574-2580, the "低/中/高" render presets — vs
  silver's 1 emitted record), on BOTH pairs. Gold MIS-DECODES the 7
  rapid fields after display_index+has_predefined: its render_target
  849379356 / render_time 1107296256 are **IEEE-754 bit patterns of
  doubles read as BLs** in gold's spec order (dwg2.spec 2659:
  AcDbRenderSettings_fields → rapidrt_version BL, render_target BL,
  render_level BL, render_time BL, lighting_model BL, filter_type BL,
  filter_width BD, filter_height BD, has_predefined B per the
  else-branch). Silver's reader decodes the same wire CLEANLY (its
  values are 0/0/16, correct per the true format). ZERO here requires
  silver to emit gold's garbage — port the gold read order into a
  shadow (keep the clean model), or find why silver emits only 1 of 7
  records first (check silver's ClassObject/RegisteredClass wrappers
  for the 537 class — the 6 missing records may be dropped wrappers
  with the same root as the RAPIDRT count).
- **UNKNOWN_OBJ**: count_mismatch + _missing i1-i6 (gold 7 vs silver 1)
  — likely the SAME 537-class records seen through the other lens, or
  the SectionViewStyle/DetailViewStyle class pair; diagnose after
  RAPIDRT.
- **SORTENTSTABLE.sort_ents/ents** (orig only, 1+1 rows): gold
  num_ents=39 [0,2,919,919]-style sort handles from the swapped stream
  (dwg2.spec 149: `str_dat = hdl_dat; hdl_dat = dat;` then
  HANDLE_VECTOR sort_ents; START_OBJECT_HANDLE_STREAM; block_owner;
  HANDLE_VECTOR_N ents) vs silver's 36 entries whose [3] is
  {entity 0, sort 1027} — both the count and the mid-list pairing
  diverge in `read_sort_entities_table` (the #146-order reader).
- **BLOCK_HEADER.name "**D**" vs silver "**D1**"** — 1 row: the lazy
  strip `^(.*?)\d+$` fixed Dynblocks; this record may need the same
  look (check its siblings list).

### R2. PolyLine2D.dwg — 7 read / 6 write (the chain-ordinal cluster)
- `BLOCK_HEADER.first/last_entity`: gold resolves {4, target 0-null or
  LINE} where silver emits the payload's entity_handles[0]/[-1]
  resolved targets (UNKNOWN_ENT / VERTEX_2D) — an upstream ordinal
  mismatch in the R2000 chain; verify what gold's model-space chain
  really points at (gold's raw BLOCK_HEADER records) and how silver's
  block_records.entity_handles got its order.
- `LINE.handle` {0, LINE} vs {None, VERTEX_2D} and
  `POLYLINE_2D.next_entity` {6, LINE} vs {None, VERTEX_2D}: per-record
  ordinal pairing shifts (gold's record at that ordinal is a LINE,
  silver's is a VERTEX_2D kid or vice versa) — probably fixed by the
  same chain-order root.
- `LAYOUTPRINTCONFIG.ownerhandle`: gold {4, DICTIONARY-owner 856} vs
  silver {BLOCK_HEADER 31} — silver's reader mis-reads the owner slot
  on the CAcLayoutPrintConfig class path (its writer writes the
  correct 856 —_rt passes with the same rows, so it is the READ).
- `VPORT.VIEWMODE` gold 0 vs silver 1: silver's VPORT reader reads
  individual BITS where gold's dwg.spec 3952-3995 block reads
  UCSFOLLOW RS / circle_zoom RS / FASTZOOM RS + the 4BITS VIEWMODE —
  align the read order (the composite VIEWMODE in normalize_silver's
  VPORT branch is built from ucs_* bools; the wire truth is the
  RS-pair sequence).
- `VIEWPORT.vport_entity_header` (rt): gold_rt {5, target 0-null} vs
  silver {None, VX_TABLE_RECORD} — silver resolves a null-target
  handle; emit the null form [5,0,0,0] when the payload handle is 0
  (the WIPEOUT code-tolerance lesson cuts the other way here).

### R3. VERTEX_3D.reactors — 6 read rows (six example files)
Gold binds the assoc-network reactor [1071] to ONE specific vertex
(1054, the THIRD kid, not the first or all six); silver's kid synthesis
binds nothing (a blanket parent-mirror emission was tried and creates
extra rows on the non-bound kids). Not derivable from silver's
payload — either find the network's per-vertex wire reference in
silver's reader or accept as residual.

### R4. Assorted singles (≈14 read / 12 write rows)
- **VIEW.VIEWMODE/has_ds_data/camera_plottable** (LiveSection1 2+2
  orig, 2 rt; example_2000 1+1+1): the composite VIEWMODE comes from
  the wrong bool set (gold's VIEW entity view_mode bits vs silver's
  ucs-derived composition — same root as VPORT.VIEWMODE); has_ds_data
  (gold 1 vs silver 0) — the R2013+ ds-data common bit on the VIEW
  records, silver's common read needs the parity check.
- **ASSOC2DCONSTRAINTGROUP.nodes** (Dynblocks 2+2): gold 129 node
  entries vs silver 113 — a count-source divergence in silver's
  `read_handles` loop for ASSOC2DCONSTRAINTGROUP (associative.rs:1057:
  node_count vs the wire's num_deps/actions region).
- **Helix ×4 versions (2/2 each)**: the ctrl_pts count derivation
  `len(knots) - degree - 1` (the branch comment) no longer matches
  gold's per-record shapes after the SPLINE collapse fix — re-derive
  from gold's raw Helix records per version.
- **Constraints ×5 (1/1 each)**: small per-file rows (pull the
  per-type diff — likely one CONSTRAINT-family field pair).
- **TS1 (3/3)**: ATTRIB.xdicobjhandle (gold {3, 355} on the kid
  ATTRIB — the synthesized insert-kid path drops the xdic handle),
  DIMENSION_ANG2LN.xline2end_pt (a value pair — compare the two
  points), VERTEX_MESH.prev_entity ({8, VERTEX_MESH} chain slot on
  the synthesized mesh kids).
- **Surface rt (0/2)**: ASSOCPLANESURFACEACTIONBODY.assocdep +
  pbsab_status — gold_rt resolves {5, 1291} from silver's rewrite
  while silver_rt synthesizes [0,0]; the batch-23 fabrication emits
  the null form which passes ORIG but not RT. The soap: silver's rt
  re-read loses the payload the orig had; check why the rt-side
  payload's surface_body.dependency differs (probably the writer
  drops the handle somewhere — the orig record's orig-side emission
  passes because the WIRE carried it).
- **ASSOC2DCONSTRAINTGROUP/Dynblocks + example files (1/0 each)**:
  the leftover VERTEX_3D.reactors row on example_2004/2007/2010/2013/
  2018 (see R3).

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
strips embedded quotes AND pipes (regex `\|` alternations die silently:
single search terms through wsl.exe, multi-pattern via the grep *tool*);
this PowerShell has NO `head` and rejects `&&`; put non-trivial shell and
ALL probe python into script files under `target/probes/` — heredocs
through wsl.exe -c break on quoting; write the script with the write tool
and run it. The `read` tool's `offset` is ignored on SOME UNC paths —
use `wsl.exe sed -n <start>,<end>p <file>` for ranges and the grep tool
for multi-pattern
searches. Files: run_roundtrip.py per-file runs; the corpus launch is
nohup run_corpus.py WITH an ABSOLUTE log path + `sleep 8` + pgrep confirm
(models: `target/probes/pk17r_corpus.sh` + `24_wait.sh`). CRITICAL
pathing: the example_*.dwg files live at the test-data ROOT, NOT in the
version folders (`$GOLD_TESTDATA/example_2010.dwg`); PolyLine3D.dwg and
Helix.dwg live IN the version folders. dwgread exit 1 with an empty workdir
usually means a wrong path, not a gold failure.)

## Workflow (per packet)

1. Pick the lever (R1..R4 — gh109_1 is the biggest; re-read the fresh
   report first).
2. Grep the gold spec: dwg.spec + dwg2.spec (+ common_entity_data.spec +
   common_entity_handle_data.spec for entity-common) — read the FULL block
   (macro + version predicate + value guards) before any retype; check §8.1.1
   liveness.
3. Locate the silver side; pull the row VALUES + both records from fresh
   per-file runs (stale-safe; the corpus dirs are stale except for
   still-open families).
4. Minimal, version-gated fix: prefer normalizer projections; codec (reader
   retention) only when the data is not stored. NEVER touch
   `diff_fields.py` / `ignore_fields.toml`.
5. `cargo build --features serde --bins`.
6. Verify per-file on ALL versions the family touches (fresh dirs).
7. **prefers** Run the corpus LAST, detached; one bounded `24_wait.sh`;
   no edits while it runs.
8. Gates: `cargo test --features serde` (47 ok segments; roundtrip 97/0)
   + `cargo test --features gold-harness --test gold_roundtrip` (ok).
   Deep-gate rule: ANY new raw-retention struct field gets a
   normalize_entity_for_comparison arm (the seqend flag pairs, raw
   dataflags byte, OLE raw, LwPolyline raw flag precedents — all have
   arms now; keep the pattern).
9. Commit `fix(harness): <packet> — <gold spec ref> + before→after
   counts`, push; batch-related families may share a wave commit with
   per-family counts in the body (the 82f0225/078c119 precedents).
   No backticks in commit-message bodies (bash command substitution).

## Hard-won lessons (carry all of these forward)

- **dwg2json/dwgread write `<stem>.json` beside the INPUT FILE by
  default** — always redirect or you WRITE INTO THE READ-ONLY GOLD TREE.
- **Write rows = rt-parser-parity pair (gold_rt vs silver_rt); read rows
  = orig pair; a family can be one-sided** — the rt pair often passes
  while the orig pair fails and vice versa (e.g. the SEQEND flags).
- **By-type tables are truncation-prone; per_file (FULL paths) is truth.
  103/124 files are at 0/0 — only 21 files carry rows.**
- **The entity-common flag pair order is [ltype BB, plotstyle BB,
  R2007: material BB + shadow RC]** — the reader was fixed accordingly
  (pair labels mis-assign INSIDE an isochronous window without desync).
- **RAW beats recomposition**: the wire's raw values (dataflags byte,
  LwPolyline flag, SEQEND per-record common flags, encr SAT blocks,
  OLE blob) must be RETAINED — gold prints them verbatim, and any
  value-based recomposition will differ (explicit width 1.0 keeps bit
  4 clear; LibreDWG-authored seqends carry 3/null, DWG-native carry 0).
- **Branch placement in the entity loop matters**: pop-branches must sit
  BEFORE the generic field loop (~line 3670); the anchor
  `if gold_type == "POLYLINE_3D":` matches MULTIPLE sites — a branch
  edit landed once in the kid area (after the loop) and leaked keys.
  Check the line number whenever an if doesn't seem to fire.
- **A pop in a branch kills the payload key for later readers** — stash
  the value in a local first (`_p3d_flags`/`_p2d_flags` precedents).
- **normalize_gold reinterprets a 4-int list as the raw handle tuple
  [code, size, value, absref]** — mirror that exact shape when gold
  prints short int vectors ([21,22,23,24] vertex ids).
- **The `[0]*n` collapse family**: normalize_gold turns any dict
  without `index`+`rgb` into 0 — childval entries, MESH edge structs,
  SPLINE ctrl pts, SECTION_SETTINGS types all print as bare 0-vectors.
- **FIELD_NAME_MAP re-merges payload keys AFTER per-type branches** —
  a name-emission a branch decodes (MTEXT "text") gets OVERWRITTEN
  unless the branch pops the source key (`value`).
- **per-SEQEND wire flags must be stashed pre-generic-loop** (the
  `_seq_pf_stash`/`_seq_sf_stash` pattern at merge time) or they leak
  as extra rows from every polyline family.
- **Fabricated constant handle codes are time bombs** (WIPEOUT lesson);
  normalize_handle_value(0) {code: None} resolves as a null pair and
  passes; the diff tolerates missing codes when targets match.
- **Typing divergence poisons handle-vector resolution far away**;
  **gold-bug parity IS the truth** (RAPIDRT garbage is IEEE patterns —
  the spec block beats intent).
- **Entity-common serde-skipped fields ride `_common_dwg` into
  merge_common — pop from `fields` AFTER the merge** (graphic_data
  precedent).
- **Bitflags serde joins with " | " (split it); FIELD_CAST BS→BL
  zero-extends; MATERIAL rgb unsigned; wire codes SOLID 31 vs TRACE
  32; GROUP wire names live in silver's `description`.**
- **Silver object payloads nest common under `common` inconsistently** —
  location-aware extraction or records silently vanish.
- **Never edit mid-corpus; never busy-poll; never trust pooled corpus
  dirs except the named stale-safe carriers; git-commit each wave so a
  regression is one revert away.**

## The commit / push convention

- Branch `gold-vs-silver`, push to `origin/gold-vs-silver` after each
  batch. `fix(harness): <packet> — <gold spec ref> + before→after counts`
  (per-wave when families share the mechanism, e.g. `078c119`), then a
  separate `docs(harness): …` commit once §7/§8.1.6 are updated.
- Landed this session (2026-09-20): `82f0225` (batches 24-32),
  `078c119` (33-38), `5a25bf9` (39, SECTION trio). Next HEAD: the
  docs commit carrying this file.
