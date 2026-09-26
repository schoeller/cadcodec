# Zero-context prompt — the post-walks halt: the write-target axis at 5,584 + the container-parity wall + the §18 walks landed

> Campaign state 2026-09-26 (the halt after the walk-3 commit; the
> session ran the review → update → commit → push → continue loop
> from the H7d halt through FIVE landings). **The ACS/SH campaign is
> COMPLETE at 0/0: the corpus stands at 280 files, read 0, write 0.**
> The §19 structure READ axis is at ZERO gaps corpus-wide. The H7
> write-target axis fell **8,718 → 5,584** (H7e: the ObjFreeSpace row
> at ZERO; H7f: the FILEHEADER identity row 1,204 → 553), and the
> §18 decoder-walk queue is **LANDED (all three walks)**. The
> maintainer's fixture surface is EMPTY. Read
> `tests/gold_harness/AGENTS.md` first, then §F2.1–F2.3 + §18.5–18.7
> in `IMPLEMENTATION.md` (§18.6 carries the full decode record
> including the three walk landings), then §19.1–19.3 (the structure
> campaign — §19.2's H7 row carries the H7a–H7f landings + the
> container-parity wall analysis), then this file top to bottom.

## What this session established (the load-bearing facts)

**H7e — the ObjFreeSpace verbatim row (`dd7f854`)**: the row's two
halves had one root each. (1) The R2004+ rebuilt content: silver
re-encoded numhandles/TDUPDATE/the max pattern words from silver's
own state — the author's bytes are file STATE (Box_2007's
zero/numhandles = 0xFFFF0000, the R2007+ pattern words; the R2000
objects_address=2672-style absolute offsets), not derivable data.
The reader now retains the raw section bytes
(`raw_obj_free_space_data`, both arms); all three writer paths
re-emit verbatim on a same-version roundtrip, skip the section when
the source had none (gold prints nothing there on R2000 and the
zeroed struct on both sides on R2004+), and keep the historical
rebuild for programmatic/conversion documents. Corpus:
ObjFreeSpace **2,453 + 30 → 0** (3,441 matched, 0/0 both axes).
(2) **The R2000 placement family**: gold reads the R2000 section
ONLY when its locator address equals the file position DIRECTLY
after the handles map (decode.c's
`section[SECTION_OBJFREESPACE_R13].address == pvz` gate, the
post-terminator-CRC position) — silver's AC15 writer placed the
section among the pre-objects records, so gold never read the
rewrite's section (PolyLine2D/entities-2d/entities-3d: 10 leaves
each, the "+30"). The AC15 record now sits AFTER the HANDLES record
(the R13/R14 branch's own order), and a never-populated record
keeps the NUL form (seeker 0 — the author's own absent convention,
cf. PolyLine2D's Template record nr4 at address 0) instead of
pointing at live bytes. The parallel session's SecondHeader row was
NOT touched (the retained 53-byte span ends where the 2ndheader
sentinel begins).

**H7f — the FILEHEADER identity bytes (`03134e7`)**: the five
identity bytes were per-writer constants where the authors wrote
per-build bytes (example_2004's maint_rel 104 / dwg_version 33 /
maint 29 / app pair 33/29; Revolve_2018's maint 0 vs the canonical
4; Box_2007's maint_rel 50 / dwg_version 33 / maint 255 / app pair
33/255 / codepage 30; PolyLine2D's version pair 31/8). All three
file-header writers take a same-version source mirror
(`set_source_header_bytes` / `set_source_version_pair` from the
retained `DwgFileHeaderSummary`); AC21's codepage is mirrored too.
THE LAYOUT-NEUTRALITY of the maint byte: the write-ac18 effective
maint becomes the author's `maint_version` — safe for every corpus
class because gold's decode gates read: R2004 →
`dwg_decode_header_variables` (PRE R_2007a) which reads NO
bitsize_hi; R2007 → its own path with the gates commented out;
R2010/R2013 → bitsize_hi iff maint>3 (the authors' bytes there are
ALL > 3 like the canonical); R2018 → the `|| >= R_2018` arm. Silver's
`has_section_extra_rl(AC1024+/maint>3 || AC1032+)` matches gold's
decode EXACTLY (verified against decode.c:2468 + decode_r2007.c).
Corpus: **FILEHEADER 1,204 → 553** — the residue is the pure
address-shift family (thumbnail_address + summaryinfo_address
pairs on R2004+, the preview seeker on R2000): layout-coupled, not
byte-identity.

**The three decoder walks (NO new fixtures)**:
- **Walk 1 (`ade0de3`), the post-corner singles**: the sweep corner
  block's trailing unpaired entry is the RECORD CONSTANT
  4.00024414192312 (named `record_constant`, bit-invariant across
  every profile/path/direction differential — previously silently
  dropped); between the corner block and the segment-end block the
  tail carries [4 zero pad bits][one '00'-framed BD][a short '10'
  pair] — the first plausible frame is `post_corner_single`, a
  32 + n/32-class value carrying the WIDTH coupling (X/L/D
  32.0625, W 32.21875, Polysolid 32.15625). **The closed form
  anomaly: W/PS track their width exactly (n=7/5); the X-family
  reads n=2 for width 3 — UNRESOLVED.** The §18.7 P-era "singles"
  ("2.0109", the "width single" 3.0/7.0, the 8.06-class) are
  OVERLAPPING ALIASES of the same zero-heavy bits — the alias
  doctrine is now pinned in the field docs; they never pin spans.
- **Walks 2+3 (`74a75d2`), the loft container + the ExtrudeP
  polyline**: the loft raw frames group into contiguous runs (a
  2-bit gap = adjacency, 4-bit = an elided canonical short BETWEEN
  raws, wider = a section boundary); the final 2-frame run names
  the trailing draft pair; earlier runs attribute to the closed
  per-section `[center.x][center.y][height][radius]` reading with
  per-field `Option` elisions (LoftC's section 1 = the 3-frame
  gap-after-2 shape). The leading region (8/48/68 bits — a fully
  elided origin section's shorts + per-record state), the
  inter-section gaps, and the constant 14-bit trailer
  `10100111010110` stay documented-verbatim. The ExtrudeP kind-77
  CALL body decodes through the embedded-LWPOLYLINE grammar (flag
  512 closed, num_points 4, raw LE64 (x,y) pairs = the 4×3
  rectangle, the trailing reserved '11' pair closes the window);
  `SolidHistoryProfilePolyline` on the CALL; vertex edits splice
  bit-locally in their own 128-bit frames. The hermetic cover grew
  15 → 20; every edit-lands test follows the Phase B write rule.

## The remaining queue (5,584) — the container-parity wall

**The analytical landing of this session (§19.2's H7 row carries
it in full): the remaining owned rows reduce to ONE root** —
silver's container page-space differs from the author's.
`numsections` (the inner header @0x40) IS the page-array slot
count: example_2004's author runs **26 page-ids** (with gaps to id
28) where silver's rewrite carries **42 pages** for the same
section set (verified: 13 section-info descriptors on both sides;
the author splits sections with custom per-descriptor
max-decomp-size — classes single-paged at 31,776 bytes — where
silver uses its conventional page splits).
`last_section_id`/`section_map_id`/`section_info_id`/
`section_array_size` follow the page space, and the three address
fields move with the layout. **R2004_Header 2,088** and
**R2007_Header 966** close only via a container-shape mirror (the
author's per-descriptor page splitting + id pattern with our own
content — approximate, since header/objects re-encode to different
sizes); **THUMBNAILIMAGE 442** is the same wall's address-coupled
face (the preview chain holds absolute file offsets);
**FILEHEADER 553** is the address family above. The
FileDepList 1,055 + SecondHeader 386 + AuxHeader 94 rows stay the
**PARALLEL SESSION's** (their untracked probes `h7_probe1.sh` /
`h7_rows.sh` sit in the repo root — not ours to commit).

**Dead / no-path rows (do not re-litigate)**: `LoftD` (no settings
path in the authoring release — the draft pair's naming stays
provisional); the SH revolve option shorts + flags through the
REVOLVE command (the typed anchor is in-corpus via RevolveM's
bit-retained raw tail); **BREP stays deferred** — only an external
authentic `ACSH_BREP_CLASS` specimen re-opens it.

## The standing facts (the decode authority is §18.6)

- The four raw-retained SH tails decode to typed views with the
  captured bits as the write authority (the Phase B write rule:
  `render_*_tail` splices only differing same-form spans;
  untouched records re-emit bit-identically — pinned by the
  hermetic suite, now 20 tests + the module tests). The
  unknown-object records (the SURFACE twins, the ACSH node classes)
  re-emit verbatim through the raw passthrough arm.
- REVOLVE is fully closed (the CALL grammar); SWEEP/EXTRUSION
  through the spine + the profile CALL (circle or polyline, both
  typed now); LOFT through the named per-section fields + the
  positional raws. Still opaque after the walks: the sweep
  frame-block repeats, the extrusion 64-bit payload, the loft
  leading/inter-section regions, the 32+n/32 closed form — all
  verbatim-retained.
- The post-corner region's span map (the X-class 1418-bit tails):
  [22..~490 the raw-BD frame region with gaps][8 byte-aligned
  corner LE64s][the record constant LE64][4 pad bits][the 32-class
  BD frame][a short pair][the 4-LE64 segment block][2 pad bits].
- The corpus workdirs are STEM-KEYED: 280 files collapse to 196
  unique stems (version-dir duplicates overwrite) — per-file
  aggregations from the workdirs are partial views; the
  report.json totals are authoritative.
- **The generation identity moved at an earlier landing without a
  re-record: the current deterministic identity is
  `40ab5d356cf05a71333ff208e1651daf`, 25,344 bytes (this session
  verified it twice, unchanged by H7e/H7f — programmatic documents
  keep the historical bytes). The README's recorded
  `0217fbac515a20b90e9c3aea883196e3`/24,986 was stale.**
- The gold tree is UNCHANGED at `34f02f54` (local build artifacts
  only). The anchors re-verified this session: the LOFTEDSURFACE
  typed spec `dwg2.spec:3984` (start/end_draft_angle+magnitude,
  the B-flags, num_cross_sections — the loft walk's naming
  corroboration), the LWPOLYLINE grammar `dwg.spec:5446`, the
  container-parity fields `r2004_file_header.spec:41-53`, and all
  H7d container-fix sites (decode.c's reassembly guard, the AC21
  RS-page gate, the out_json presence gates).

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
cargo test --features serde          # 1592 passed / 0 failed at this halt
cargo test --features gold-harness --test gold_roundtrip

# 2. Family smokes (any sh_history fixture must stay 0/0)
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (must stay 280 files 0/0; read key-gap 0;
#    write-target key-gap 5,584 at this halt)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 byte-walk for any writer re-encode path
target/debug/dump_section_bytes <file> <A> <N>
```

## Commit inventory (this halt — all PUSHED through `74a75d2`)

```
74a75d2 feat(sh): the loft container and ExtrudeP polyline walks — the per-section fields and the kind-77 CALL body named (§18 walks 2 and 3)   <- HEAD
ade0de3 feat(sh): the post-corner singles walk — the sweep tail's record constant and width-coupled single named
03134e7 fix(dwg): the FILEHEADER identity bytes from the source — the H7f maint/app row at 1204 -> 553
dd7f854 fix(dwg): the ObjFreeSpace verbatim sections — the H7e write-target row at zero (2,453 + 30 @ 0/0)
f9e4e06 docs(harness): the halt refresh — the H7 review + the H7c/H7d landings, the 8,718 queue, the container-fix knowledge
... (the 2026-09-25/26 §19 arc below, oldest first: the plan-session
docs, the H0 axis skeleton + day-one census, the H2 header rows, the
H4 metadata rows, the H5 CLASSES landings, the H3 header landing, the
H7a header splice, the H7a/H7b review pass, the H7b SummaryInfo, the
H7c CLASSES verbatim, the H7d AppInfo/AppInfoHistory — the corpus
held 280 files at 0/0 through every commit)
```

**PUSH STATE (2026-09-26)**: the `gold-vs-silver` branch is PUSHED
through `74a75d2` (push after each landing per the maintainer's
loop instruction: `git push origin gold-vs-silver`).

**Session arc, for context**: the halt-state verification (corpus
280 @ 0/0 at 8,718) → H7e (the reader retention both arms; the AC15
placement surgery + the NUL-record semantics; five family smokes:
PolyLine2D 76→66, TS1 unchanged, Box_2007 35→31, example_2004
20→16, Revolve_2018 25→15; the corpus at −2,483 = the row exactly)
→ H7f (the five-byte mirror across the three writers; the
maint-layout-neutrality verification against gold's three decode
paths; eight family smokes across every version class; the corpus
at −651) → the gold re-scan (tree unchanged; the
LOFTEDSURFACE/LWPOLYLINE/r2004_file_header anchors pinned) → the
three decoder walks (the alias doctrine for the P-era singles; the
loft grouping rules; the embedded polyline grammar wired; hermetic
15 → 20) → the halt refresh. The corpus held 280 @ 0/0 and the
tests 1592/0 through every landing; the write-target key-gap fell
8,718 → 5,584.
