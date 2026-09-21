# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target
(2026-09-20, raised) is read AND write 0 on BOTH sides. Current baseline
(2026-09-20 post-dossier fold; code HEAD `e0c6f93`, docs fold on top):

**read 0 / write 2 — 123 of the 124 corpus files are at 0/0.**

gh44-error.dwg stays explicitly out of scope via `run_corpus.in_scope_files`.
The ONLY remaining rows live in **one file** (2004/Surface.dwg, 2 write
rows, rt-pair-only). This pocket was time-boxed at the previous halt —
IT IS NOW FULLY DECODED: the "route to zero" below carries the complete
forensic dossier (gold's per-slot trace decodes of the orig AND rewrite
wires, the raw record bytes, the seven decoded truths incl. the flattened
JSON key collision and the truncated-orig record, the exact three-edit
fix with file/line targets, and the verification matrix). Zero is a
2-3 hour packet from this file alone — no other context needed.
Full residue values: `target/probes/pk18_residues_full.txt` (regenerate any
time: `python3 target/probes/pk18a_all_rows.py`).

**Session history (2026-09-20):** morning batches 7-23 (`fa2cb0a..b2955a7`);
evening batches 24-32 (`82f0225`), 33-38 (`078c119`), 39 (`5a25bf9`), 40
(`c20e6fe`); the late-night third fold: 41 (`707e7a8`, gh109_1 16/14 → 0/0 —
RAPIDRT rapid-order gold shadow + SORTENTSTABLE wire entries), 42 (`604f956`,
the chain-ordinal wave — PolyLine2D/TS1/LiveSection1/examples ALL → 0/0),
43 (`e0c6f93`, deep-gate arms for the new retention fields), docs `fe23963`
+ this fold's docs commit on top. Session total: read 38 → 0, write 30 → 2.

**Staleness rule:** re-read `target/gold_harness_corpus/report.json`
(`read_fidelity_total`, `write_fidelity_total`, and `per_file` — entry
keys are file/returncode/read_fidelity_diffs/write_fidelity_diffs; the
by-type tables truncate, per_file is truth) after every landed batch —
families self-resolve as side effects.

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec` **plus `common_entity_data.spec` and
   `common_entity_handle_data.spec`** (the common flag pairs), and
   `spec.h` (flag-bit names AND the VERSION/VERSIONS macro semantics);
   verify class-block liveness (§8.1.1) before any retype;
   version-gate every conditional; differ/ignore-list frozen; commit
   conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — §7 (baseline chain + the
   single-packet Surface queue = the long form), §8.1.0, §8.1.1, §8.1.6
   (DONE entries batches 7-43; the batch-41/42 entries carry the full
   recipes for this session's mechanisms).
3. `target/probes/` — the probe library: `pk16a/b/c` (census/key-maps),
   `pk17*` (family probes), `pk18a_all_rows.py` (residue dump),
   `pk19_*` (this session's waves: RAPIDRT theory verifier
   `pk19_07_theory.py`, LPC bit-walker `pk19_29_lpcwalk2.py` (the
   reusable MSB-first cursor class), generic fresh-run
   `pk19_15_run_any.sh <relpath>`, gates `pk19_13*`, and the Surface
   dossier set `pk19_42_surf.py` / `pk19_52_surftrace.sh` /
   `pk19_53_recdump.sh` / `pk19_54_afterrec.sh` — all regenerable via
   `pk19_55_surf_dossier.sh`).
4. `target/probes/pk18_residues_full.txt` — the (now 2-row) residue list.

## The route to zero — the single remaining pocket (FULL DOSSIER)

### 2004/Surface.dwg — 0 read / 2 write (rt only): ASSOCPLANESURFACEACTIONBODY.assocdep + .pbsab_status

Everything below is decoded and evidence-backed (traces + byte dumps,
regenerable in one shot with `target/probes/pk19_55_surf_dossier.sh`).

#### A. The record

Handle 1292 (0x50C), type 536 ACDBASSOCPLANESURFACEACTIONBODY, class
number 537-style ≥500 (unstable per gold). The file is R2004 → silver's
record parse uses the **pre-2007 TwoStream path**
(object_reader/mod.rs step 5, `read_record_at`).

- **ORIG record**: MS 23 → 23 data bytes at [342801..342824) in the
  DECOMPRESSED objects stream (Address = the BS-type position). Raw:
  `06 00 9F C0 00 00 00 81 43 2A 80 D2 03 51 07 55 00 64 0A 1C 84 0A 1B`
  Bytes right after (silver's overread source, [342824..342840)):
  `AD AE | 1B 00 | 03 80 A5 00 00 00 00 81 43 6A 81 20`
  (`AD AE` = the per-object local CRC the trace computes as AEAD; `1B` =
  the next object-map MC stamp; then record 212's data).
- **RT record** (silver's rewrite, Surface_rt.dwg): MS 37, data
  [354965..355002). Same core bytes, then an APPENDED TAIL:
  `01 21 02 85 A1 02 87 29 02 86 A9 02 85 80` — the extra slots silver's
  writer emits for this family (sab.assocdep + the main tail).

Gold trace preface convention (verified on both records): the v9 `@(n.m)`
markers count from the MS start (Address−2); [trace-byte 0..2) = MS;
type BS at trace-bit 16; RL bitsize at trace-bit 34 (orig 127, rt 193 —
both verified by bit-decode of the dumped bytes); handle stream starts
AT THE BITSIZE position (orig @15.7 = bit 127, rt @24.1 = bit 193); the
UMC "Hdlsize" = total_data_bits − bitsize (orig 184−127 = 57 = 0x39,
rt 296−193 = 103 = 0x67 ✓ the trace prints).

#### B. Gold's decodes (paste-relevant extracts at
`target/probes/pk19_surf_orig_trace.log` / `pk19_surf_rt_trace.log`,
lines ~108638 / ~120542; regen: `pk19_52_surftrace.sh`)

ORIG — the record is TRUNCATED; gold's tail reads go past its end (its
own dat-end clamps + "buffer overflow" ERROR lines):
```
ownerhandle: (8.0.0) abs:50B [H 330] @15.7          ← empty code-8, resolves rel to 1291
aab_version: 1 [BL] @11.1; pab.version/minor 0; pab.num_deps: 1 @12.7
pab.deps[vcount]: (3.2.50E) abs:50E = 1294 [H 360] @16.7
pab.l4 0; pab.num_values 0; pab.l5 0
pab.assocdep: (4.2.50D) abs:50D = 1293 [H 330] @19.7   ← the pab slot EXISTS on the trunc wire
REPEAT_CHKCOUNT pab.values x 0
sab.version: 847293059 [BL] @17.7
sab.assocdep: NULL 5 [H 330] @22.7       ← OVERFLOW: "bit_read_RC buffer overflow at 22.7 + 1 > 23"
sab.is_semi_assoc 0; sab.l2 672166440; is_semi_ovr 0; grip_status: 256 [BS '11'] @22.5
pbsab_status: 0 [BL] @22.7               ← overflowed read → 0
class_version: 0 [BL] @23.1              ← overflowed
handle stream = exactly 3 slots: [owner 8.0.0][deps (3.2.50E)][pab.assocdep (4.2.50D)]
```
RT — the full layout (exactly what the DWG spec block expects):
```
ownerhandle: (4.2.50B) abs:50B = 1291 @24.1
pab.deps: (4.2.50E)=1294 @27.1; pab.assocdep: (5.2.50D)=1293 @30.1
sab.version 847293059 @17.7; ... grip_status 256 @22.5
sab.assocdep: (5.2.50B) abs:50B = 1291 [H 330] @33.1
pbsab_status: 128 [BL] @23.7            ← REAL (main stream, pre-handle-region)
class_version: 0 [BL] @24.1
```
Note the orig-vs-rt code differences on shared slots (owner (8.0.0) vs
(4.2.50B); deps (3.2.50E) vs (4.2.50E)) — silver's writer canonicalizes;
the differ tolerates code-only differences (targets are compared).

#### C. The seven decoded truths

1. **The flattened JSON "assocdep" = the SAB slot.** The embedded
   pab.assocdep and sab.assocdep are two DIFFERENT wire slots but land on
   ONE JSON key — out_json writes pab's first, sab's second, LAST WINS.
   The pab slot (1293 on both files) prints NOWHERE. Gold orig prints
   assocdep=[0,0] because its sab read hit the record end → NULL-5 form;
   gold rt prints [5,2,1291,1291] from the real sab slot.
2. **Gold's orig decode is an overflow of a truncated record**: the wire
   physically has only [owner][deps 1294][pab.assocdep 1293] in its
   handle region and nothing for the sab slot/main tail; every tail read
   clamps (NULL / BL 0) with printed overflow errors.
3. **pbsab_status is a main-stream BL** after the sab block: orig →
   overflow 0; rt → real 128 (verified in the appended-tail bytes).
4. class_version: orig 0 (overflow) / rt 0 (real) — coincidentally
   equal, passes both pairs today.
5. **Silver's WRITER is correct** — it lays out the full gold-spec record
   (the rt append-tail proves it). No writer change is required for
   parity; after the reader fix it will simply write the null/0 tail for
   this file, and gold_rt will then decode [0,0]/0 = its orig decode.
6. **Silver's READER overreads the truncated record**: its model has
   surface_body.dependency=1291 + path_status=128 on the ORIG read —
   garbage, because the pre-2007 merged reader has NO record-end bounds
   (the handle reader is built over the shared buffer with no end; main
   reads likewise continue past the data). Prime-suspect ingredients
   (verify by walking, one step below): the last record bit '1' + the
   post-record bytes `AD AE 1B 00 …` + the stale ref_handle=1291 from
   the (8.0.0) owner resolution at the moment of the relative-garbage
   pull. The model's pab dependency=1293 is REAL (that slot exists).
7. **The normalizer fabricates the failure**: the
   ASSOCPLANESURFACEACTIONBODY branch (~line 4850,
   `normalize_silver.py`) hard-emits `assocdep=[0,0]` + `pbsab_status=0`
   — which matches gold's TRUNCATED orig print and mismatches gold_rt's
   real 1291/128. Cure = project the model fields instead.

#### D. The fix (three edits, surgical)

1. READER BOUNDS — `src/io/dwg/dwg_stream_readers/merged_reader.rs` +
   `object_reader/mod.rs` + `object_reader/associative.rs`:
   - Thread the record's data byte-size (already in scope in
     `read_record_at`) into `DwgMergedReader` (e.g.
     `handle_remaining_bits()` mirroring `main_remaining_bits()`, or an
     explicit record-end position).
   - In `read_surface_body` (~:202, the `dependency: handle(reader)`
     pull) and `read_surface_action` (~:243, `path_status =
     reader.read_bit_long()` plus the class_version/option tails): when
     the cursor is at/past the true record end, return the gold-parity
     forms (Handle NULL / BL 0 / field defaults) instead of reading
     section bytes. Guards can never cut a real read — on full wires
     (rt, other action-body records) the cursor sits inside the record.
2. NORMALIZER PROJECTION — `normalize_silver.py` SurfaceActionBody arm:
   `fields["assocdep"] = normalize_handle_value(surface_body.dependency)`
   (NULL prints the null-pair form, matching gold's [0,0] via the
   null-pair convention) and
   `fields["pbsab_status"] = int(path_status)`.
   (Check the branch serves all SurfaceActionBody kinds — Extend/Loft/
   etc. share these tails; with the reader clamp they are all
   gold-parity.)
3. WRITER CHECK — `object_writer/associative.rs`: verify the NULL
   dependency serializes as the null handle form (no panic, code-5-null
   like gold's own overflow print). Behavior change not expected.

#### E. Step plan

1. One measurement to confirm truth 6 (15 min): re-run
   `pk19_55_surf_dossier.sh` (or `pk19_52/pk19_53/pk19_54`), then
   hand-walk silver's exact read order (associative.rs
   read_parameter_body / read_surface_body / read_surface_action) over
   the dumped bytes with the pk19_29_lpcwalk2.py MSB-first cursor class,
   tracking its main/handle positions: the sab-dep pull should land at
   handle-position ≈ record-bit 183 (one bit from the end) and the
   path-status BL read just past the data end — pin which bytes form
   1291/128 (leading candidate: `AD AE 1B …` + ref-relative resolution).
   If the positions contradict the overread story, stop and re-document
   (but gold's own overflow ERRORs in the orig trace already prove the
   truncation side; only the garbage SOURCE is unmeasured).
2. Implement D1+D2 (D3 verify); `cargo build --features serde --bins`.
3. Fresh per-file verification matrix (the reader touches associative.rs
   only, but re-run every assoc-bearing file): 2004/Surface (expect
   0/0 both pairs), example_2000/2004/2007/2010/2013/2018 (assoc
   networks), 2018/LiveSection1, 2018/Dynblocks, 2010/gh209_1,
   2000/TS1, 2000/PolyLine2D, the PolyLine3D stems.
4. Deep gates: `cargo test --features serde` (roundtrip 97/0, 47
   segments — no new model fields are expected, so no new
   normalize_entity_for_comparison arms should be needed) +
   `cargo test --features gold-harness --test gold_roundtrip`.
5. Corpus LAST (`pk17r_corpus.sh` detached + one bounded `24_wait.sh`),
   re-dump residues (`pk18a_all_rows.py`), commit
   `fix(harness): Surface ASSOCPLANESURFACEACTIONBODY zeroed — ...`
   + before→after counts, push, fold the docs.

#### F. Time-box

It is 2 rows and the dossier is complete — budget 2-3 hours total.
If a contradiction emerges in step E1 that invalidates the overread
theory, document with the byte evidence and re-halt.

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
embedded quotes AND pipes (regex `\|` alternations die silently);
single search terms through wsl.exe, multi-pattern via the grep *tool*;
HEREDOCS via wsl.exe -c BREAK — write probe python to script files with
the write tool, run via their absolute paths. This PowerShell has NO
`head` and rejects `&&`, and it also INTERPOLATES `$var` inside
double-quoted bash -c strings — loops with variables go in script files,
never inline. Multi-pattern grep through wsl.exe needs the grep *tool*
instead. The `read` tool's `offset` is ignored on SOME UNC paths — use
`wsl.exe -- sed -n <start>,<end>p <file>` (no quotes needed) and the grep
tool for multi-pattern searches. CRITICAL paths: the example_*.dwg files
live at the test-data ROOT (`$GOLD_TESTDATA/example_2010.dwg`); PolyLine3D/
Helix/Constraints live IN the version folders; PolyLine2D/TS1 in 2000/;
Underlay+Surface in 2004/; LiveSection1 in 2018/; gh109_1 in 2013/;
gh209_1 in 2010/. dwgread exit 1 + empty output usually means a wrong
path, not a gold failure. Corpus launch: `target/probes/pk17r_corpus.sh`
(nohup, ABSOLUTE log path, sleep 8, pgrep confirm) + bounded
`24_wait.sh`; NEVER edit while the corpus runs (give it the full time it
needs; a second corpus can race the report).)

## Workflow (per packet)

1. Re-read the fresh report first (staleness rule).
2. Grep the gold spec: dwg.spec + dwg2.spec (+ common_entity_data.spec,
   common_entity_handle_data.spec, spec.h for flag semantics) — read the
   FULL block (macro + version predicate + value guards) before any
   retype; check §8.1.1 liveness (a typed gold record in the diff PROVES
   liveness).
3. Locate the silver side; pull row VALUES + both records from fresh
   per-file runs into a fresh dir (use `target/probes/pk19_15_run_any.sh
   <relpath>`; the pooled corpus dirs are stale for fixed families but
   valid for still-open ones; the residue dump pk18_residues_full.txt is
   the quick reference).
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
8. Gates: `cargo test --features serde` (47 ok segments; roundtrip 97/0 —
   the deep tests have a KNOWN-ISSUE BUDGET: `dwg_roundtrip_deep_r2000/
   r2013/r2018` and `dwg_double_roundtrip_stability` assert
   `diffs <= max_known` (1 for the unresolved Shape-name known issue);
   a NEW raw-retention model field MUST get a normalize_entity_for_
   comparison arm or the budget trips — the failing test names the exact
   field) + `cargo test --features gold-harness --test gold_roundtrip`
   (ok).
9. Commit `fix(harness): <packet> — <gold spec ref> + before→after
   counts`, push. No backticks in commit-message bodies (bash command
   substitution). If a semantic rust test encoded the OLD wire theory,
   update the test WITH the spec citation.

## Hard-won lessons (each one cost rows — do not repeat)

- **dwg2json/dwgread write `<stem>.json` beside the INPUT FILE by
  default** — always redirect or you WRITE INTO THE READ-ONLY GOLD TREE.
- **Write rows = rt-parser-parity pair (gold_rt vs silver_rt); read
  rows = orig pair; families can be one-sided** — Surface's ACTIONBODY
  passes orig and fails rt; one file's gold values can DIFFER between
  orig and rt reads of different wires (read-pair first, then the pair
  you fix against).
- **By-type tables truncate; per_file (FULL paths) is truth.** The
  multi-version stems (Helix/Constraints) share ONE corpus workdir —
  the pooled diff files there hold whichever version ran last; use
  per-file fresh runs for those.
- **The entity-common flag pair order is [ltype BB, plotstyle BB,
  R2007: material BB + shadow RC]** (common_entity_data.spec 507-522);
  handle-pull order is ltype, material, shadow, plotstyle
  (common_entity_handle_data.spec 127-141).
- **RAW beats recomposition**: retain the wire's raw values (dataflags
  byte, LwPolyline flag, per-SEQEND common flags, encr SAT blocks, OLE
  blob, polyline kid wire handles, mesh chain ends, vport header slots,
  RAPIDRT's garbage come read-order) — gold prints them verbatim and any
  value-based recomposition will differ.
- **Gold-bug parity IS the truth** (RAPIDRT garbage is a one-bit-cursor
  misparse; the spec block beats intent; the differ compares gold's
  OUTPUT, not the "correct" decode).
- **`spec.h` VERSION(v) is an EQUALITY check, VERSIONS(v1,v2) a range**
  — "R2013 behavior" in gold's spec often means *exactly* AC1027, NOT
  R2013+ (the RAPIDRT mis-order applies ONLY at AC1027; at R2018 gold
  parses cleanly). Gate rust shadows with the same equality.
- **gold's handle/BL printing**: BL prints through FORMAT_BL "%u"
  (values > 0x7fffffff are LARGE POSITIVES); handle tuples keep their
  raw code/size/absref through normalize_gold (the VS-code-style
  `__handle_code__`/`__handle_target__` convention; the DIFFER compares
  resolved targets, codes are display-only).
- **R2000 object records start with a 2-byte little-endian size, then
  [BS type][RL bitsize][H handle][EED...]** — the v9 trace's `Address`
  points AT the type (bit 0 of the walk is the type's first bit; the
  RL's value = the main-data bit-width = the handle-stream start;
  `hdl_dat: @n.m` markers confirm). The obj dat spans
  [MS-after-2B-size .. +size bytes] with the CRC at the end —
  hand-walk with an MSB-first cursor, RS/RL/RD byte-wise little-endian.
- **Class entities (≥500, "Extended"/ClassObject wrappers) flow through
  the SAME entity preface** — including the entity PREVIEW block
  (common_entity_data.spec: preview_exists B + RL/BLL size + bytes,
  consumed via silver's has_graphic path). rebuild_block_membership
  used to force their non-block owners into Model_Space (the
  LAYOUTPRINTCONFIG/chain root — batch 42c).
- **Branch placement in the entity loop matters**: pop-branches before
  the generic field loop; stashed per-record payload keys must be
  popped at merge time or they leak through every generic loop.
- **normalize_gold reinterprets a 4-int list as the raw handle tuple
  [code, size, value, absref]** — mirror that when gold prints short
  int vectors.
- **Fabricated constant handle codes are time bombs** (WIPEOUT);
  retain the wire slot when gold reads it directly (VIEWPORT.
  vport_entity_header precedent: the vx-table-lookup fabrication broke
  the rt pair on the writer's echo).
- **Typing divergence poisons handle-vector resolution far away**
  (a synthesized kid that steals an existing record's handle flips
  every resolution of that handle — the PolyLine2D LINE@512 root).
- **Entity-common serde-skipped fields ride `_common_dwg` into
  merge_common — pop from `fields` AFTER the merge**.
- **Bitflags serde joins with " | "** (split it); FIELD_CAST BS→BL
  zero-extends (0xFFCE→65486); MATERIAL rgb unsigned; wire codes
  SOLID 31 vs TRACE 32; ACIS banner split fixed-at-15 ("%.*s").
- **Deduplication design decisions in the MODEL can silently drop wire
  slots** (SortEntitiesTable.add_entry folded four dead pairs;
  whenever gold keeps repeated wire elements, wire reads append
  verbatim — add_wire_entry precedent).
- **Silver object payloads nest common under `common` inconsistently** —
  location-aware extraction or records vanish.
- **The DWG binary wire cannot carry a semantic the format lacks**
  (constraint-group registry/class data is DXF-side) — gate by wire era.
- **Never edit mid-corpus; never busy-poll; verify every touched version
  folder; git-commit each wave so a regression is one revert away.**

## The commit / push convention

- Branch `gold-vs-silver`, push to `origin/gold-vs-silver` after each
  batch. `fix(harness): <packet> — <gold spec ref> + before→after
  counts` (per-wave when families share a mechanism), then a separate
  `docs(harness): …` commit once §7/§8.1.6 are updated.
- Landed 2026-09-20: morning `fa2cb0a..b2955a7` (batches 7-23),
  `82f0225` (24-32), `078c119` (33-38), `5a25bf9` (39), `c20e6fe` (40),
  docs `fe23963`; late-night `707e7a8` (41), `604f956` (42), `e0c6f93`
  (43), docs third fold `e088f33`; the Surface dossier fold (this
  commit) adds the decoded-forensic route — no code change.
- The remaining inventory after each landed batch MUST be re-dumped
  (pk18a_all_rows.py) and this file re-checked against it before the
  next halt.
