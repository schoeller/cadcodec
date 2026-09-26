# Zero-context prompt — the post-H7d halt: the write-target axis at 8,718 + the container-fix knowledge + the ObjFreeSpace/address queue

> Campaign state 2026-09-26 (the halt after the H7d row; the session
> ran the review → update → commit → push → continue loop from the
> H7b halt through three landings). **The ACS/SH campaign is COMPLETE
> at 0/0: the corpus stands at 280 files, read 0, write 0.** The §19
> structure READ axis is at ZERO gaps corpus-wide. The H7
> write-target axis is IN PROGRESS: **the review pass (H7a/H7b), the
> CLASSES landing (H7c), and the AppInfo/AppInfoHistory landing
> (H7d) all landed at 0/0 — the write-target key-gap fell
> 13,653 → 8,718.** The maintainer's fixture surface is EMPTY.
> Read `tests/gold_harness/AGENTS.md` first, then §F2.1–F2.3 +
> §18.5–18.7 in `IMPLEMENTATION.md` (§18.6 carries the full decode
> record), then §19.1–19.3 (the structure campaign — §19.2's H3 row
> carries the read landing + review, the H7 row carries
> H7a/H7b/H7c/H7d), then this file top to bottom.

## What this session established (the load-bearing facts)

**The H7a/H7b review pass (landed `0eec9e0`)**: the landed splice
held on the census-visible surface; three exactness gaps fixed
behind it. (1) The raw-only header handle slots re-emitted a
RECOMPUTED canonical form — they now re-emit the retained
`[code, size, value]` tuple verbatim (`write_handle_form`, the
`read_handle_raw` mirror; corpus-dead: every corpus header handle
is already the canonical code-5 minimal form —
`HardPointer.code() == 5`). (2) **The three undocumented trailing
slots after unknown_57 (BL, BL, B) were read-discarded and
re-written as 0/0/false — a LIVE census-blind corruption: 217 of
243 probed files carry nonzero values** (a constant `0xec99a4aa`
word + a per-file word on the R2004+ family; example_2004's tail
is `0/0/true`). Gold emits nothing there; the slots are now
retained (`unknown_tail_long1/long2/bit`, serde-skipped) and
spliced byte-exact. (3) **The SummaryInfo presence coupling**:
gold gates its JSON key on `summaryinfo_address != 0`
(out_json.c:2663); gh209_1 (AC1024, address 0, no section)
exposed a blind family on both axes — struct_axis now mirrors
gold's own gate, and both writers skip the section when the read
document's address was 0 and the model still holds the default
(a modified summary still writes — user intent wins). **The
census asymmetry pinned: the write-target key-gap counts
value_diffs + missing_gold_rt only; missing_gold (rt-extra)
leaves are a blind family by design** — presence-coupling rows
live there. Corpus: 13,653 → 13,656 (gh209_1's +3
id-coincidence, documented).

**H7c — the CLASSES landing (`a03c901`)**: the row was TWO
families with one root — the authored tables whose tail encoding
desyncs gold's walk (the AutoCAD-2027.1 fixture set) can only
round-trip byte-exactly (any re-encoding desyncs the walk
DIFFERENTLY — LoftC_2007's [10] went gold 2147673665 vs rt
587458113), and the classes whose instances re-emit through the
raw-object passthrough are OUTSIDE the write census
(`class_counts_complete=false` → 0 counts where the author wrote
1/3, with the zombie re-derivation marking live classes
zombie). The fix follows the AcDs precedent: the reader retains
the raw classes section bytes (`raw_classes_data`) + a state
hash (`raw_classes_fingerprint` — the ordered class identity
tuple + the document's per-class object census via the shared
`classes_state_fingerprint`, computed at the read capture and
again at the write gate); a same-version roundtrip with the
class table + census unchanged re-emits the author's bytes
verbatim (all three writer paths), anything else falls back to
the sane encoding. Corpus: CLASSES 60,954 @ 0/0; the key-gap
13,656 → 10,410.

**H7d — the AppInfo/AppInfoHistory landing (`d9ee081`)**: gold
prints both sections unconditionally on R2004+ (zeroed when
absent) — the rows were the static boilerplate vs the author's
content, the never-written AppInfoHistory, and the
absent-source boilerplate materialization. The fix: retain both
sections' raw bytes; verbatim on same-version roundtrips, skip
when the source had none, boilerplate for programmatic/conversion
documents. The AppInfoHistory hash for the AC21 section map
(`0x96de0737`, constant across the corpus) was extracted from the
author's files; the ac21 writer uses the author's single-page
align-0x80 form. **THREE CONTAINER BUGS found and fixed on the
way — load-bearing knowledge for every remaining row:**
(a) **the AC18 page header's 0x0C "page size - decompressed"
field must be the page's decompressed CAPACITY, not the stored
frame size** — gold's reassembly copies MIN(section-remaining,
page_size) per uncompressed page (decode.c:2236) and errors the
whole section when the bytes_left balance goes negative before
the last page; (b) **the AC21 encoding-1 (stored) pages are RAW
content + padding (the author's form), NOT any RS layout** —
gold picks its decode path by the page's physical size
(decode_r2007.c:854: the RS path iff page->size ==
`page_size_if_rs_coded(comp)` = align32(ceil(align8(comp)/251)×255))
and de-interleaves with stride ceil(align8(comp)/251) — a stored
page whose size lands on the RS form gets de-interleaved into
garbage; silver writes raw + a +0x20 collision guard for the
[225..248]-byte contents that would land on the 1-block form
0x100; (c) **the AC18 tail page must ALWAYS be written** — the
old all-zero-tail-page skip shorted sections whose content ends
in zeros below gold's `size ≤ num_pages × max_decomp` guard
(gh209_1's AppInfoHistory: 642 = 5×128 + 2 zero bytes). Corpus:
AppInfo 2,396 @ 0/0, AppInfoHistory 546 @ 0/0; the key-gap
10,410 → 8,718 (R2004_Header absorbed +313 id-coincidence from
the section-count changes; R2007_Header improved 978 → 966).

## The remaining H7 rows (8,718, the write-target axis)

ObjFreeSpace 2,453+30 (rebuilt content — the verbatim family: the
H4 read retains the `dwg_obj_free_space` summary; retain the raw
section bytes + the same presence/verbatim gate), R2004_Header
2,088 (the address/numsections family: silver writes its own
section set where the author's table carries id gaps — the fix
rewrites the author's section-info table), FILEHEADER 1,204
(address shifts + maint_rel 0→4), R2007_Header 966,
THUMBNAILIMAGE 442 (re-encoded — `preview.raw` is retained; the
row is ADDRESS-COUPLED: the container descriptors hold absolute
file offsets, so a byte-identical chain needs the section at the
original offset or gold-style address re-computation, which
itself changes the chain), the whole-section write drops
FileDepList 1,055 + SecondHeader 386 (R2000, lives inside
ObjFreeSpace), AuxHeader 94 — **the FileDepList/SecondHeader/
AuxHeader family belongs to a PARALLEL SESSION (their untracked
probe scripts `h7_probe1.sh`/`h7_rows.sh` sit in the repo root —
not ours to commit)**. The verbatim-re-emit family follows the
AcDs precedent (raw section bytes + a fingerprint gate; see
`acds_data`, `classes_section_data` in dwg_writer.rs for the two
landed patterns).

## The work: the three decoder walks (no new fixtures, interleaved per maintainer priority)

1. **The post-corner singles walk (sweep)**: the entries are
   CLASSIFIED (§18.7's Polysolid rows: the width single at bit
   1084, the record constant 4.00024414192312, the
   profile-derived 2.0109/@900/@1092, the path-derived segment
   end) but stay raw — extend `sh_tail_decode.rs` past the corner
   blocks with a proper BD walk and pin the spans.
2. **The loft container walk**: the raw-run reading is CLOSED
   (per-section `[center.x][center.y][height][radius]` runs + the
   `[π/2, π/2]` draft pair) but the model keeps `raw_doubles`
   positional — walk the inter-value regions so the per-section
   fields can be exposed as named model fields.
3. **The ExtrudeP polyline header**: the profile CALL kind 77
   body (length 544) holds the packed (x, y) vertex array; the
   grammar is ALREADY in-repo (`read_embedded_lwpolyline` in the
   object readers) — wire it into the CALL body decode.

**Dead / no-path rows (do not re-litigate)**: `LoftD` (no settings
path in the authoring release); the SH revolve option shorts +
flags through the REVOLVE command (the typed anchor is in-corpus
via RevolveM's bit-retained raw tail); **BREP stays deferred** —
only an external authentic `ACSH_BREP_CLASS` specimen re-opens it.

## The standing facts (the decode authority is §18.6)

- The four raw-retained SH tails decode to typed views with the
  captured bits as the write authority (the Phase B write rule:
  `render_*_tail` splices only differing same-form spans;
  untouched records re-emit bit-identically — pinned by the
  hermetic suite). The unknown-object records (the SURFACE twins,
  the ACSH node classes) re-emit verbatim through the raw
  passthrough arm.
- REVOLVE is fully closed (the CALL grammar); SWEEP/EXTRUSION
  through the spine + the profile CALL; LOFT through the
  per-section raw run. The hermetic cover is
  `tests/solid_history_tail_decode.rs` (15 tests) + the module
  tests in `sh_tail_decode.rs` — all run under gate 1.
- The un-quarantined C first attempts live as
  `ExtrudeCSurf_<v>`/`LoftCSurf_<v>` (their Solid re-authors
  kept the bare C names).
- The corpus workdirs are STEM-KEYED: 280 files collapse to 196
  unique stems (version-dir duplicates overwrite) — per-file
  aggregations from the workdirs are partial views; the
  report.json totals are authoritative.

## Environment (complete)

The repo lives in WSL. From Windows:
`\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`.
Shell commands run via
`wsl.exe -d Ubuntu-24.04 -- bash <script>` — write scripts with the
write tool and run by absolute path (PowerShell quoting caveats:
inline `&&`, `$var`, pipes, and multi-word grep alternations are
all broken; ONE COMMAND PER LINE in script files; `sleep` is
capped at 120 s — use the tracked background process for the
corpus).

```bash
# Environment (source this):
export PATH="$HOME/.cargo/bin:$PATH"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

## Verification gate (the zero-keeping rule applies to 0/0)

```bash
# 1. Build gates
cargo test --features serde          # 1587 passed / 0 failed at this halt
cargo test --features gold-harness --test gold_roundtrip

# 2. Family smokes (any sh_history fixture must stay 0/0)
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (must stay 280 files 0/0; read key-gap 0;
#    write-target key-gap 8,718 at this halt)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 byte-walk for any writer re-encode path
target/debug/dump_section_bytes <file> <A> <N>
```

## Commit inventory (this halt — all PUSHED through `d9ee081`)

```
d9ee081 fix(dwg): the AppInfo/AppInfoHistory verbatim sections — the H7d rows at zero (2,396 + 546 @ 0/0)   <- HEAD
a03c901 fix(dwg): the classes verbatim re-emit — the H7c CLASSES write-target row at zero (60,954 @ 0/0)
0eec9e0 fix(dwg): the H7a/H7b review pass — the raw handle forms, the trailing slots retained, the SummaryInfo presence coupling
91f81e0 docs(harness): the halt refresh — the H3 review + the H7a/H7b write landings, the 13,653 queue, the decoder walks
9314b08 fix(dwg): the summary write from the model — the H7b SummaryInfo write-target row at zero (4,352 @ 0/0)
... (the 2026-09-25/26 §19 arc below, oldest first: the plan-session
docs e1f75cd/0740827/bb73e72/3f490bd, the H0 axis skeleton + day-one
census d27c0c7 with the 15a4a01 review, the H2 header rows through
9e945fe + the 902eadc review, the H4 metadata rows 50c246d + the
745b7af review, the H5b CLASSES landing 5bbd79c, the H5c partial
35e3a9f, the H5a landing ea8e731, the H3 header landing e7ead8f + the
a5ecf95 review, the H7a header splice 788d6f0 — the corpus held 280
files at 0/0 through every commit)
```

**PUSH STATE (2026-09-26)**: the `gold-vs-silver` branch is PUSHED
through `d9ee081` (the remote tracks this halt's HEAD; push after
each landing per the maintainer's loop instruction:
`git push origin gold-vs-silver`).

**Session arc, for context**: the halt-state verification (the
corpus 280 @ 0/0 confirmed at 13,653) → the H7a/H7b review pass
(the CMC/SummaryInfo-grammar re-derivations held; the raw-handle
splice analysis found every corpus header handle canonical; the
trailing-slot sweep found the 217-file live corruption; the
gh209_1 presence probe found the blind family on both axes —
three fixes landed + the census-asymmetry doctrine pinned) → H7c
(the two-family CLASSES analysis: the desync tables + the
raw-object census gap; the AcDs-pattern verbatim gate with the
read/write-shared state fingerprint) → H7d (the presence probes;
the AC18 page_size-field bug via gold's bytes_left error; the
AC21 encoding-1 layout bug via gold's stride-6 de-interleave
diagnosis; the AC21 hash extraction from the author's traces;
the all-zero-tail-page guard via gh209_1's 642>640 error — three
container fixes + the verbatim gates). The corpus held 280 @ 0/0
and the tests 1587/0 through every landing; the write-target
key-gap fell 13,653 → 8,718.
