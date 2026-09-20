# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target is
read AND write below **100** on BOTH sides. Current baseline (2026-09-20,
after docs commit `9bece22`): read **719** / write **755** (124 corpus
files; gh44-error.dwg explicitly out of scope via
`run_corpus.in_scope_files`). The two sides MIRROR family-for-family — every
wire-family you fix pays double. All remaining mass is reader/writer-side
captures, value-dependent forensics, or writer wire-order bugs; every packet
below carries its diagnosis and file:line anchors.

**FIRST ACTION: finish the in-flight MULTILEADER packet** — uncommitted WIP
is already in the working tree; the diagnosis is complete and the remaining
fix is ONE mechanical version gate (see "In-flight packet"). Expected −18
read / −18 write.

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
   15+ landed sessions deep).
3. `target/probes/fullsrc/` — a full LibreDWG source parse (2026-09-20).
   `findings_notes.md` is the distilled index with verbatim spec anchors
   for EVERY family in the queue below; `pkt_*.txt` files hold verbatim
   spec windows (WIPEOUT, VIEWPORT, smalls, dimstyle), and `gap2-5.txt` the
   stream/handle geometry. Reuse this before re-grepping gold.

## Current state (2026-09-20, session handoff)

- HEAD `9bece22` on `gold-vs-silver`, pushed. `cargo test --features serde`
  = all segments ok; `gold_roundtrip` = ok. Untracked
  `examples/cylinder_dwg.rs` predates the campaign — leave uncommitted.
- Three packets landed this session (docs folded into §7/§8.1.6):
  - **PROXY_OBJECT data/data_numbits/objids** (`fa2cb0a`, −13/−13): raw
    window capture to hdlpos in wire order (`capture_proxy_window` +
    `ProxyObject.raw_window`), byte<size−1 objids terminator, and the
    **PUSH_HV consecutive-dup collapse** (common.h:634) — the real ghost
    killer, not the ≥8-bits guard.
  - **DIMSTYLE_CONTROL.morehandles** (`b08d346`, −104/0): pass-1 RCu
    capture (the row was on EVERY carrier, one per file — the ranking's
    "19" was top-N truncation), writer echo, normalizer emission.
  - **LEADER R2000-pair family** (`b6e6e92`, −24/−24): box_height/
    box_width/arrowhead_type are wire fields at EVERY version; endptproj
    is VERSIONS(R_13c3,R_2007) INCLUDES R2007; reader/writer/normalizer
    aligned to dwg.spec 3014-3045.

## In-flight packet — MULTILEADER attach trio (FINISH FIRST)

Uncommitted WIP in the tree (all deliberate, keep it; builds green):

- `src/entities/multileader.rs` — new raw fields `dwg_attach_dir`,
  `dwg_attach_top`, `dwg_attach_bottom: i16` (+ constructor defaults 0)
- `src/io/dwg/dwg_stream_readers/object_reader/entities.rs` —
  `read_multileader`: trio wire order fixed to gold's dir(271),
  top(273), bottom(272) (dwg2.spec 1449-1451 — the DXF codes are NOT in
  wire order; silver's old dir/bottom/top swap was real but secondary)
- `src/io/dwg/dwg_document_builder.rs` — maps the three raws onto the
  entity
- `src/io/dwg/dwg_stream_writers/object_writer/entities.rs` —
  `write_multileader` tail writes the raws in gold order (R2010+)
- `tests/gold_harness/normalize_silver.py` — MULTILEADER branch emits
  `attach_dir/attach_top/attach_bottom` from `dwg_attach_*` (R2010+),
  pops them; residual comment updated

**Diagnosis (complete; evidence
`target/probes/fullsrc/pk4_open_diagnosis.txt`)**: rows persist as
wrong_value (gold attach_top=32, attach_bottom=178 vs silver 9/9) even
with the order fix — because silver's reader consumes bits the R2010+
wire does not carry. Gold dwg2.spec:1418-1445 wraps `VERSIONS (R_14,
R_2007) { num_arrowheads+loop, num_blocklabels+loop, is_neg_textdir B,
ipe_alignment BS, justification BS, scale_factor BD }` — on R2010+ ALL of
that is ABSENT, and the attach trio follows `is_annotative` immediately.
Silver reads `num_blocklabels` (ba_count BL + labels loop, entities.rs
4562-4583) and the four-field tail (4584-4587: is_neg_textdir/
ipe_alignment/justification/scale_factor) **unconditionally** → the trio
read lands on wrong bits. Gold's R2010 JSON record indeed lacks
scale_factor/is_neg_textdir/ipe_alignment/justification/num_blocklabels
(verified via `normalize_gold.normalize_gold` probe).

**Remaining fix**: in `read_multileader`, gate the block-attributes read
AND the four-field tail under `if !version.r2010_plus()`
(arrowhead_overrides is already gated; keep defaults for the pre-R2010
fields on R2010+ so nothing else changes). Then:

1. `cargo build --features serde --bins`
2. Verify carriers into FRESH dirs: 2010/Leader, 2013/Leader, example_2018
   (attach rows must be 0) AND 2000/Leader, 2004/Leader, 2007/Leader,
   entities-2d/3d (pre-R2010 still reads the group — no regression).
3. Watch for NEW extra_in_silver rows on R2010+ files for the pre-R2010
   fields (scale_factor, is_neg_textdir, ipe_alignment, justification,
   num_blocklabels): gold does not emit them there. If rows appear, gate
   the SAME fields in normalize_silver's MULTILEADER emissions and the
   writer's pre-R2010 outputs (write_multileader must not write
   ba_count/the tail on R2010+ — verify via the rt diff).
4. Corpus LAST, gates, commit `fix(harness): MULTILEADER attach trio —
   gold dwg2.spec 1418-1452 VERSIONS(R_14,R_2007) tail gate + dir/top/
   bottom raw retention`, push, fold into §7/§8.1.6, docs commit, push.

## Packet queue (after the in-flight one; sizes from the 719/755 report)

1. **UNKNOWN_OBJ.ownerhandle 37 + _missing 15 + _count 9** — biggest
   family. The ownercode side channel: silver's unknown-obj records carry
   a pipeline-default handle code 4 where gold reads wire-relative codes
   (6/8 — the unknown_bits precedent); `_missing`/`_count` are the
   dropped-record reader gaps (ex2010's handle-3140 class, TS1 ex-*).
   ASSOCSWEPTSURFACEACTIONBODY must STAY UNKNOWN_OBJ (dead block).
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
5. **VERTEX_MESH._missing 12 (TS1 mesh parse gap)** — silver drops
   VERTEX_MESH records; gold spec is trivial (flag RC + point 3BD).
6. **LEADEROBJECTCONTEXTDATA/OBJECTCONTEXTDATA typing (~24)** — silver
   types the object-context records as generic OBJECTCONTEXTDATA where
   gold decodes LEADEROBJECTCONTEXTDATA (dwg2.spec 4611, live);
   shows as count_mismatch + missing pairs on every Leader carrier.
   Retype via dxf_name in normalize (liveness rule §8.1.1) or reader.
7. **TOLERANCE field-name set (~10 on 2010/Leader)** — gold keys
   ins_pt/x_direction/text_height vs silver insertion_point/direction —
   normalize projection, value-gated (dwg.spec TOLERANCE block).
8. **Small write-side batch**: GROUP.name 6 (wire name T is ALWAYS "",
   writer writes the model name), MLINE.flags closed-bit (MLINE enum
   HAS_VERTEX=1 | CLOSED=2, dwg.h), 3DFACE.z_is_zero 8 (gold: has_no_
   flags B + z_is_zero B, omits z RDs when zero — silver writes them),
   VISUALSTYLE.edge_silhouette_width 9 (sign boundary: gold 65486
   (0xFFCE) vs silver -50 — check the BL vs BS sign handling),
   SORTENTSTABLE.ents (R2000 entries lost), MTEXT columns residue,
   LEADER boxes at 6 each carry over — spec windows all live in
   fullsrc/pkt_smalls.txt + fullsrc/findings_notes.md.
9. **Residue** — everything below the top-N tables: use
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
embedded quotes/pipes AND this PowerShell has NO `head` alias and rejects
`&&`; put non-trivial shell and ALL probe python into script files under
`target/probes/` and execute those. The read tool's `offset` may be ignored
on UNC paths — use `sed -n 'a,bp'` in scripts for line ranges.)

## Workflow (per packet)

1. Pick the packet from the queue above (finish the in-flight one first).
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
   shapes — stale last-wins on stem collisions).
4. Minimal, version-gated fix in `normalize_silver.py`/`normalize_gold.py`
   (projection) or the codec (only when the data is not stored). NEVER
   touch `diff_fields.py` / `ignore_fields.toml`.
5. `cargo build --features serde --bins`.
6. Verify per-file on all versions the family touches via
   `run_roundtrip.py` into fresh `target/probe_wip/<v>` dirs.
7. **Run the corpus LAST** (`run_corpus.py`), and while it runs DO NOT
   touch `normalize_silver.py`/`normalize_gold.py`/reader/writer — a
   mid-run edit produces a mixed-state report. Wait with the bounded
   `target/probes/24_wait.sh` (one blocking call; do NOT busy-poll).
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
  entirely while broken on the read side (morehandles) or vice versa
  (status_flag). The writer echo still matters: it keeps the rt faithful
  and silver_orig ≡ silver_rt.
- **Corpus report by-type tables are top-N TRUNCATED** — a family can
  carry one row per file across the whole corpus (morehandles was 104,
  ranked "19"). Truth: `report.json` `per_file` (compare by FULL path —
  stems collide across version dirs) and fresh per-file probes. For
  before/after A/B on a suspicious delta: `git stash`, rebuild, rerun
  corpus, compare `report.json` per-file by full path, `git stash pop`.
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
  preprocessor frame first (ASSOCSWEPTSURFACEACTIONBODY is DEAD). The
  UNKNOWN-family payload-clear runs LAST, after payload-keyed branches.
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
- **MULTILEADER**: the pre-R2010 tail (num_arrowheads/blocklabels/
  is_neg_textdir/ipe_alignment/justification/scale_factor) is
  VERSIONS(R_14,R_2007) — absent on R2010+; attach trio wire order is
  dir(271), top(273), bottom(272) — DXF codes ≠ wire order; the raw BS
  values (32/4786/178) are outside silver's typed enums — raw retention
  (dwg_attach_*) is required, enum projection loses them.
- **Value-gate every spec conditional**: tri R2007a, first/last chains
  pre-R2004, mtext_type SINCE R_2018b, vport_entity header pre-2004,
  endptproj VERSIONS(R_13c3,R_2007) INCLUDES R2007, CMC color forms per
  era, status_flag/count families per era. The DONE entries carry these.
- **Never edit mid-corpus**; never busy-poll (one bounded 24_wait.sh
  call); never trust pooled corpus dirs for field shapes.
- **The differ compares RESOLVED handle-target TYPE NAMES** — record
  retypes ripple; always re-run the corpus after type-map changes.

## The commit / push convention

- Branch `gold-vs-silver`, tracks `origin/gold-vs-silver`.
- `fix(harness): <packet> — <gold spec ref> + before→after counts`, then a
  separate `docs(harness): …` commit once §7/§8.1.6 are updated; push
  after each. Landed this session: `fa2cb0a`, `b08d346`, `b6e6e92` (+ docs
  `8c49887`, `a9031a5`, `9bece22`). The in-flight MULTILEADER packet is
  uncommitted WIP — finish, verify, commit it first.
