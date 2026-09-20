# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target
(2026-09-20, raised) is read AND write 0 on BOTH sides. Current baseline
(2026-09-20 late-night halt, HEAD `e0c6f93`):

**read 0 / write 2 — 123 of the 124 corpus files are at 0/0.**

gh44-error.dwg stays explicitly out of scope via `run_corpus.in_scope_files`.
The ONLY remaining rows live in **one file** (2004/Surface.dwg, 2 write
rows, rt-pair-only) and are a TIME-BOXED RESIDUAL — see the route below.
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
   `pk19_*` (this session: RAPIDRT theory verifier `pk19_07_theory.py`,
   LPC bit-walker `pk19_29_lpcwalk2.py`, generic fresh-run
   `pk19_15_run_any.sh <relpath>`, gates `pk19_13*`).
4. `target/probes/pk18_residues_full.txt` — the (now 2-row) residue list.

## The route to zero — the single remaining packet

### 2004/Surface.dwg — 0 read / 2 write (rt only, time-boxed residual)

`ASSOCPLANESURFACEACTIONBODY.assocdep` + `.pbsab_status`: gold_rt resolves
{5 → ASSOCACTION 1291} and pbsab_status 128 from **silver's own rewrite**,
while silver_rt's normalizer emits the [0,0]/0 null form (the orig pair
passes: gold_orig prints [0,0]/0).

The root is in the **embedded struct handle pulls** of the
AcDbAssocPathBasedSurfaceActionBody macro (dwg2.spec ~1847-1960):
- `AcDbAssocParamBasedActionBody_fields(pab)` PRE (R_2013b): version BL,
  minor BL, num_deps BL, SUB_HANDLE_VECTOR deps, l4 BL, num_values BL,
  and when num_values==0: SUB_FIELD_BL l5 + `SUB_FIELD_HANDLE (pab,
  assocdep, 5, 330)`.
- `AcDbAssocSurfaceActionBody_fields(sab)`: version BL,
  `SUB_FIELD_HANDLE (sab, assocdep, 5, 330)`, is_semi_assoc B, l2 BL,
  is_semi_ovr B, grip_status BS.
- Then `FIELD_BL (pbsab_status, 90)` — the top-level field.

**Both embedded slots are literally named `assocdep`** and flatten to ONE
gold JSON key. Gold's orig print of [0,0] means the wire's printed slot
is null there; the RT wire (silver-written) carries 1291 in whatever slot
gold reads — i.e., silver's writer and reader disagree with gold AND with
each other about WHERE that handle lives on this family. pbsab_status
follows the same story (silver's model `path_status`=128 is the payload's
semantic value, but gold prints 0 on orig / 128 on rt — again pair-flip).

The treatment that cracked the LAYOUTPRINTCONFIG preview block applies
here (see IMPLEMENTATION.md §8.1.6 batch-41/42 entries + the probes):
1. Dump the record's bits on BOTH files (gold trace §8.1.0 flow: the
   record for handle 1292 in 2004/Surface.dwg — orig AND the silver
   rewrite rt file) via dump_section_bytes + a python hand-walk
   (the `pk19_29_lpcwalk2.py` cursor class is reusable as-is).
2. Walk gold's decode order (SUB_HANDLE_VECTOR pab.deps from the handle
   stream, then pab.assocdep, then sab.assocdep after the sab B/BL/BS
   fields) and silver's `read_parameter_body`/`read_surface_body`
   (`associative.rs:157-190`) pull sequence SLOT BY SLOT on the same
   bits. Find where they diverge (silver's parameter_body "dependency"
   reads 1293, its surface_body "dependency" reads 1291 on BOTH pairs of
   files — neither is gold's printed slot).
3. Retain the slot gold prints (as its own model field), echo it in the
   CLASS writer (`object_writer/associative.rs`), and emit it in
   normalize_silver's ASSOCPLANESURFACEACTIONBODY branch (the current
   "assocdep=[0,0]" fabrication site) — plus pbsab_status the same way.
4. TIME-BOX reminder: it is 2 rows. If the embedded-slot truth turns out
   to be gold-unfixable within ~2 hours, re-accept as residual and
   document with the specific bit evidence.

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
  (43), docs `fe23963`-successor (this fold) + this file's docs commit.
- The remaining inventory after each landed batch MUST be re-dumped
  (pk18a_all_rows.py) and this file re-checked against it before the
  next halt.
