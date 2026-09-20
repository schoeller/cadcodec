# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target
is read AND write below **100** on BOTH sides (raised from 1 000 after it
was passed on 2026-09-20). Current baseline (2026-09-20, HEAD `b0b251e`):
read **860** / write **792** (124 corpus files; gh44-error.dwg explicitly
out of scope via `run_corpus.in_scope_files`). The two sides MIRROR
family-for-family — every family you fix pays double. All remaining mass
is reader/writer-side captures or value-dependent forensics; every packet
in the queue below carries its diagnosis and the file:line anchors.
Work the queue in order; iterate diagnose → fix → verify → gates →
commit → docs until you halt.

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec`, **verify class-block liveness
   (preprocessor frames) before any retype** (§8.1.1), version-gate every
   conditional, the differ/ignore-list are frozen, regression gates, commit
   conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — the living plan. Read §7 (entry
   point; the baseline block ends with the "**Next packets…**" list — that
   IS the authoritative handoff), §8.1.0 (environment verification),
   §8.1.1 (liveness rule + frame map), §8.1.6 (queue; the newest DONE
   entries carry per-packet recipes — 12 landed sessions deep).

## Current state (2026-09-20, session handoff)

- Baseline: read **860** / write **792**. `cargo test --features serde` =
  all segments ok, 0 failed (the 1556 figure spans segments);
  `gold_roundtrip` = ok. All work pushed on `gold-vs-silver` (HEAD
  `b0b251e`). Two untracked `examples/*.rs` files predate the campaign —
  leave them uncommitted.
- Campaign so far (this file's obsolete packets are folded into
  IMPLEMENTATION.md §8.1.6 DONE entries): U2 dynamic-block retypes,
  unknown_bits raw-remainder side channel (−448/−448), style-map +
  INSERT-chain + MLINE (−327/−319), POLYLINE_3D + GROUP + PFACE chains +
  ASSOC actionbody/path retypes (−478/−493), RAY/XLINE + IMAGEDEF + HATCH
  degenerates + VX family + LIGHT + RASTERVARIABLES (−338/−336), HELIX +
  LEADER/TOLERANCE dimstyle + MATERIAL rgb (−172/−172), UNKNOWN-family
  handle-code unstamp (−37/−3), raw-linewt fidelity + LAYOUT.viewports
  (−46/−9).

## Packet queue (in this order)

1. **PROXY_OBJECT data/data_numbits 30+30 + objids 18** (~78/side, pure
   reader capture): gold's `data` is the raw window from after the proxy
   prologue to hdlpos (dwg.spec 5752 DECODER). Forensics done: on
   Constraints/2007 h=992 gold_numbits=1179 = payload-bits(332) ++
   text-bits(516) ++ handle-tail(331) — BIT-spliced, NOT byte-aligned
   (silver's stored sections diverge from gold at bit 337 because silver's
   merged-reader main/text emulation boundary ≠ the classic wire).
   NOT derivable from current storage. Fix in silver's proxy parse
   (`src/io/dwg/dwg_stream_readers/object_reader/entities.rs:855-930`,
   after `from_dxf`): capture the full raw window in WIRE order across
   the main/text/handle sections into a new `ProxyEntityData` field (serde-
   transparent, `bit_count` + bytes), then emit `data` hex +
   `data_numbits` in normalize_silver's ProxyObject branch. Verify
   bit-exactness per carrier (Cons*, Constraints, Robertson-era files)
   before trusting the merged-reader splice; pre-2010 and R2010+ records
   must both be probed. objids: on some carriers silver's list has
   terminator ghosts — the §8.1.1 byte-geometry lesson (gold stops at
   `hdl_dat->byte < size - 1`); locate carriers from a clean report.
2. **DIMSTYLE_CONTROL.morehandles 19** (reader capture): gold's vector uses
   its own wire count `RCu num_morehandles` (dwg.spec 4163-4182,
   "additional hard handles, undocumented") — silver's reader drops it.
   Capture point: pass-1 right after `read_common_non_entity_data` for
   `OBJ_DIMSTYLE_CONTROL` (builder dispatch at
   `src/io/dwg/dwg_document_builder.rs:767`); pin the RCu read semantics
   from `dec_macros.h` first; per-type CONTROL data shapes differ, so
   guard the parse per class. Store as a pub serde-transparent map; emit
   in the DIMSTYLE_CONTROL `_ctrl` block of normalize_silver. WARNING
   (2026-09-20 regression story): emitting the whole dim-style table
   produced 109 wrong_value rows — morehandles ≠ entries.
3. **WIPEOUT.imagedefreactor 12 (write-side)**: gold expects
   [4,imagedef][5,reactor]; silver's `write_wipeout` writes BOTH as
   HardPointer{5} (`.../object_writer/entities.rs:4015-4070`), yet gold-rt
   reads a stray `{3,0}` null in the reactor slot on R2000/2004/2007 —
   suspect a common-handle count/sequence shift for unlisted-class
   entities on classic records. Diagnose by dumping the rt file's WIPEOUT
   record bytes (dump_section_bytes works on the rewritten file too) and
   comparing the handle-section sequence against gold's spec order.
4. **Value-dependent set**: MULTILEADER.attach_top/attach_bottom 9+9
   (gold BS pairs 32 / 4786 / 178 per record — spec forensics on the
   dwg2.spec 1298 MLEADER dock/context fields; constants not derivable
   from silver enums yet); VIEWPORT.status_flag 17 (Dynblocks R2018: gold
   819232 vs silver 32800 — gold reads raw BS bits silver's bit-name
   decomposition drops; needs raw retention: reader capture + writer
   echo + normalizer preference); SEQEND.ownerhandle 18 (write rows —
   the writer's synthesized seqends' owner links); UNKNOWN_OBJ
   _missing 15 + _count 9 (reader drops some class records — ex2010's
   handle-3140 type; find and parse them or leave documented).
5. **Small residue tails** (each a mini-packet): 3DFACE.z_is_zero 8
   (write, R2000), MTEXT.column_count/width 6+6, VISUALSTYLE
   .edge_silhouette_width 9, LEADER R2000 pairs (~24: arrowhead_type/
   box_height/box_width/hookline_dir/unknown_bit_4), LEADEROBJECT
   CONTEXTDATA + OBJECTCONTEXTDATA _count/_missing (~24), VERTEX_MESH
   _missing 12 (TS1 mesh parse gap), MLINE.flags closed-bit (R2000:
   silver's parse keeps only HAS_VERTICES → gold flag 3), poly-SEQEND
   shadow pairs (wire-record shadow commons — a seqend storage
   side-channel or reader parsing), GROUP.name 6 write rows (writer
   writes the model name where the wire name T is always ""), and the
   accepted residuals (3DSOLID/REGION.encr_sat_data on R2000).

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

1. Pick the packet from the queue above (order matters: PROXY is the
   biggest single lever; the reader captures 2-4 share a rebuild cycle).
2. Grep the gold spec: BOTH `dwg.spec` and `dwg2.spec`; check the enclosing
   preprocessor frame for liveness (§8.1.1) BEFORE any retype; read the
   full spec block (macro + version predicate + value guards).
3. Locate the silver side: reader
   (`src/io/dwg/dwg_stream_readers/object_reader/{entities,objects}.rs`),
   writer (`src/io/dwg/dwg_stream_writers/object_writer/*.rs`),
   builder (`src/io/dwg/dwg_document_builder.rs`), struct
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
   mid-run edit produces a mixed-state report (paid for this twice on
   2026-09-20; both runs had to be killed). Wait with the bounded
   `target/probes/24_wait.sh` (one blocking call; do NOT busy-poll).
8. Gates: `cargo test --features serde` (all ok) and
   `cargo test --features gold-harness --test gold_roundtrip` (ok).
9. Commit: `fix(harness): <packet> — <gold spec ref> + before→after
   counts`, push, update §7 baseline + §8.1.6 queue, docs commit, push.

## Hard-won lessons (do not repeat)

- **unknown_bits tail byte is LSB-packed** (`chain[bytes] |= last << i`,
  bits.c 1733): full bytes MSB-first, trailing partial byte read-order bit
  i at LOW position i. MSB-aligned tails differ in EXACTLY the final byte
  (03/01 vs C0/80). The HANDLE_UNKNOWN_BITS window is a FULL class-payload
  snapshot (position restored after) — not leftover bits.
- **The differ tolerates a missing handle code** (identity = resolved
  target); NEVER fabricate constant codes — the UNKNOWN-family code-4
  stamp mismatched gold's wire-relative 6/8/12 and cost 37 rows until
  unstamped.
- **Retype by dxf_name ONLY for LIVE class blocks** — check the
  preprocessor frame first. `ASSOCSWEPTSURFACEACTIONBODY` is DEAD in gold
  (types UNKNOWN_OBJ) — do not retype. The UNKNOWN-family payload-clear
  runs LAST, after every payload-keyed retype branch.
- **Same-version DWG roundtrips keep `document.classes` verbatim**; entity-
  common serde-skipped fields ride `_common_dwg` (hex-handle keys) into
  `merge_common` — payload pop lists cannot see them.
- **The `[0]*n` degenerate REPEAT pattern** covers dozens of families
  (verts, pab.values, actions, deps, colors, deflines, cells, paths…):
  gold collapses one element per record into a bare 0. The count source
  differs per family (kid list, rows×cols, len(values)); verify per file
  across versions (2000/2004/2007/2010/2013/2018).
- **SEQEND records must be re-sorted ascending by handle** at the end of
  `normalize_silver` — the differ aligns by (type, ordinal-within-type)
  and silver's iteration order interleaves wrongly.
- **Entity-common linewt (370) is the RAW code**, not a table index:
  out-of-table codes (Dynblocks' invalid 28) echo verbatim; the reader
  keeps 24..28 as `Value(raw)`, the writer echoes, `_lweight_index`
  echoes untabled mm values (`6fd5a10`).
- **Wire-name constants**: GROUP's name T is always "" (2001-era verified,
  even for named groups); ATTRIB style is raw `[0,0]` null from R2010+;
  MULTILEADER/ARC_DIMENSION/LIGHT never carry graphic_data (census-verified
  pops); osnap params' gold constants are osnap_mode 160 / param 0.0 on
  every corpus record.
- **MATERIAL rgb is the UNSIGNED i32** (silver serializes signed; `& 0xFFFFFFFF`).
- **DIMSTYLE_CONTROL.morehandles is its own wire vector** (RCu count) —
  emitting the dim-style table as morehandles regressed 19 → 109 rows.
- **Value-gate every spec conditional**: tri locks R2007a / RCs R2010b,
  first/last chains pre-R2004, mtext_type SINCE R_2018b, vport_entity
  header pre-2004, CMC color forms per era — the DONE entries carry these.
- **CMC color method byte, dataflags/num_* absence-bitmasks, REPEAT/REPEAT_CN
  degenerate JSON, LineWeight table, side channels
  (`xdic_by_handle`/`reactors_by_handle`/`dwg_data_store_handles`/
  `unknown_bits_by_handle`), stem collisions, handle-vector codes (objids
  byte-geometry)** — all still apply; the DONE entries carry their details.
- **The differ compares the RESOLVED handle-target TYPE NAME** — record
  retypes ripple; always re-run the corpus after type-map changes.
- **Never edit mid-corpus** (see workflow 7) and never busy-poll background
  waits — one bounded blocking script call (`target/probes/24_wait.sh`).

## The commit / push convention

- Branch: `gold-vs-silver` (tracks `origin/gold-vs-silver`).
- Commit: `fix(harness): <packet> — <gold spec ref> + before→after counts`
  followed by a separate `docs(harness): …` commit once §7/§8.1.6 are
  updated; push after each.
- The totals in THIS brief go stale by design — §7 is authoritative.
