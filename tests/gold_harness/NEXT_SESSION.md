# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target is
read AND write below **100** on BOTH sides. Current baseline (2026-09-20,
after fix commit `fca5367` + its docs commit): read **683** / write **719**
(124 corpus files; gh44-error.dwg explicitly out of scope via
`run_corpus.in_scope_files`). The two sides MIRROR family-for-family — every
wire-family you fix pays double. All remaining mass is reader/writer-side
captures, value-dependent forensics, typed-vs-raw divergences, or writer
wire-order bugs; every packet below carries its diagnosis and file:line
anchors.

**FIRST ACTION: pick a packet from the queue below and start.** The working
tree is clean (only the unrelated, campaign-predating untracked
`examples/cylinder_dwg.rs` remains; leave it uncommitted). Two packets landed
on 2026-09-20 and are fully closed — do NOT re-diagnose them:
`45382ec` (MULTILEADER attach trio; MULTILEADER rows zero on both sides) and
`b123b4c` (TABLECONTENT→UNKNOWN_OBJ retype; the example_* "handle-3140
class" records; UNKNOWN_OBJ._count zero, _missing 9) and `fca5367`
(VERTEX_MESH dropped records; TS1; VERTEX_MESH rows zero on both sides).

**Staleness rule:** always re-read the by-type table from the FRESH
`target/gold_harness_corpus/report.json` before starting a packet — queue
numbers go stale (the "UNKNOWN_OBJ.ownerhandle 37" family self-resolved: its
rows were downstream desync of the unbated R2010+ MULTILEADER reader and died
with `45382ec` without any packet touching it).

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec`, verify class-block liveness
   (preprocessor frames) before any retype (§8.1.1), version-gate every
   conditional, differ/ignore-list frozen, regression gates, commit
   conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — the living plan. Read §7 (entry
   point; the baseline block ends with the "Next packets…" list — that IS
   the authoritative handoff), §8.1.0 (environment), §8.1.1 (liveness +
   frame map), §8.1.6 (queue; DONE entries carry per-packet recipes —
   17+ landed sessions deep; batches seven through eleven landed
   2026-09-20).
3. `target/probes/fullsrc/` — a full LibreDWG source parse (2026-09-20).
   `findings_notes.md` is the distilled index with verbatim spec anchors
   for EVERY family in the queue below; `pkt_*.txt` files hold verbatim
   spec windows (WIPEOUT, VIEWPORT, smalls, dimstyle), and `gap2-5.txt` the
   stream/handle geometry. Reuse this before re-grepping gold.
   `target/probes/pk5*.py` (this branch's probes) hold the UNKNOWN-family
   row forensics: row extraction, class-name mapping, per-carrier drops.

## Current state (2026-09-20, session handoff)

- HEAD is past fix `fca5367` on `gold-vs-silver`, pushed; the docs commit
  that carries this file follows it. `cargo test --features serde` = all
  segments ok (roundtrip suite 97/0); `gold_roundtrip` = ok. Working tree
  clean apart from untracked `examples/cylinder_dwg.rs`.
- Fresh corpus (post-`fca5367`): read **683** / write **719**. Top rows:
  SEQEND.ownerhandle 18 (write), VIEWPORT.status_flag 17 (read),
  UNKNOWN_OBJ._missing 9 (Cone/LiveSection/Surface typing pockets),
  LEADEROBJECTCONTEXTDATA/OBJECTCONTEXTDATA _count/_missing 6 each
  (typing pair), WIPEOUT.imagedefreactor 12 (write),
  VISUALSTYLE.edge_silhouette_width 9, 3DFACE.z_is_zero 8,
  SORTENTSTABLE.ents 6, GROUP.name 6, MTEXT column residue 6,
  UNKNOWN_ENT._missing 6, RAPIDRTRENDERSETTINGS._missing 6.
- Session history 2026-09-20 (all folded into §7/§8.1.6):
  - **PROXY_OBJECT data/data_numbits/objids** (`fa2cb0a`, −13/−13), notes
    in its DONE entry.
  - **DIMSTYLE_CONTROL.morehandles** (`b08d346`, −104/0).
  - **LEADER R2000-pair family** (`b6e6e92`, −24/−24).
  - **MULTILEADER attach trio** (`45382ec`, −12/−12): VERSIONS(R_14,R_2007)
    tail gate + dir(271)/top(273)/bottom(272) raw retention; raw-retention
    structs must mirror typed enum defaults at construction or the
    deep-roundtrip gate fails (full recipe in the DONE entry).
  - **UNKNOWN-family dropped-records: TABLECONTENT retype** (`b123b4c`,
    −12/−12): gold's DWG_OBJECT(TABLECONTENT) (dwg2.spec 466) is inside the
    dead frame opened at dwg2.spec 297; silver's typed TableContent objects
    nest their common fields under `payload["common"]`, so the
    handleless-wrapper guard skipped EVERY handled record; retype to
    UNKNOWN_OBJ + common-aware guard + common hoist (DONE entry has the
    full recipe).
  - **VERTEX_MESH dropped records** (`fca5367`, −12/−12): gold's TS1 mesh
    vertices decode fine in silver (flag 64, point 3BD, dwg.spec
    1199-1220) — the vanish was normalizer-side: the kid-capture tuple had
    the silver struct name POLYGON_MESH where the gold record name is
    POLYLINE_MESH (silently dead), plus the builder zeroed the parsed
    wire flag. LESSON: kid-capture tuples key on GOLD record names; a
    silver struct name is silently dead.

## Packet queue (sizes from the 683/719 report)

1. **UNKNOWN-family retyping pockets** (UNKNOWN_OBJ._missing 9 + Cone/
   LiveSection/Surface rows, both sides mirrored): (a) 2000/Cone.dwg —
   gold types one record ACSH_CONE_CLASS where silver's DynamicBlock
   wrapper retypes it UNKNOWN_OBJ (near-grade: other ACSH classes have
   landed retypes + projections in `_DYNBLOCK_RETYPE`/the object loop;
   add ACSH_CONE_CLASS + its field projection); (b) 2018/LiveSection1.dwg
   — gold: SECTIONOBJECT/SECTION_MANAGER/SECTION_SETTINGS (1 each) where
   silver decodes UNKNOWN_ENT(1)+UNKNOWN_OBJ(2); silver's raw bits ride
   `unknown_bits_by_handle`; model or retype via the side channel (check
   §8.1.1 liveness before retyping); (c) 2004/Surface.dwg — silver types
   5 SURFACE records where gold decodes UNKNOWN_ENT (dead SURFACE frame)
   and gold's PLANESURFACE record is missing in silver; the
   ASSOCDEPENDENCY.dep_on rows ride the same divergence.
   REMEMBER: ASSOCSWEPTSURFACEACTIONBODY must STAY UNKNOWN_OBJ (dead
   block); retype by dxf_name only for LIVE blocks; retype must come WITH
   the field projection or it explodes rows.
2. **SEQEND.ownerhandle 18 (write rows)** — the writer's synthesized
   seqends' owner links (entmode==0 ⇒ ownerhandle code 4; pre-R2004
   prev/next nolinks). Diff rows on gold_rt-vs-silver_rt pair.
3. **VIEWPORT.status_flag 17 (read rows only)** — plain `FIELD_BL
   (status_flag, 90)` SINCE R_2000b (dwg.spec 2484, after num_frozen_
   layers BL); silver decomposes into named bits and normalizer
   re-composes (drops bits — gold 819232 vs silver 32800). Needs raw
   retention: reader capture + writer echo + normalizer preference.
   Write rows do NOT appear for this family (rt-parser-parity pair).
4. **WIPEOUT.imagedefreactor 12 (write rows)** — silver's write_wipeout
   (entities.rs ~4015) writes BOTH handles at the END as
   HardPointer{5}; gold's wire order (dwg2.spec 1561-1594, exact IMAGE
   copy): imagedef(code 5) between image_size 2RD and display_props BS,
   imagedefreactor(code 3) after fade RC. Fix writer order/codes; verify
   the stray `{3,0}` disappears via dump_section_bytes on the rt record.
5. **LEADEROBJECTCONTEXTDATA/OBJECTCONTEXTDATA typing (~24)** — silver
   types the object-context records as generic OBJECTCONTEXTDATA where
   gold decodes LEADEROBJECTCONTEXTDATA (dwg2.spec 4611, live);
   shows as count_mismatch + missing pairs on every Leader carrier.
   Retype via dxf_name in normalize (liveness rule §8.1.1) or reader.
6. **TOLERANCE field-name set (~10 on 2010/Leader)** — gold keys
   ins_pt/x_direction/text_value vs silver insertion_point/direction —
   normalize projection, value-gated (dwg.spec TOLERANCE block).
7. **Small write-side batch**: GROUP.name 6 (wire name T is ALWAYS "",
   writer writes the model name), MLINE.flags closed-bit (MLINE enum
   HAS_VERTEX=1 | CLOSED=2, dwg.h), 3DFACE.z_is_zero 8 (gold: has_no_
   flags B + z_is_zero B, omits z RDs when zero — silver writes them),
   VISUALSTYLE.edge_silhouette_width 9 (sign boundary: gold 65486
   (0xFFCE) vs silver -50 — check the BL vs BS sign handling),
   SORTENTSTABLE.ents (R2000 entries lost), MTEXT column residue,
   LEADER boxes at 6 each carry over — spec windows all live in
   fullsrc/pkt_smalls.txt + fullsrc/findings_notes.md. Also TS1's
   SOLID._count 3 / TRACE._count 3 ord-shift rows (NOT mesh fallout —
   they survived `fca5367`; adjudicate separately).
8. **Residue** — everything below the top-N tables: use
   report.json `*_fidelity_by_type_field` dicts (they are TRUNCATED —
   per-file truth only) and per-file probes.

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
commands through `wsl.exe -d Ubuntu-24.04 -- bash <script>` — wsl.exe strips
embedded quotes AND pipes (including `\|` alternations in grep patterns:
pass single search terms through wsl.exe, use the grep *tool* for
multi-pattern queries) AND this PowerShell has NO `head` alias and rejects
`&&`; put non-trivial shell and ALL probe python into script files under
`target/probes/` and execute those. The `read` tool's `offset` is ignored
on SOME UNC paths — if a read starts at line 1, use `sed -n 'a,bp'` in a
script for line ranges instead. To launch the corpus detached AND have it
survive the launcher session, use a launcher script that nohups the corpus
with an ABSOLUTE log path and sleeps ~8s before exiting (pk4j/pk5t
pattern); a bare launch died once.)

## Workflow (per packet)

1. Pick the packet from the queue above (in order).
2. Grep the gold spec: BOTH `dwg.spec` and `dwg2.spec`; check the enclosing
   preprocessor frame for liveness (§8.1.1) BEFORE any retype; read the
   full spec block (macro + version predicate + value guards). The
   fullsrc/ artifacts usually already hold the verbatim window.
3. Locate the silver side: reader
   (`src/io/dwg/dwg_stream_readers/object_reader/{entities,objects}.rs`),
   writer (`src/io/dwg/dwg_stream_writers/object_writer/*.rs`), builder
   (`src/io/dwg/dwg_document_builder.rs`), struct
   (`src/objects|entities|tables/<type>.rs`). Confirm silver stores the
   data in the dump (fresh `run_roundtrip.py` into a FRESH dir; NEVER
   trust pooled `target/gold_harness_corpus/<stem>/` artifacts for field
   shapes — stale last-wins on stem collisions. Single-version stems
   (Cone, TS1, LiveSection1, Surface, PolyLine2D, example_*) ARE fresh.)
4. Minimal, version-gated fix in `normalize_silver.py`/`normalize_gold.py`
   (projection) or the codec (only when the data is not stored). NEVER
   touch `diff_fields.py` / `ignore_fields.toml`.
5. `cargo build --features serde --bins`.
6. Verify per-file on all versions the family touches via
   `run_roundtrip.py` into fresh `target/probe_wip/<v>` dirs.
7. **Run the corpus LAST** (`run_corpus.py`), and while it runs DO NOT
   touch `normalize_silver.py`/`normalize_gold.py`/reader/writer — a
   mid-run edit produces a mixed-state report. Launch detached (see
   Environment), confirm the pid with `pgrep -f run_corpus.py`, then wait
   with the bounded `target/probes/24_wait.sh` (ONE blocking call; do
   NOT busy-poll).
8. Gates: `cargo test --features serde` (all segments ok — count the
   `test result: ok` segments, not just the tail) and
   `cargo test --features gold-harness --test gold_roundtrip` (ok).
9. Commit: `fix(harness): <packet> — <gold spec ref> + before→after
   counts`, push, update §7 baseline + §8.1.6 queue, docs commit, push.

## Hard-won lessons (do not repeat)

- **dwg2json writes `<stem>.json` next to the INPUT FILE by default** —
  always pass an explicit output path, or you will WRITE INTO THE
  READ-ONLY GOLD TREE (happened once; file removed immediately).
- **Write-fidelity rows come from the rt-parser-parity pair**
  (gold_rt vs silver_rt) — a family can be absent from the write side
  entirely while broken on the read side (morehandles, status_flag) or
  vice versa. The writer echo still matters: it keeps the rt faithful
  and silver_orig ≡ silver_rt.
- **Corpus report by-type tables are top-N TRUNCATED and stem-inflated**
  — MULTILEADER attach ranked 18 read rows while the true per-file drop
  was −12/−12. Truth: `report.json` `per_file` (compare by FULL path —
  stems collide across version dirs) and fresh per-file probes. For
  before/after A/B on a suspicious delta: `git stash`, rebuild, rerun
  corpus, compare `report.json` per-file by full path, `git stash pop`.
- **Re-read the FRESH by-type table before each packet** — families can
  self-resolve as side effects (UNKNOWN_OBJ.ownerhandle 37 died with the
  MULTILEADER reader fix `45382ec`; consuming the queue verbatim diagnoses
  ghosts).
- **A reader that eats more bits than its record carries desyncs
  everything downstream in the file** — treat count/missing-family
  "mystery" records in the SAME file as potential downstream fallout of
  an unbounded read; fix the upstream record first, then re-check.
- **Raw-retention struct fields must mirror the typed enum defaults at
  construction** — whenever a struct carries BOTH a typed enum and its
  raw DWG wire value (dwg_attach_*, raw linewt codes, …), the internal
  deep-roundtrip gate (`dwg_roundtrip_deep_{r2000,r2013,r2018}`) fails
  on any split: pre-gated writes read back reader defaults, post-gated
  writes read back the raws. Set constructor raws = the typed defaults
  (e.g. CenterOfText=9, Horizontal=0), as the MULTILEADER tenth batch did.
- **unknown_bits tail byte is LSB-packed** (`chain[bytes] |= last << i`,
  bits.c): full bytes MSB-first, trailing partial byte read-order bit i
  at LOW position i. Same packing for PROXY raw windows.
- **PROXY `data` window** = [after-prologue .. obj->hdlpos) in WIRE
  order incl. the string area (R2007+: the dxf_subclass TU + text bits +
  17-bit RS/has_strings trailer sit INSIDE the window; use
  `capture_proxy_window()`); objids = the handle walk with gold's
  PUSH_HV **consecutive-duplicate (code,value) collapse** + terminator
  `hdl_dat->byte < hdl_dat->size − 1`.
- **The differ tolerates a missing handle code** (identity = resolved
  target); NEVER fabricate constant codes — the UNKNOWN-family code-4
  stamp mismatched gold's wire-relative 6/8 (−37/−3 lesson).
- **Retype by dxf_name ONLY for LIVE class blocks** — check the
  preprocessor frame first (§8.1.1; TABLE/TABLECONTENT sit inside
  `#if DEBUG_CLASSES || defined(IS_FREE)` at dwg2.spec 297-959 and must
  stay UNKNOWN; ASSOCSWEPTSURFACEACTIONBODY is dead). Retype must come
  WITH the field projection in the same packet or it explodes field
  rows. The UNKNOWN-family payload-clear runs LAST, after payload-keyed
  branches.
- **Silver object payloads nest common fields inconsistently** —
  top-level on most wrappers, under `payload["common"]` on TableContent;
  guards/extractions must be location-aware or they skip every record
  (the TABLECONTENT bug).
- **Same-version DWG roundtrips keep `document.classes` verbatim**; entity-
  common serde-skipped fields ride `_common_dwg` (hex-handle keys) into
  `merge_common` — payload pop lists cannot see them.
- **The `[0]*n` degenerate REPEAT pattern** covers dozens of families —
  gold collapses one element per record into a bare 0. Count source
  differs per family; verify per file across versions.
- **SEQEND records must be re-sorted ascending by handle** at the end of
  `normalize_silver` — the differ aligns by (type, ordinal-within-type).
- **Entity-common linewt (370) is the RAW code**, not a table index.
- **Wire-name constants**: GROUP's name T is always "" (even for named
  groups); ATTRIB style is raw `[0,0]` null from R2010+; MULTILEADER/
  ARC_DIMENSION/LIGHT never carry graphic_data (census-verified pops);
  osnap params' gold constants are osnap_mode 160 / param 0.0.
- **MATERIAL rgb is the UNSIGNED i32** (`& 0xFFFFFFFF`).
- **MULTILEADER is fully closed** — the pre-R2010 tail (num_arrowheads/
  blocklabels/is_neg_textdir/ipe_alignment/justification/scale_factor)
  is VERSIONS(R_14,R_2007), absent on R2010+; attach trio wire order is
  dir(271), top(273), bottom(272); the raws live in dwg_attach_* and are
  the ONLY wire-true source of attach values (32/4786/178-style codes).
- **Value-gate every spec conditional**: tri R2007a, first/last chains
  pre-R2004, mtext_type SINCE R_2018b, vport_entity header pre-2004,
  endptproj VERSIONS(R_13c3,R_2007) INCLUDES R2007, status_flag/count
  families per era. The DONE entries carry these.
- **Never edit mid-corpus**; never busy-poll (one bounded 24_wait.sh
  call); never trust pooled corpus dirs for field shapes.
- **The differ compares RESOLVED handle-target TYPE NAMES** — record
  retypes ripple; always re-run the corpus after type-map changes.

## The commit / push convention

- Branch `gold-vs-silver`, tracks `origin/gold-vs-silver`.
- `fix(harness): <packet> — <gold spec ref> + before→after counts`, then a
  separate `docs(harness): …` commit once §7/§8.1.6 are updated; push
  after each. Landed on 2026-09-20: batches 7–12 = `fa2cb0a` (PROXY),
  `b08d346` (DIMSTYLE_CONTROL), `b6e6e92` (LEADER family), `45382ec`
  (MULTILEADER attach trio), `b123b4c` (TABLECONTENT dropped records),
  `fca5367` (VERTEX_MESH dropped records), each followed by a docs commit
  (`8c49887`, `a9031a5`, `9bece22`, `444f4aa`, `3065f74`, `0a79f98`,
  and the one carrying this file).
