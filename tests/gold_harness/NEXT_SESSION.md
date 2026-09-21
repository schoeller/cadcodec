# Zero-context prompt — BricsCAD strict-load campaign (next session)

> Paste this whole file into a fresh session to continue the strict-load
> campaign with no prior context. It is the cold-start brief. Replace this
> file at the next halt (fold landed outcomes into IMPLEMENTATION.md first).
> After reading this file, read in order: `tests/gold_harness/AGENTS.md`
> (durable rules), then `tests/gold_harness/IMPLEMENTATION.md` §7 and §18.

## Task

The **strict-load zero target**: `cargo run --example
gen_all_entities_all_versions_dwg` produces `gen_all_entities_all_versions.dwg`
(AC1032/R2018, 30 entity types). That file must open in **BricsCAD** on the
USER's machine via plain `_open` (not RECOVER) with **no modal error, no
command-line warnings, and 30 visible entities**.

Current state (halt 2026-09-21 ~14:00Z):

- 28 of 29 entities visible in the mleader-omitted file; the LEADER parses
  but is dropped at deep-load with a bare warning.
- The MULTILEADER record is the only fatal blocker when present.
- Both remaining defects are fully scoped: silverWRITER encoding-form
  deltas (a few bits) against authored wires. The route to zero below is
  complete and needs no new content theories.

This campaign runs alongside the COMPLETED gold-vs-silver fidelity campaign
(0/0 on the 124-file corpus — section "Standing fidelity rules" below).
Preserving that 0/0 is a hard constraint on every writer change.

## BricsCAD message semantics (decoded — do not re-derive)

1. Modal `Unable to load drawing ... Object improperly read: <Class> (N)`
   = FATAL at the first unparseable object. **(N) is the object's handle
   in HEX** (proven by handle-shift experiments: adding an entity before
   the leader moved it 0x40→0x41 and the complaint followed the handle).
2. Bare `Object improperly read (N)` at the command line = NON-FATAL
   per-object warning: the record parsed, the entity gets dropped at
   deep-load. Identify the victim by the visible-entity count, not just
   the message.
3. RECOVER names entities with specific validation text and heals
   silently (`Total errors found during audit N, fixed M`).
4. **The stale-copy trap**: always confirm WHICH generation was tested.
   On 2026-09-21 the user once tested a stale copy — the mleader printed
   (50) where the fresh generation had (51). Cross-check the printed
   handle against the freshly generated file's actual handles (gold JSON
   query) before interpreting a result.
5. User observations arrive as pasted text: modal lines, bare warning
   lines, and visible-entity counts. Ask for the count when absent.

## What is fixed and user-validated (do not retest these)

1. **Region/BODY/3dSolid SAT topology** — the example's cylinder
   (`build_cylinder_sat`) keeps its correct coedge wiring and gained the
   missing back-pointers: every edge record points at one of its coedges
   (tokens[5]) and every vertex at an edge (tokens[1]).
   `build_region_sat` (new) builds a valid planar square sheet; BODY
   reuses the cylinder. Receipts: the earlier RECOVER texts ("shell not
   connected", "coedge's edge doesn't point to coedge", "edge without
   backptr", "vertex without edge", "Data stream is empty") are all GONE.
2. **Shape** — example adds a shape-file TextStyle ("LTYPESHP",
   font `ltypeshp.shx`, `is_shape_file = true`), `shape.shape_number =
   130`; writer-side `write_shape` resolves a null style handle by name
   against `doc.text_styles`. Receipts: "font file not set / shape number
   not set" GONE.
3. **MESH population bits** — model `blend_crease = false` (wire B72 =
   gold's `is_watertight`), `unknown_b1 = true` (authored census:
   2004/Surface.dwg MESH). Receipt: the bare `(4E)` on SubDMesh GONE —
   the mleader-omitted, leader-omitted file opened with **no
   errors/warnings** once. ⚠ DO NOT "fix" the mesh face-count header to
   the face count — the flattened-length convention is the authored
   truth (the corpus caught that regression at 8 rows and it was
   reverted).
4. **MLEADER text content style** — `write_multileader_annotation_context`
   falls back to the document's "Standard" text style when the content
   style handle is null. Necessary but not sufficient (the fatal remains).
5. **Leader model default** — `Leader::new()` creation_type =
   `NoAnnotation` (annot_type 3), so API-constructed leaders no longer
   claim WithText with a dangling null association.

## Where the remaining fault lives (the campaign's core finding)

**Silver's WRITER emits different bitcode FORMS than authored wires.**
Both local decoders (LibreDWG gold and silver) tolerate either form, so
the fidelity harness stays 0/0 — but a strict consumer (BricsCAD)
validates forms. Proof chain:

- The envelope lab (`examples/xleader_lab.rs`) loaded an authored file
  known to warn, re-wrote it with silver, and appended one constructed
  leader: the output still warned on the **authored-content** leader
  (0x72E) as well as the appended one, and the mleader (732) stayed
  fatal → the fault travels with silver's ENCODING, not the content.
- The earlier "(40) fatal → (41) warning" progression was real progress
  but every content theory after that failed (see FALSE LEADS): the
  content class is now byte-complete; the residual is encoding form.

## The two open defects, precisely scoped

### LEADER — warn-class (bare `(41)`), record drops at deep-load

Pair method: authored `2018/Leader.dwg` object 145 = handle 0x72E
(frame: `Size: 240 [MS], Hdlsize: 0x6A [UMC], Type: 45 [BOT], Address:
4916`) vs silver's rewrite (`Size: 241, Hdlsize: 0x6C, Address: 1968`).
Accounting: auth 240 bytes vs rt 241; hdl 0x6A vs 0x6C (+2 bits); main
≈ +6 bits. Byte-compare results (record data = [Address+1 ...]):

- Byte-identical through the EED payload (73-byte DSTYLE + 41-byte
  AnnotativeData) and again through the common entity data.
- Divergence set: (a) the CMC alpha nibble at record-data-bit **1050**
  (auth `0x2000056` type 2 vs rt `0x3000056` type 3 — silver's
  `to_alpha_value` currently writes the 3-form; the authored uses 2);
  (b) the tail bits `[1812..1894]` — raw bytes:
  auth `... 21 00 c8 1e 01 44 41 48 1d e5 48 1c`
  rt   `... 21 00 c3 20 78 05 11 05 20 77 95 20 73`
- Tail field layout (validated by anchors; `@n.m` = MS bit 8n+m, most
  prints are END-of-read positions): box_height 0.0 raw-64 (66 bits),
  box_width −0.09 raw-64, hookline_dir B, arrowhead_on B, arrowhead_type
  BS 322 = `'00'+RS16` (18 bits), unknown_bit_4/5. Handle slots have
  IDENTICAL forms in both files: [xdic (3.2.780)][layer (5.1.10)]
  [ltype (5.2.779)][assoc (5.2.731)][dimstyle (5.1.E1)].
- ⚠ One open anomaly: the −0.09 raw-double bit pattern was NOT FOUND in
  the sliced dump (search bug or wrong slice base — verify the slice
  before trusting any derived bit offsets). Re-anchor by finding the
  f64 bit patterns of the box values first.
- CRC: auth `82F5` over [4913..5156], rt `55E4` over [1965..2209].

### MULTILEADER — the only FATAL (`AcDbMLeader (N)`)

Pair: the same authored file's MULTILEADER record (833 bytes at section
Address 5283, object 147) vs silver's rewrite (831 bytes, Address 2336;
MS at 2333 → `[MS 2][UMC 1][BOT 1][data from Address+1]` — verified on
both records, e.g. auth MTEXT `[..] 0.2.731`). Values decode IDENTICALLY
under gold; the net delta = **−17 main bits**, all inside the final
~180-bit tail, first divergent bit = record-data-bit **6367** (values
match before it). Suspected decomposition: two 9-valued BS fields
emitted as `'01'+RC` (10 bits each) where the authored wire uses
`'00'+RS16` (18) = −16, plus 1 bit elsewhere. Candidates: the BS-9 pair
(ctx.text_top/text_bottom — both are 9) and the attach trio
(dir 271/top 273/bottom 272), spec `dwg2.spec:1449-1451` + the
`MLEADER_CONTEXT_DATA_fields` macro at `dwg2.spec:1227`, entity block at
`dwg2.spec:1298`. R2010+ record tail layout: `[main...][RS data_size
16][flag bit 1][string stream (data_size bytes)][handle region
(hdlsize)][CRC 2]`; TU strings live in the stream and consume ZERO main
bits; handles read at their own positions.

## FALSE LEADS — all tested and disproven, do not repeat

Each cost a user round-trip on 2026-09-21:

- annotation class: WithText+null-assoc vs NoAnnotation vs
  WithText+real-MTEXT-assoc — ALL still warn.
- EED: none vs AnnotativeData vs DSTYLE+AnnotativeData (bytes transcribed
  from the authored leader with the embedded masked-RLL handle reference
  repointed 0x77A→0x40) — ALL still warn. (The transcription remains in
  the example as `const DSTYLE_EED` with `#[allow(dead_code)]`.)
- population bits (hookline_dir=1, unknown_bit_4=1), 3-point geometry,
  spline path, arrowhead_type 322, box 0/−0.09 — collectively
  insufficient.
- named linetype (ACAD_ISO02W100): its constructed table record is an
  empty shell (no dashes) and named-reference resolution deep-loads the
  table record — leader went back to Continuous; still warns (so this
  was not the cause either, but keep Continuous to avoid table-record
  dependencies).
- DIMSTYLE "Annotative" vs "Standard" — both still warn.
- Extension dictionary (`doc.ensure_extension_dictionary(leader_handle)`)
  — still warns. (Witness: gold JSON `is_xdic_missing 0`, slot
  `[3,1,66,66]`, DICTIONARY object 0x42 owned by the leader.)
- **Mesh face-count header** — WRONG, reverted; the corpus caught it.
- Interpreting `(N)` as anything other than a hex handle; interpreting
  the bare warning line as a fatal.

## Route to zero (step plan)

1. **Tree state at this halt (committed, pushed)**: the strict-load
   campaign's validated work landed as `30218c3`
   (fix(dwg): strict-consumer compatibility — code + examples) and
   `6f485f9` (test(harness): oracle-optional gold_roundtrip +
   bootstrap), with the docs fold in the docs commit carrying this file.
   The fidelity corpus was re-verified 0/0 on this exact tree before
   committing. Nothing is outstanding in the working tree — start
   straight at step 2.
2. **Regenerate the pair artifacts** — everything below lived in /tmp
   (volatile). Authored trace:
   `"$GOLD_DWGREAD" -v9 "$GOLD_TESTDATA/2018/Leader.dwg" > /tmp/l18a_full.log`
   Silver rewrite: `bash target/probes/pk19_15_run_any.sh 2018/Leader.dwg`
   → `target/probes/pk19_Leader/Leader_rt.dwg` (the repo-root copy
   `gen_all_rewrite_authored_2018_leader.dwg` is that file for user-side
   UNC access); trace it the same way. Record dumps:
   `target/debug/dump_section_bytes <file> <start> <len>` (R2000+ frame =
   [MS 2 @Address−4][UMC 1 @Address−2][BOT 1 @Address][data @Address+1]
   [CRC 2]; dump [Address−6, +size+12] for margin). The compare-loop
   python probes live in `target/probes/` (pk211_firstdiv.sh,
   pk230_lddiff.sh, pk233/234 — locally persisted, not in git).
3. **Leader walk**: re-anchor via the box-value f64 bit patterns
   (resolve the not-found anomaly), then walk the tail per spec
   (`dwg.spec` LEADER block, unknown bits at SINCE(R_2000b)) and name
   which fields' forms differ; the alpha nibble fixes itself when the
   record matches (auth = type 2).
4. **Mleader walk**: same, using the corrected spec sequence (strings
   consume zero main bits; handles at their own positions). Expected
   outcome: the BS-9 pair (and/or the attach trio) named.
5. **Writer fix**: emit the authored byte-form in those fields
   (a raw-16 BS write for those positions —primitive or retained-form
   driven), keeping it surgical. The alpha form question settles toward
   authored (2) by byte-matching.
6. **THE LOCAL ORACLE LOOP (§18 layer 4)**: after each writer change,
   regenerate the rewrite of 2018/Leader.dwg and byte-compare BOTH the
   leader and mleader records against the authored file. Zero means
   byte-identical per record (handle slots that legitimately renumber
   compare by code/counter shape; CRC excepted). When byte-equal,
   BricsCAD acceptance follows by construction.
7. **Preserve the fidelity 0/0** after each writer change:
   `cargo build --features serde --bins` → `cargo test --features serde`
   (47 ok segments, the gold_roundtrip oracle-optional semantics are now
   skip-mode) → corpus detached + one bounded `24_wait.sh` → residues
   empty. Parser parity is form-blind, so the 0/0 must survive every
   form fix — if it does not, the fix changed values, not just forms.
8. **Regenerate + user verification**: all three GENALL files
   (canonical; `GENALL_MLEADER_MODE=skip` variant; the
   leader+mleader-omitted control — that one previously opened with zero
   errors/warnings). Hand to the user with the handle table of the fresh
   generation (defeats the stale-copy trap) and iterate. Then fold the
   close-out into IMPLEMENTATION.md and replace this file.

## Artifacts and tools on this machine

- `examples/gen_all_entities_all_versions_dwg.rs` — the generator;
  switches: `GENALL_LEADER_MODE=skip|annot|plain(default)`,
  `GENALL_MLEADER_MODE=skip`. Output at repo root:
  `gen_all_entities_all_versions.dwg` (all 30 — mleader fatal expected),
  `gen_all_all_but_mleader.dwg` (29 — leader `(41)` warn expected),
  `gen_all_no_leader_no_mleader.dwg` (28 — the strict-load CLEAN control
  to re-verify after every regen).
- `examples/xleader_lab.rs` — the envelope lab (load an accepted-context
  file, append one constructed leader, write out; framework for
  record-vs-envelope isolation).
- `target/debug/dump_section_bytes` — section-aware byte dumper
  (source `tests/gold_harness/src/bin/dump_section_bytes.rs`).
- Probe scripts under `target/probes/` (persisted but not in git; see
  their headers for regen inline equivalents): `pk19_15_run_any.sh`
  (fresh per-file harness run), `pk17r_corpus.sh` + `24_wait.sh` (corpus),
  `pk18a_all_rows.py` (residue dump), `pk19_59_gates.sh` (both cargo gates),
  `pk19_71/72/73` (dossier builders), `pk211/230/233/234` (record
  bit-compare patterns), `pk237_finalverify.sh` (oracle-optional matrix).
- Gold traces + JSON dumps: ALWAYS redirect (`dwgread` writes beside
  its INPUT otherwise — `-o /tmp/x.json` or `>`), never write into the
  read-only gold tree.

## Standing fidelity rules (from the completed 0/0 campaign)

- `tests/gold_harness/AGENTS.md` governs: gold is read-only;
  `diff_fields.py`/`ignore_fields.toml` frozen; version-gate every field
  by gold's exact predicate; never touch dispatch/CRC/section map.
- Baseline: corpus report `read_fidelity_total: 0` / `write_fidelity_total:
  0` (use `per_file`, never the truncating by-type tables) on 124 files;
  residues empty; `cargo test --features serde` 47 ok (roundtrip asserts
  `diffs <= max_known`); `gold_roundtrip` = oracle-optional skip-mode
  without LibreDWG (see README "Oracles" — the four validation layers).
- Oracle layering (README + IMPLEMENTATION.md §18): layers 1–3 = parser
  parity; layer 4 = the authored-wire byte-fidelity oracle that closes
  the form-blind spot — the strict-load campaign's own instrument.

## Environment (identical constraints carry over)

The repo lives in WSL; reach via
`\\wsl$\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`. Run shell
commands via `wsl.exe -d Ubuntu-24.04 -- bash <script>`: inline quotes
and pipes get stripped (single search terms only; multi-pattern via the
grep *tool*); heredocs via `wsl.exe -c` BREAK — write scripts with the
write tool, run by absolute path. PowerShell has no `head` and rejects
`&&`, and interpolates `$var` inside double-quoted `bash -c` strings.
The `read` tool's `offset` is unreliable on some UNC paths — use
`wsl.exe -- sed -n <a>,<b>p <file>`. For the user's BricsCAD tests: the
files open via `\\wsl.localhost\...` paths; always state the generation
(handles) with the handoff.

## Session history (2026-09-21)

- Fidelity campaign close-out (committed): `9b1738c` (batch 44, the
  Surface ASSOCPLANESURFACEACTIONBODY zero-out — corpus 0/0, campaign
  complete), docs `bf5fc39` + typo `a113e10`.
- Strict-load campaign (committed at this halt): `30218c`
  (fix(dwg): leader defaults, shape/mleader style resolution, mesh
  population bits, valid SAT topology, the example overhaul +
  xleader_lab), `6f485f9` (test(harness): oracle-optional
  gold_roundtrip + bootstrap_oracle.sh), and this docs fold
  (README oracles + IMPLEMENTATION §18 + this brief).
- Remaining open at this halt: the LEADER warn (~6+2 tail bits vs
  authored) and the MLEADER fatal (−17 tail bits). Everything else
  strict-loads.
