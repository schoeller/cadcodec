# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target
(2026-09-20, raised) is read AND write **0** on BOTH sides — land every
remaining family, including the heavy pockets; do not stop at an interim
milestone. Current baseline (2026-09-20,
after fix commit `b2955a7` + its docs commit): read **479** / write **455**
(124 corpus files; gh44-error.dwg explicitly out of scope via
`run_corpus.in_scope_files`; gh109_1/gh209_1 ARE in scope). The two sides
MIRROR family-for-family — every wire-family you fix pays double. The
remaining mass is pockets of undecoded/unmodeled records, gold-bug-parity
reads, and field-level residue; the queue below carries per-packet recipes
from the session that re-anchored it.

**Staleness rule:** always re-read the by-type table from the FRESH
`target/gold_harness_corpus/report.json` before starting a packet (families
self-resolve as side effects; queue numbers go stale).

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec`, verify class-block liveness
   (preprocessor frames, §8.1.1) before any retype, version-gate every
   conditional, differ/ignore-list frozen, regression gates, commit
   conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — §7 (the baseline block + the
   "Next packets" list IS the authoritative handoff), §8.1.0, §8.1.1,
   §8.1.6 (DONE entries carry per-packet recipes; batches seven through
   twenty-three landed 2026-09-20).
3. `target/probes/fullsrc/` — the LibreDWG source parse + verbatim spec
   windows; `target/probes/pk1*.py`-style probes from prior sessions hold
   row forensics (row extraction, class-name mapping, per-carrier drops).

## Current state (2026-09-20, session handoff)

- HEAD is past fix `b2955a7` on `gold-vs-silver`, pushed; the docs commit
  that carries this file follows it. `cargo test --features serde` = all
  segments ok (roundtrip suite 97/0); `gold_roundtrip` = ok. Working tree
  clean apart from untracked `examples/cylinder_dwg.rs` (predates the
  campaign — leave it uncommitted).
- Fresh corpus (post-`b2955a7`): read **479** / write **455**. Top rows:
  UNKNOWN_OBJ._missing 8, RAPIDRTRENDERSETTINGS._missing 6,
  LWPOLYLINE.flag 6, LWPOLYLINE.vertexids 6, UNKNOWN_ENT._missing 6,
  SPLINE.ctrl_pts 6, POLYLINE_3D.flag 6, plus the spread residue.
- Landed since the last cold start, all committed+pushed with docs:
  `45382ec` MULTILEADER attach trio (−12/−12), `b123b4c` TABLECONTENT
  dropped records (−12/−12), `fca5367` VERTEX_MESH (−12/−12), `fad3042`
  ACSH_CONE_CLASS retype (−4/−4), `543f877` WIPEOUT/IMAGE reactor codes
  (−12 write), `689b14d` SEQEND real handles (−18 write), `263ab5f`
  VIEWPORT.status_flag raw (−17 read), `9f06d89` LEADEROBJECTCONTEXTDATA
  retype (−24/−24), `a7e451b` TOLERANCE names (−63/−63), `257895a`
  smalls batch (−17/−62), `91e72a3` TRACE/SOLID split (−53/−53),
  `e90fb77` graphic_data pops (−5/−5), `ab0e02f` SORTENTSTABLE.ents
  (−4/−5), `b2955a7` SURFACE retypes + PLANESURFACE (−17/−18).

## Packet queue (from the 479/455 report; recipes sharpened)

1. **RAPIDRTRENDERSETTINGS._missing 6 (gh109_1, both sides)**: silver
   PARSES all six records structurally (ClassObject.data.RapidRtRenderSettings,
   payloads in the gh109_1 silver dump) and reads them CLEAN
   (version 3, render_target 0, render_level 1, ...), while GOLD's own
   decode is misaligned garbage (render_target 849379356, filter_width
   -6.1e+201, ...) for everything past the AcDbRenderSettings base
   (name/description/fog parse fine on both sides). The class_object.rs
   "RAPIDRTRENDERSETTINGS" arm also reads has_predefined unconditionally
   while gold's spec gates it VERSION (R_2013) {}. Zeroing these rows
   needs a gold-bug-compatible parse: diff gold's
   AcDbRenderSettings_fields read against silver's read_render_settings
   (field counts/gates per era), land whatever makes silver consume the
   bits exactly like gold (the garbage parity IS the campaign's truth
   definition — gold is the oracle), then add the ClassObject kind→
   RAPIDRTRENDERSETTINGS retype + field projection (base + the seven
   rapid fields + has_predefined per the gold spec's R2013 gate).
2. **LiveSection1 SECTION trio (2018, both sides)**: gold emits
   SECTIONOBJECT (ENTITY — heavy: full AcDbSection wire + a 188-byte
   preview blob; silver's record is its UNKNOWN_ENT passthrough),
   SECTION_MANAGER (trivial: is_live + sections handle vector — silver
   parses it under ClassObject data.SectionManager) and SECTION_SETTINGS
   (large settings REPEAT + a 2320-bit handle-stream remainder gold
   dumps via HANDLE_UNKNOWN_BITS; already in _UNKNOWN_BITS_TYPES;
   silver parses it under data.SectionSettings). Per-pocket: the MANAGER
   retype is trivial (kind map + 2-field projection); SETTINGS is medium
   (settings REPEAT projection); the OBJECT is heavy (needs the entity
   modeled or a full UNKNOWN-with-fields projection).
3. **Surface PLANESURFACE residue (3 wrong_value rows, both sides)**: the
   single @1290 record still carries acis_data (SAB boundary — compare
   silver's emitted [head, hex-rest] with gold's element-by-element),
   modeler_format_version 6-vs-1 and v_isolines 8-vs-6 (silver's Plane
   reader misparses two wire fields upstream of the projection — find
   the divergent reads in silver's surface reader vs the gold spec).
4. **gh109_1 SORTENTSTABLE null entries (orig pair, ~2 rows)**: gold's
   sort vectors KEEP the zero pairs (~3 indices in the 1045 table);
   silver's sort-table reader drops most of them, shifting every
   ordinal. Reader fix: retain null (0,0) pairs in the entries list;
   the normalizer emission then flows (it emits zero handles fine).
5. **UNKNOWN_OBJ._missing 8 + UNKNOWN_ENT._missing 6 census**: re-census
   the fresh report per-file (stem pools are fresh for single-version
   stems; example_* are collision-free; compare by FULL path). The old
   pockets partially landed (Cone/TABLECONTENT/Surface); what remains
   are per-file dropped records — diagnose carriers first.
6. **Small residue families (6-each in the by-type tables)**:
   LWPOLYLINE.flag + .vertexids (silver's branch constructs the flag
   from is_closed/plinegen — verify the bit layout per era;
   vertexids is a degenerate-REPEAT candidate), SPLINE.ctrl_pts (6,
   point-list projection detail), POLYLINE_3D.flag (6,
   bitfield-keyed), 3DSOLID.encr_sat_data (Cone's residue: gold's SAT
   text uses 0A newlines where silver_rt writes 0D0A — writer newline
   conversion), TS1 residue ~80 rows (re-census; the SOLID _count x2
   SOLID/TRACE ord-shifts died with `91e72a3`).
7. **Residue** — everything below the top-N tables: use the per_file
   report (compare by FULL path) and fresh per-file probes.

The totals in THIS brief go stale by design — §7 + the latest
report.json are authoritative.

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
strips embedded quotes AND pipes (search patterns with `\|` die silently:
single search terms through wsl.exe, multi-pattern via the grep *tool*;
`2>/dev/null` in the PowerShell line leaks — never pass it); this
PowerShell has NO `head` alias and rejects `&&`; put non-trivial shell and
ALL probe python into script files under `target/probes/` and execute
those. The `read` tool's `offset` is ignored on SOME UNC paths. To launch
the corpus detached: a script that nohups run_corpus.py with an ABSOLUTE
log path and sleeps ~8s before exiting works; a bare launch died once.
NEVER start edits before the detached corpus is confirmed via pgrep.)

## Workflow (per packet)

1. Pick the packet from the queue above (in order).
2. Grep the gold spec: BOTH `dwg.spec` and `dwg2.spec`; check the
   enclosing preprocessor frame for liveness (§8.1.1) BEFORE any retype;
   read the full spec block (macro + version predicate + value guards).
3. Locate the silver side; confirm silver stores the data (fresh
   `run_roundtrip.py` into a FRESH dir; NEVER trust pooled corpus dirs
   for field shapes — stale last-wins on stem collisions. Single-version
   stems + example_/sample_ are fresh in the pool).
4. Minimal, version-gated fix in `normalize_silver.py`/`normalize_gold.py`
   (projection) or the codec (only when the data is not stored). NEVER
   touch `diff_fields.py` / `ignore_fields.toml`.
5. `cargo build --features serde --bins`.
6. Verify per-file on all versions the family touches via fresh dirs.
7. **Run the corpus LAST**, launched detached; wait with the bounded
   `target/probes/24_wait.sh` (ONE blocking call; do NOT busy-poll; do
   NOT edit anything mid-corpus).
8. Gates: `cargo test --features serde` (count the `test result: ok`
   segments, not just the tail) and `cargo test --features gold-harness
   --test gold_roundtrip` (ok). The deep gate catches raw-vs-typed
   default splits: extend tests/roundtrip.rs's
   normalize_entity_for_comparison when adding a raw-retention field
   (the seqend_handle/dwg_status_flag precedents).
9. Commit: `fix(harness): <packet> — <gold spec ref> + before→after
   counts`, push, update §7 baseline + §8.1.6 queue (a DONE entry with
   the recipe), docs commit, push. NEVER put backticks in commit-message
   bodies written from bash `-m` strings (one got command-substituted).

## Hard-won lessons (do not repeat)

- **dwg2json/dwgread write `<stem>.json` next to the INPUT FILE by
  default** — always redirect explicitly or you WRITE INTO THE
  READ-ONLY GOLD TREE (a stray Cone.json from a prior session was
  removed during the 2026-09-20 batch-16 verification).
- **Write-fidelity rows come from the rt-parser-parity pair**
  (gold_rt vs silver_rt); read rows from the orig pair; a family can be
  one-sided (status_flag read-only, WIPEOUT write-only).
- **By-type tables are top-N TRUNCATED and stem-inflated** — per_file
  (FULL paths) and fresh probes are truth (MULTILEADER ranked 18, true
  drop −12; TOLERANCE ranked ~10, true drop −63).
- **Re-read the fresh by-type table before each packet** — families
  self-resolve (UNKNOWN_OBJ.ownerhandle 37 died with the MULTILEADER
  reader fix; the TS1 corner rows died with the TRACE typing).
- **A reader that eats more bits than its record carries desyncs
  everything downstream in the file** — treat mystery count/missing
  records in the same file as potential fallout; fix upstream first.
- **Raw-retention struct fields must mirror the typed enum defaults at
  construction** (dwg_attach_*, status_flag, seqend_handle); the deep
  roundtrip gate catches splits — normalize_entity_for_comparison
  extension is part of the pattern.
- **Retype by dxf_name/kind ONLY for LIVE blocks** (§8.1.1 —
  EXTRUDED/LOFTED/REVOLVED/SWEPT SURFACEs, TABLE/TABLECONTENT,
  ASSOCSWEPTSURFACEACTIONBODY are dead; Plane PLANESURFACE and
  TABLESTYLE/TABLEGEOMETRY are live). A retype must come WITH its field
  projection or it explodes rows; a silver struct name in a
  GOLD-name-keyed tuple is silently dead (POLYGON_MESH).
- **Fabricated constant handle codes are time bombs** — the WIPEOUT
  {code:3} stamp masked the writer nibble bug on ORIG and exploded on
  RT. The differ tolerates absent codes (code=None) when targets
  resolve; use normalize_handle_value(0), never a constant.
- **Typing divergence poisons handle-vector resolution** — the SURFACE
  mis-typing created wrong_value rows in SORTENTSTABLE/dep_on far from
  the records themselves.
- **Gold-bug parity IS the truth definition** — when gold mis-parses a
  block (RAPIDRTRENDERSETTINGS' garbage), silver must reproduce gold's
  parse, not AutoCAD's intent; diagnose by diffing the two readers.
- **unknown_bits tail byte is LSB-packed**; raw PROXY/remainder windows
  ride the reader side channels (`unknown_bits_by_handle`,
  `capture_proxy_window`); _UNKNOWN_BITS_TYPES gates the emission.
- **Entity-common serde-skipped fields ride `_common_dwg` into
  merge_common** — per-payload pops cannot see them; pop from `fields`
  AFTER the merge (the MESH/underlay/PLANESURFACE graphic_data block).
- **The `[0]*n` degenerate REPEAT pattern** — gold collapses one value
  per record to a bare 0 (PLANESURFACE wires: 12 wires → [0]*12).
- **Aggregate pipe-fragility**: joined bitflags serde strings need
  " | " splitting (MLINE); bitcode sign conventions differ per macro
  (FIELD_CAST BS→BL zero-extends: 0xFFCE=65486; MATERIAL rgb unsigned).
- **Wire-name constants**: GROUP's name T carries REAL names sometimes
  ("Superhatch" — silver stores the wire name under the misnomered
  `description` key); wire type codes split SOLID 31 vs TRACE 32.
- **Never edit mid-corpus; never busy-poll; never trust pooled dirs.**

## The commit / push convention

- Branch `gold-vs-silver`, tracks `origin/gold-vs-silver`.
- `fix(harness): <packet> — <gold spec ref> + before→after counts`, then a
  separate `docs(harness): …` commit once §7/§8.1.6 are updated; push
  after each. Batches landed 2026-09-20: 7–23 (see the Current state
  list for hashes), each followed by a docs commit; the one carrying
  this file follows `b2955a7`.
