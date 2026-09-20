# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target
(2026-09-20, raised) is read AND write **0** on BOTH sides — land every
remaining family. Current baseline (2026-09-20 night halt, HEAD `c20e6fe`):
**read 38 / write 30 — 116 of the 124 corpus files are already at 0/0.**
gh44-error.dwg stays explicitly out of scope via `run_corpus.in_scope_files`.

The remaining 68 rows live in **NINE files** and every row's exact gold/silver
values are already dumped to `target/probes/pk18_residues_full.txt` (regenerate
any time: `python3 target/probes/pk18a_all_rows.py`). The bulk is one file
(gh109_1: 16/14) whose two pockets share one likely root; the rest are small,
diagnosed clusters.

**Session history (2026-09-20):** morning batches 7-23 (`fa2cb0a..b2955a7`);
evening batches 24-32 (`82f0225`, the big-family projection wave), 33-38
(`078c119`, Dynblocks/PolyLine2D wave), 39 (`5a25bf9`, SECTION trio), 40
(`c20e6fe`, constraint-group flat nodes + Helix era gates). Session total:
read 479 → 38, write 455 → 30. Recipes + before→after counts: §8.1.6 and the
commit messages of `fa2cb0a..c20e6fe`.

**Staleness rule:** re-read `target/gold_harness_corpus/report.json`
(`read_fidelity_by_type_field`, `write_fidelity_by_type_field`, `per_file`)
after every landed batch — families self-resolve as side effects.

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec` **plus `common_entity_data.spec` and
   `common_entity_handle_data.spec`** (the entity-common flag pairs), and
   `spec.h` (the LWPOLYLINE flag bit names); verify class-block liveness
   (§8.1.1) before any retype; version-gate every conditional;
   differ/ignore-list frozen; commit conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — §7 (baseline chain + the
   Next-packets queue = this inventory in long form), §8.1.0, §8.1.1,
   §8.1.6 (DONE entries batches 7-40).
3. `target/probes/` — the probe library: `pk16a/b/c` (census/key-maps),
   `pk17*` (the evening session's family probes), `pk18a_all_rows.py` (the
   full residue dump) — all rerunnable.
4. `target/probes/pk18_residues_full.txt` — every remaining row, full values.

## The route to zero — complete inventory (fresh post-`c20e6fe` numbers)

### R1. gh109_1.dwg — 16 read / 14 write  (the LAST big pocket; single root suspected)

**(a) RAPIDRTRENDERSETTINGS — count_mismatch + _missing i0-i5 (7/7 rows, both

pairs).** Gold has 7 records (handles 2574-2580 — the "低/中/高" render
presets, class 537/AcDbRapidRTRenderSettings) where silver emits 1.
Gold's records decode the RenderSettings base fields CLEANLY (name
"低", description, display_index, fog/backfaces/environ bits,
has_predefined) and then MIS-DECODE the 7 rapid fields:
`render_target` 849379356 (0x32A4…) and `render_time` 1107296256
(0x42046000 — an IEEE-754 double's bit pattern!) and
`filter_width` -6.145506773533412e+201 — the wire does not match
gold's field order (dwg2.spec 2659 + AcDbRenderSettings_fields 2585:
after display_index comes has_predefined B [R2013] then
rapidrt_version BL / render_target BL / render_level BL /
render_time BL / lighting_model BL / filter_type BL / filter_width
BD / filter_height BD). Silver's reader decodes the same wire
CLEANLY (per the true third-party format).

Zero requires silver to emit gold's garbage values. Steps:
1. First find why silver emits only 1 of the 7 records — inspect
   silver's class-537 dispatch path (dwg_document_builder.rs, the
   CAcLayoutPrintConfig neighborhood ~4845; check the
   ClassObject/RegisteredClassObject wrapper arms ~5680/5820) — the
   same dropped-wrapper root likely explains the UNKNOWN_OBJ pocket
   below.
2. Port gold's read order as a per-record SHADOW beside the clean
   parse (the model keeps the clean values; a gold-parity mirror of
   the misplaced reads reproduces 849379356 etc.), or derive gold's
   per-record offsets from the wire and re-project in the normalizer.
3. Emit the records typed RAPIDRTRENDERSETTINGS with gold's
   field-for-field values (name/description/display_index/has_predef
   clean + the garbage rapid seven).
Note: gold's `class_version` prints through
`VALUE_BL (class_version + 1, 90)` (display +1) — check what the
JSON actually emits per record before emitting.

**(b) UNKNOWN_OBJ — count_mismatch + _missing i1-i6 (7 read/7 write rows).**
Gold has 7 UNKNOWN_OBJ records vs silver's 1. Diagnose AFTER (a):
if the missing silver records are the 537-class wrappers, the
UNKNOWN_OBJ counts re-balance at the same time. The 426/428
SectionViewStyle/DetailViewStyle stay UNKNOWN_OBJ on silver's side
per the liveness map (that is CORRECT — do not retype them).

**(c) SORTENTSTABLE.sort_ents + .ents — 1+1 rows, orig only.**
Gold's record (handle 1045): num_ents **39**, sort handles read from
the SWAPPED stream (dwg2.spec 149: `str_dat = hdl_dat; hdl_dat =
dat;` → HANDLE_VECTOR(sort_ents) → START_OBJECT_HANDLE_STREAM →
block_owner → HANDLE_VECTOR_N(ents)); the raw sort_ents begin
[1194, 1292, 825, **919**, 879, ...] and the corresponding ents have
dead references (index 3: gold sort [0,2,919,919], ent code 4
target 0). Silver reads **36** entries whose [3] is
{entity_handle: 0, sort_handle: 1027} — off by 3 entries and
mid-list mispairing. The reader is
`read_sort_entities_table` (objects.rs:1369 — the #146 stream-order
design). Compare bit-for-bit where silver's `read_main_handle()`
sequence diverges from the gold swap-order; retain the 3 dead
entries.

### R2. PolyLine2D.dwg — 7 read / 6 write (the chain-ordinal cluster)

All R2000-era chain/ordinal issues on one small file:
- `BLOCK_HEADER.first_entity` + `last_entity` (2 rows): gold resolves
  {code 4, target 0-null} where silver emits its block_records'
  entity_handles[0]/[-1] resolved to LAYOUTPRINTCONFIG — gold's
  model-space chain genuinely starts/ends NULL; check what gold's raw
  BLOCK_HEADER records really carry and how silver's
  block_records.entity_handles list gets its head/tail.
- `last_entity` row 2: gold {4, LINE} vs silver {VERTEX_2D} — an
  upstream ordinal shift in the entity chain (the same root as
  LINE.handle + POLYLINE_2D.next_entity below).
- `LINE.handle`: gold {0, LINE} vs silver {None, VERTEX_2D} — per-type
  ordinal pairing shifted: at the LINE ordinal silver's record is a
  synthesized VERTEX_2D kid. Likely fixed by re-ordering silver's
  emitted records (the kid synthesis placement) or re-checking the
  chain slots.
- `POLYLINE_2D.next_entity`: gold {6, LINE} (code-6 relative = +4) vs
  silver {None, VERTEX_2D} — the R2000 parent's next-entity slot:
  gold reads the post-seqend LINE; silver's payload reads the first
  kid. Inspect where the parent's next-entity handle comes from in
  silver's common (the prev/next chain slot read on the merged
  reader).
- `LAYOUTPRINTCONFIG.ownerhandle`: gold {4, DICTIONARY 856} vs silver
  {BLOCK_HEADER 31} — silver's CAcLayoutPrintConfig class path
  (dwg_document_builder.rs:4851) mis-reads the owner slot; note the
  WRITER writes the correct 856 (rt pair differs only via the read).
- `VPORT.VIEWMODE`: gold 0 vs silver 1 — silver's VPORT reader
  (tables.rs:950+) reads individual BITS where gold's dwg.spec
  3952-3995 reads UCSFOLLOW RS/circle_zoom RS/FASTZOOM RS + the 4BITS
  VIEWMODE; align the read order (the compose in normalize_silver's
  VPORT branch at ~6078 builds from ucs bools — wrong source bits).
- rt only: `VIEWPORT.vport_entity_header` gold_rt {5, target 0-null}
  vs silver {VX_TABLE_RECORD} — silver resolves a null-target handle;
  emit the null form (normalize_handle_value(0)) when the payload
  handle is 0.

### R3. TS1.dwg — 3/3

- `ATTRIB.xdicobjhandle` (missing_in_silver): gold {3, 355} on a
  synthesized insert-kid ATTRIB — the kid path in
  normalize_silver.py (~line 1560s) drops the xdic slot; thread the
  payload's xdictionary_handle through the kid rec like ownerhandle.
- `DIMENSION_ANG2LN.xline2end_pt`: gold [28.38942, 46.63480, 0.0] vs
  silver [24.13153, 44.46327, 0.0] — a genuine value pair; compare
  the raw payloads (gold's orig-record def-points vs silver's
  dropdown — probably a swapped xline1/xline2 endpoint pair or an
  era-gated read of the second xline point).
- `VERTEX_MESH.prev_entity`: gold {code 8→4-rt, VERTEX_MESH} — the
  synthesized VERTEX_MESH kids need the prev chain slot (the
  kid-synthesis block builds rec["prev_entity"]=null today; the
  parent's own prev/next + the kid sequence should thread the real
  mesh-kid chain).

### R4. LiveSection1.dwg — 4/2

- `VIEW.VIEWMODE` gold 1 vs silver 0 (2 rows orig, 2 rt): for the
  VIEW ENTITY, gold's view_mode bits (dwg2.spec VIEW block —
  perspective active bit?) vs silver's composite built from
  ucs_per_viewport/ucs_at_origin/ucsfollow (~line 6178) — the pair
  composition is from the wrong bool set for the entity variant.
- `VIEW.has_ds_data` gold 1 vs silver 0 (2 rows orig only): the
  R2013+ ds-data presence bit on gold's VIEW records; silver's common
  read needs the parity flag (its own common machinery has the bit?
  check merge_common's has_ds_data handling vs the wire).

### R5. example_2000.dwg — 3/3, and example_2004/2007/2010/2013/2018 — 1/0 each

- `VERTEX_3D.reactors`: gold binds [assoc-net 1071] to ONE specific
  kid (handle 1054 — the THIRD vertex on example_2000) where silver's
  kid synthesis binds nothing. A blanket parent-mirror was TRIED and
  creates extra rows on the five non-bound kids — the binding is NOT
  derivable from silver's payload. Either: find the network wire's
  per-vertex reference in silver's reader (the ASSOCNETWORK/
  constraint dependency data) and thread it to the kid, or accept as
  residual and document.
- `VIEW.VIEWMODE` + `VIEW.camera_plottable` (example_2000 only, 2
  rows): same VIEW root as R4; camera_plottable extra_in_silver
  (gold omits the field) — pop it in the VIEW branch.

### R6. 2004/Surface.dwg — 0/2 (rt only)

`ASSOCPLANESURFACEACTIONBODY.assocdep` + `.pbsab_status`: the
ASSOCPLANESURFACEACTIONBODY branch (normalize_silver.py, the
"assocdep=[0,0]" fabrication ~line 4850) passes ORIG (gold_orig's
sab-decoded assocdep really is the raw-null form) but on RT gold
resolves {5, action 1291} + pbsab_status 128 from silver's rewrite
while silver_rt's payload synthesizes the null/0 form. The rt-side
payload keeps surface_body.dependency=1291/path_status=128 —
flip the emission to the payload values when the pair is rt
(the harness passes a pair-pointing argument? check run_roundtrip's
normalizer invocation — simplest: emit the payload's real values
and re-check the orig side; the orig may ALSO come out right because
gold_orig's [0,0] vs payload 1291 — the orig paper trail is in the
§8.1.6 batch-28/29 notes and pk17o probe outputs. TIME-BOX this
one; it is 2 rows.)

## Environment

```
cd ~/work/cadcodec
source "$HOME/.cargo/env"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
python3 tests/gold_harness/check_env.py   # must print "Environment looks good"
cargo build --features serde --bins        # must succeed before any edit
```

(Windows host specifics: the repo lives in WSL; reach it via
`\\wsl$\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec` and run shell
commands through `wsl.exe -d Ubuntu-24.04 -- bash <script>`. wsl.exe strips
embedded quotes AND pipes (regex `\|` alternations die silently); single
search terms through wsl.exe, multi-pattern via the grep *tool*; HEREDOCS
via wsl.exe -c BREAK — write probe python to script files with the write
tool, run via their absolute paths. This PowerShell has NO `head` and
rejects `&&`. The `read` tool's `offset` is ignored on SOME UNC paths — use
`wsl.exe -- sed -n <start>,<end>p <file>` (no quotes needed) and the grep
tool for multi-pattern searches. CRITICAL paths: the example_*.dwg files
live at the test-data ROOT (`$GOLD_TESTDATA/example_2010.dwg`); PolyLine3D/
Helix/Constraints live IN the version folders; PolyLine2D/TS1 in 2000/;
Underlay+Surface in 2004/; LiveSection1 in 2018/; gh109_1 in 2013/;
gh209_1 in 2010/. dwgread exit 1 + empty output usually means a wrong
path, not a gold failure. Corpus launch: `target/probes/pk17r_corpus.sh`
(nohup, ABSOLUTE log path, sleep 8, pgrep confirm) + bounded
`24_wait.sh`; NEVER edit while the corpus runs (give it the full ~10
minutes; a second corpus can race the report).)

## Workflow (per packet)

1. Pick the lever (R1 is the biggest — its two pockets likely share one
   root; re-read the fresh report first).
2. Grep the gold spec: dwg.spec + dwg2.spec (+ common_entity_data.spec,
   common_entity_handle_data.spec, spec.h for flag semantics) — read the
   FULL block (macro + version predicate + value guards) before any
   retype; check §8.1.1 liveness (a typed gold record in the diff PROVES
   liveness).
3. Locate the silver side; pull row VALUES + both records from fresh
   per-file runs into a fresh dir (the pooled corpus dirs are stale for
   fixed families but valid for still-open ones; the residue dump
   pk18_residues_full.txt is the quick reference).
4. Minimal, version-gated fix: prefer normalizer projections; codec
   (reader retention + writer echo) only when the data is not stored.
   NEVER touch `diff_fields.py` / `ignore_fields.toml`.
5. `cargo build --features serde --bins`.
6. Verify per-file on ALL versions the family touches (fresh dirs) —
   use pk17e_rows.py `<workdir>` for the row list. Multi-version stems
   (Helix ×6 folders INCLUDING 2013+2018, Constraints ×4, PolyLine3D ×4)
   MUST be probed on every version — the Helix era-gate regression came
   from verifying only 2000-2010.
7. Run the corpus LAST, detached; one bounded `24_wait.sh` call.
8. Gates: `cargo test --features serde` (47 ok segments; roundtrip 97/0;
   the associative_constraint_group segment tests the FLAT constraint
   wire now) + `cargo test --features gold-harness --test gold_roundtrip`
   (ok). Deep-gate rule: ANY new raw-retention struct field gets a
   normalize_entity_for_comparison arm (seqend flag pairs, raw dataflags
   byte, OLE raw, LwPolyline raw flag precedents — keep the pattern; a
   failing deep test names the exact field).
9. Commit `fix(harness): <packet> — <gold spec ref> + before→after
   counts`, push (waves may bundle per-family counts; see 82f0225/
   078c119/c20e6fe). If a semantic rust test encoded the OLD wire
   theory, update the test WITH the spec citation (the
   associative_constraint_group precedent). No backticks in
   commit-message bodies (bash command substitution).

## Hard-won lessons (each one cost rows — do not repeat)

- **dwg2json/dwgread write `<stem>.json` beside the INPUT FILE by
  default** — always redirect or you WRITE INTO THE READ-ONLY GOLD TREE.
- **Write rows = rt-parser-parity pair (gold_rt vs silver_rt); read
  rows = orig pair; families can be one-sided** — Surface's ACTIONBODY
  passes orig and fails rt; the VIEW.has_ds_data rows are orig-only.
- **By-type tables truncate; per_file (FULL paths) is truth.** The
  multi-version stems (Helix/Constraints) share ONE corpus workdir —
  the pooled diff files there hold whichever version ran last; use
  per-file fresh runs for those.
- **The entity-common flag pair order is [ltype BB, plotstyle BB,
  R2007: material BB + shadow RC]** (common_entity_data.spec 507-522) —
  silver's reader was fixed in batch 32; handle-pull order is ltype,
  material, shadow, plotstyle (common_entity_handle_data.spec 127-141).
- **RAW beats recomposition**: retain the wire's raw values (dataflags
  byte, LwPolyline flag, per-SEQEND common flags, encr SAT blocks, OLE
  blob, RAPIDRT's garbage come read-order) — gold prints them verbatim
  and any value-based recomposition will differ.
- **Gold-bug parity IS the truth** (RAPIDRT garbage is IEEE patterns —
  the spec block beats intent; the differ compares gold's OUTPUT, not
  the "correct" decode).
- **Branch placement in the entity loop matters**: pop-branches before
  the generic field loop (~line 3670); the anchor
  `if gold_type == "POLYLINE_3D":` matches MULTIPLE sites in the file —
  verify the line number whenever an edit "doesn't fire", and stash
  values in locals before popping (`_p3d_flags`/`_p2d_flags`/the
  `_seq_pf_stash` precedents).
- **FIELD_NAME_MAP re-merges payload keys AFTER per-type branches** — a
  decoded emission (MTEXT "text") is overwritten unless the branch pops
  the source key; stashed per-record payload keys (seqend flags) must
  be popped at merge time or they leak through every generic loop.
- **normalize_gold reinterprets a 4-int list as the raw handle tuple
  [code, size, value, absref]** — mirror that when gold prints short
  int vectors (LWPOLYLINE.vertexids [21,22,23,24] case).
- **The `[0]*n` collapse family**: normalize_gold turns any dict
  without `index`+`rgb` into 0 (childval entries, MESH edge structs,
  SPLINE ctrl pts, SECTION_SETTINGS types, constraint-graph nodes).
- **Fabricated constant handle codes are time bombs** (WIPEOUT);
  normalize_handle_value(0) resolves as the null pair and passes when
  targets agree — but a null-vs-resolved FLIP between the orig and rt
  pairs (Surface ACTIONBODY, VIEWPORT.vport_entity_header) exposes
  the fabrication: match the payload's real value per pair.
- **Typing divergence poisons handle-vector resolution far away**
  (SURFACE mis-typing → SORTENTSTABLE rows in OTHER files).
- **Entity-common serde-skipped fields ride `_common_dwg` into
  merge_common — pop from `fields` AFTER the merge** (graphic_data
  precedent).
- **Bitflags serde joins with " | "** (split it); FIELD_CAST BS→BL
  zero-extends (0xFFCE→65486); MATERIAL rgb unsigned; wire codes
  SOLID 31 vs TRACE 32; ACIS banner split fixed-at-15 ("%.*s").
- **Silver object payloads nest common under `common` inconsistently** —
  location-aware extraction or records vanish.
- **The DWG binary wire cannot carry a semantic the format lacks**
  (constraint-group registry/class data is DXF-side; Helix pre-2013
  has no knotparam/splineflags) — gate by wire era, keep model
  richness out of the DWG writer for those fields, and update the
  semantic tests with the spec citation.
- **Never edit mid-corpus; never busy-poll; verify every touched
  version folder; git-commit each wave so a regression is one revert
  away.**

## The commit / push convention

- Branch `gold-vs-silver`, push to `origin/gold-vs-silver` after each
  batch. `fix(harness): <packet> — <gold spec ref> + before→after
  counts` (per-wave when families share a mechanism), then a separate
  `docs(harness): …` commit once §7/§8.1.6 are updated.
- Landed 2026-09-20: morning `fa2cb0a..b2955a7` (batches 7-23),
  `82f0225` (24-32), `078c119` (33-38), `5a25bf9` (39),
  `c20e6fe` (40), docs `1b1ac19` (+ this file's docs commit on top).
- The remaining inventory after each landed batch MUST be re-dumped
  (pk18a_all_rows.py) and this file re-checked against it before the
  next halt.
