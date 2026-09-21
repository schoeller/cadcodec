# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

The acadrust gold-vs-silver roundtrip campaign is COMPLETE. The target
(2026-09-20, raised: read AND write 0 on BOTH sides) was reached
2026-09-21 at batch 44 (`9b1738c`; docs fold on top):

**read 0 / write 0 — ALL 124 of the 124 corpus files are at 0/0.
Residue dump empty (`target/probes/pk18_residues_full.txt`).**

gh44-error.dwg stays explicitly out of scope via `run_corpus.in_scope_files`
(the frozen `246e60a` audit decision). The work queue (IMPLEMENTATION.md
§8.1.6) is EMPTY. A fresh session therefore has exactly ONE job:

**Re-verify the standing 0/0, and treat any row that resurfaced (e.g. after
an unrelated codec change) with the per-packet workflow in IMPLEMENTATION.md
§8.1.** There is no outstanding pocket; do not invent work beyond the
verification pass unless a concrete row exists.

**Session history (2026-09-20):** morning batches 7-23 (`fa2cb0a..b2955a7`);
evening batches 24-32 (`82f0225`), 33-38 (`078c119`), 39 (`5a25bf9`), 40
(`c20e6fe`); late-night 41 (`707e7a8`, gh109_1), 42 (`604f956`, chain-ordinal
wave), 43 (`e0c6f93`, deep-gate arms), docs folds `fe23963`/`e088f33` +
the dossier fold `33d5a0e`. Session total read 38 → 0, write 30 → 2.

**Session history (2026-09-21):** batch 44 (`9b1738c`, the Surface
zero-out — the last pocket, from the decoded dossier; read 0/write 2 →
0/0; docs fold on top). The campaign-closing recipe and the one
measured refinement of the dossier are in §7 and the §8.1.6a DONE entry.

**Staleness rule:** re-read `target/gold_harness_corpus/report.json`
(`read_fidelity_total`, `write_fidelity_total`, and `per_file` — entry
keys are file/returncode/read_fidelity_diffs/write_fidelity_diffs; the
by-type tables truncate, per_file is truth) FIRST; it must still say 0/0
with no per-file nonzero rows. After every landed change, re-run and
re-dump residues (`python3 target/probes/pk18a_all_rows.py`).

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec` **plus `common_entity_data.spec` and
   `common_entity_handle_data.spec`** (the common flag pairs), and
   `spec.h` (flag-bit names AND the VERSION/VERSIONS macro semantics);
   verify class-block liveness (§8.1.1) before any retype;
   version-gate every conditional; differ/ignore-list frozen; commit
   conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — §7 (the campaign-closing
   chain), §8.1.0, §8.1.1, §8.1.6 (the queue banner records the
   complete state), §8.1.6a (batches 7-44 DONE recipes).
3. `target/probes/` — the probe library: `pk16a/b/c` (census/key-maps),
   `pk17*` (family probes, `pk17e_rows.py <workdir>` row lists,
   `pk17r_corpus.sh` detached corpus launcher), `pk19_*` (verification
   waves; the Surface dossier set `pk19_42_surf.py` / `pk19_52_53_54`
   regenerable via `pk19_55_surf_dossier.sh`; fresh-run
   `pk19_15_run_any.sh <relpath>`; deep gates `pk19_13*`),
   `pk18a_all_rows.py` (residue dump — currently EMPTY).
4. `target/probes/pk18_residues_full.txt` — must be 0 lines; if not,
   that list IS the work queue.

## The standing verification pass (what "complete" means)

1. Fresh report: `report.json` totals 0/0, per_file all-zero.
2. `python3 tests/gold_harness/check_env.py` → "Environment looks good".
3. `cargo build --features serde --bins` → success.
4. Deep gates: `cargo test --features serde` → 47 ok segments
   (roundtrip 97/0, 1312 units; the deep tests carry a KNOWN-ISSUE
   BUDGET: `dwg_roundtrip_deep_r2000/r2013/r2018` and
   `dwg_double_roundtrip_stability` assert `diffs <= max_known`; a NEW
   raw-retention model field MUST get a `normalize_entity_for_
   comparison` arm or the budget trips — the failing test names the
   exact field) + `cargo test --features gold-harness --test
   gold_roundtrip` → ok.
5. Corpus (`pk17r_corpus.sh` detached + one bounded `24_wait.sh`) →
   read 0 / write 0 across the 124 in-scope files.

If all five hold, the session's task is verification bookkeeping only
(no commit is needed for a clean re-run). If a row resurfaced, STOP the
patrol and open a packet: the row's `(type, field)` + per-file value
probes via `pk19_15_run_any.sh`, gold spec block, then the §8.1.4 fix
recipe. Never "fix" a row by touching `diff_fields.py` /
`ignore_fields.toml`.

## Known out-of-scope items (do NOT reopen without user direction)

- `2013/gh44-error.dwg` — frozen exclusion (upstream-crash file; the
  `-nan` shim once re-included it at 7689/7559 rows).
- The §7 "Write-fidelity diff compares silver_rt" architectural note
  (`run_roundtrip.py` builds diff_rt = gold_rt vs silver_rt rather than
  the §3-documented gold_orig vs gold_rt) — harness design decision,
  recorded in §7's Known-issues table.
- Plain `cargo test` failing to compile `examples/entity_atlas.rs`
  (pre-existing E0432, serde-feature-gated example; `cargo test
  --features serde` is the authoritative gate).
- The R13/R14 example files (`example_r13/r14*`) — out-of-scope format
  versions, excluded by `run_corpus.in_scope_files`.
- The untracked `examples/cylinder_dwg.rs` + `*.ocs.lock` in the tree
  belong to other workstreams; leave them alone.

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

## Workflow (per packet — only if a row resurfaced)

1. Re-read the fresh report first (staleness rule).
2. Grep the gold spec: dwg.spec + dwg2.spec (+ common_entity_data.spec,
   common_entity_handle_data.spec, spec.h for flag semantics) — read the
   FULL block (macro + version predicate + value guards) before any
   retype; check §8.1.1 liveness (a typed gold record in the diff PROVES
   liveness).
3. Locate the silver side; pull row VALUES + both records from fresh
   per-file runs into a fresh dir (use `target/probes/pk19_15_run_any.sh
   <relpath>`; the residue dump pk18_residues_full.txt is the quick
   reference).
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
8. Gates: `cargo test --features serde` (47 ok segments; roundtrip 97/0)
   + `cargo test --features gold-harness --test gold_roundtrip` (ok).
9. Commit `fix(harness): <packet> — <gold spec ref> + before→after
   counts`, push. No backticks in commit-message bodies (bash command
   substitution). If a semantic rust test encoded the OLD wire theory,
   update the test WITH the spec citation.

## Hard-won lessons (each one cost rows — do not repeat)

- **dwg2json/dwgread write `<stem>.json` beside the INPUT FILE by
  default** — always redirect or you WRITE INTO THE READ-ONLY GOLD TREE.
- **Write rows = rt-parser-parity pair (gold_rt vs silver_rt); read
  rows = orig pair; families can be one-sided** — one file's gold values
  can DIFFER between orig and rt reads of different wires (read-pair
  first, then the pair you fix against).
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
  `hdl_dat: @n.m` markers confirm; the trace's main-dat anchors are
  END-of-read positions, MS-inclusive coordinates). The obj dat spans
  [MS-after-2B-size .. +size bytes] with the CRC at the end — hand-walk
  with an MSB-first cursor, RS/RL/RD byte-wise little-endian.
- **Gold's overflow-null and valid-null prints DIFFER**: a read REFUSED
  at the dat end prints the [0,0] null pair (bit_read_RC overflow), but
  an EXPLICIT (5,0) null-form slot READ VALIDLY prints the full
  [5,0,0,0] handle tuple — a spectrum that cost the Surface batch 44 a
  verification cycle (the writer now OMITS the absent slot instead of
  fabricating a (5,0) form).
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
- **Fabricated constant handle codes are time bombs** (WIPEOUT); retain
  the wire slot when gold reads it directly (VIEWPORT.vport_entity_
  header precedent) and OMIT a slot the wire never carried (Surface
  batch 44's null-sab echo).
- **Both silver stream cursors are bounded by the SAME record slice**
  (`read_record_at` hands the merged reader exactly the MS size bytes);
  overread garbage comes from the zero-fill window that OVERLAPS the
  last real bits, not from bytes past the record. The poison window of
  2004/Surface was `[bit 183..191)`: the record's final bit `1` made
  both the sab handle form byte (0x80 → code 8 → ref−1 = 1291) and
  pbsab_status's RC (0x80 = 128).
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
- Landed 2026-09-20: `fa2cb0a..b2955a7` (7-23), `82f0225` (24-32),
  `078c119` (33-38), `5a25bf9` (39), `c20e6fe` (40), `707e7a8` (41),
  `604f956` (42), `e0c6f93` (43), docs `fe23963`/`e088f33`/`33d5a0e`.
- Landed 2026-09-21: `9b1738c` (44, the Surface zero-out — campaign
  complete) + this docs fold on top.
- If a future session lands new batches, re-dump the residue inventory
  (pk18a_all_rows.py) at every halt and reconcile this file against it.
