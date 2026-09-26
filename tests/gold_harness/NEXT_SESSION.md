# Zero-context prompt — the post-mirror halt: the write-target axis at 3,577 + the wall's residue map + the AC21 follow-ups

> Campaign state 2026-09-26 (the halt after the H7g commit; the
> session ran the review → update → commit → push → continue loop
> from the 5,584 halt through the container-shape mirror landing).
> **The ACS/SH campaign is COMPLETE at 0/0: the corpus stands at 280
> files, read 0, write 0.** The §19 structure READ axis is at ZERO
> gaps corpus-wide. The H7 write-target axis fell **5,584 → 3,577**
> (H7g: the container-shape mirror — R2004_Header 2,088 → 963,
> FILEHEADER 553 → 104, THUMBNAILIMAGE 442 → 50, R2007_Header
> 966 → 925 via the AC21 random_seed mirror). The §18 decoder-walk
> queue stays LANDED (all three walks). The maintainer's fixture
> surface is EMPTY. Read `tests/gold_harness/AGENTS.md` first, then
> §F2.1–F2.3 + §18.5–18.7 in `IMPLEMENTATION.md` (§18.6 carries the
> full decode record including the three walk landings), then
> §19.1–19.3 (the structure campaign — §19.2's H7 row carries the
> H7a–H7g landings + the wall's residue map), then this file top to
> bottom.

## What this session established (the load-bearing facts)

**H7g — the container-shape mirror (the AC18 family)**: the
remaining owned rows reduced to ONE root, and the session proved
the root CLOSES rather than walls: `numsections` (inner header
@0x40) IS the page-map entry count, the four id fields (@0x28
`last_section_id`, @0x50 `section_map_id`, @0x5C `section_info_id`,
@0x60 `section_array_size`) follow the page space, and the
FILEHEADER addresses are page-data positions (seeker + 0x20) — so a
rewrite that reproduces the author's PAGE SPACE reproduces every
count, id and address up to the file tail. Three measured author
conventions were mirrored: (1) the per-descriptor maxdecomp page
splits — the authors single-page the metadata sections at custom
caps (example_2004: AppInfo 0x300, AppInfoHistory 0x580, Preview
0x7C00, SummaryInfo 0x80; the author's tail page pads to the FULL
maxdecomp frame: content 0x510 → frame 0x580) where the historical
writer used the 0x80 SMALL_PAGE and 0x7400 conventions; (2) the
box-id gap — the authors allocate the section-info and page-map box
pages at data_count+3/+4 (example_2004: 24 data pages, boxes at
27/28, ids 25/26 unused, numsections 26 counting only the entries)
where the historical writer used +1/+2; (3) the physical order —
the corpus authors lay the SummaryInfo page first at 0x100 (data at
0x120 = `summaryinfo_address` 288) and the preview page second at
0x1a0 (data at 0x1C0 = `thumbnail_address` 448), where the
historical writer emitted header-first.

**The mirror mechanics**: the reader retains
`DwgAc18ContainerShape` on the document (`dwg_ac18_shape`,
serde-skipped): per-descriptor [mapped + raw 64-byte name, content
size, maxdecomp, compression code, (page id, start-offset) list],
the page map's entries in physical order, and the three identity
ids. `write_ac18` builds every section buffer up front (the
builders are pure — the conventional path stays byte-identical),
runs the `ac18_mirror_plan` content-parity gate (same-origin,
numgaps 0, coherent ids, core sections present, per-section
parity: our re-encoded content covers the author's last page offset
within her capacity, ascending offsets, preview single-paged, our
skipped sections must be the author's 0-page ones; entry count ==
the author's numsections; a physical-order walk with contiguous
section pages and the boxes last), then emits through
`add_section_shaped` — OUR content chunked at the AUTHOR's per-page
offsets, every page carrying the AUTHOR's page id, the tail padded
to her frame, the raw name bytes into the descriptor table — in
the author's physical order, with `set_mirror_ids` driving the
0x50/0x5C/0x60 fields and the box page ids.

**Two hard review edges**: (a) gold's descriptor parser
bounds-checks `dec.byte + 8 + 6*4 + 64 >= dec.size` BEFORE every
entry (decode.c read_R2004_section_info "out of range") — a
mirrored table ending with a 0-page descriptor (the unnamed AcDs)
exactly consumes the stream and fails the check (the historical
tables always ended with a pages-bearing section whose own page
records were the slack): the mirrored table stream carries +32
bytes of tail slack. (b) The preview re-emits RETAINED-RAW when its
actual landing equals the retained `thumbnail_address` (the prefix
pages are size-faithful — the reader retains the whole preview
container since H5c), else the container is rebuilt around OUR
actual address (honest bytes; the row keeps its diff there).

**AcDb:XrefManifest**: the R2013+ authoring tables carry a section
silver never modeled and gold never prints (no census row — the
read axis stays 0 with it absent), but its page is part of the
author's page space. Retained raw (`raw_xref_manifest_data`, the
AppInfo/ObjFreeSpace doctrine) and emitted MIRROR-ONLY
(Box_2013/Revolve_2018-class fixtures gated on it).

**The seven fallback files** (the gate declines; every decline
falls back byte-identically — stash-verified on 2004/Arc
(14→6, its read-gap 2 and the FileDepList mo are the halt-state
values) and 2013/Arc (29→29)): the numgaps>0 authors (2013/Arc/
Line/RAY — gap map entries plus the author's NEGATIVE
tree-node-gap fields, an ODA convention the fallback conventionally
zeroes), the objects-overflow files (2004/2010/2013 Constraints,
2018 Dynblocks: our re-encoded objects exceed the author's page
space — `len − last_offset > maxdecomp`; forcing the fit would trip
gold's reassembly guard), and 2018/Leader (the author's real
FileDepList content vs our 8-byte boilerplate — the PARALLEL
session's row; closing their row re-engages these mirrors for
free). `AC18_MIRROR_DEBUG=1` prints every per-file decline reason.

**The AC21 companion**: `random_seed` mirrored from the retained
`DwgR2007SystemHeader` (gated on the author's crc_seed == our 0).
Decode-inert (gold only prints it in JSON — verified: the field
appears only in the emitters), but it IS the CRC random encoder's
seed (spec §5.2.1.1.1), so the derived draws
(`sections_map_crc_seed`, `pages_map_crc_seed`, `crc_seed_encoded`)
were the hoped bonus — they did NOT land: our CrcRandomEncoder's
sequence diverges from the author's engine at the same seed +
crc_seed (measured on example_2007: the first draw already
differs). The 3-per-file derive family needs the author's
MT-variant pinned bit-exactly (a §5.11 instrument; the table init,
the padding-table consumption, and the draw order all differ
somewhere — the follow-up).

**Verification surfaces kept**: the layer-4 −v9 map comparison
(example_2004: pages 1–5 byte-exact at the author's addresses —
summary 160@0x100, preview 31,776@0x1a0, the verbatim AppInfo
800@0x7dc0, AppInfoHistory 1,440@0x80e0, RevHistory 192@0x8680 —
objects 13 pages both sides, the boxes at 27/28); the
AC18_MIRROR_DEBUG trace; the stash-check fallback proof; the
identity check.

## The remaining queue (3,577) — the wall's residue map

**The AC18 residue is irreducible-by-design**: last_section_address,
secondheader_address, section_map_address, crc32 (4 per engaged
file, 225 files) — file-tail positions and the system CRC move with
our content sizes; they cannot match without whole-file byte
identity. The 7 fallback files keep their historical 9. The rows:

- **R2007_Header 925**: the AC21 container mirror follow-up —
  the page-space pair (pages_amount/pages_maxid + the four map-id
  fields) + the layout/content-coupled families (offsets, sizes,
  six CRCs, corrections) + the crc-seed derive family (the author's
  MT-variant).
- **FILEHEADER 104** (= AC1021 82 + R2000 7 + fallback 14 +
  gh109_1 1) and **THUMBNAILIMAGE 50**: the AC1021 side closes only
  through the AC21 mirror (the RS-chunk page space); the R2000
  seeker pair needs flat-layout parity.
- **FileDepList 1,055 + SecondHeader 386 + AuxHeader 94**: the
  PARALLEL SESSION's rows (their untracked probes `h7_probe1.sh` /
  `h7_rows.sh` sit in the repo root — not ours to commit). NOTE:
  the FileDepList CONTENT class (2004/Arc 2 → gh109_1 75) declines
  our container mirror on the same missing-content root — their
  landing re-engages those mirrors for free.
- **R2004_Header 963 = 4 × 225 + 9 × 7**: accepted residue.

**Dead / no-path rows (do not re-litigate)**: `LoftD` (no settings
path in the authoring release); the SH revolve option shorts;
**BREP stays deferred** — only an external authentic
`ACSH_BREP_CLASS` specimen re-opens it.

## The standing facts (the decode authority is §18.6)

- The four raw-retained SH tails decode to typed views with the
  captured bits as the write authority (the Phase B write rule).
  The hermetic suite stands at 20 tests + the module tests.
- REVOLVE/SWEEP/EXTRUSION/LOFT closed as recorded; the loft
  leading/inter-section regions, the sweep frame-block repeats, the
  extrusion 64-bit payload, and the 32+n/32 closed form stay
  verbatim-retained.
- The corpus workdirs are STEM-KEYED: 280 files collapse to 196
  unique stems (version-dir duplicates overwrite) — per-file
  aggregations from the workdirs are partial views; the
  report.json totals are authoritative.
- **The generation identity is UNTOUCHED:
  `40ab5d356cf05a71333ff208e1651daf`, 25,344 bytes (re-verified
  twice after the H7g landing — programmatic documents keep the
  conventional path).**
- The gold tree is UNCHANGED at `34f02f54` (local build artifacts
  only). The anchors re-verified: the LOFTEDSURFACE typed spec
  `dwg2.spec:3984`, the LWPOLYLINE grammar `dwg.spec:5446`, the
  container-parity fields `r2004_file_header.spec:41-53`, the
  read_R2004_section_map/info decoders (decode.c:1432-1870), and
  all H7d container-fix sites.

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
# (the mirror classes: AC18 fixtures land at write-target 4 —
#  the residue family; Box_2007 stays 25 until the AC21 mirror)

# 3. Full corpus (must stay 280 files 0/0; read key-gap 0;
#    write-target key-gap 3,577 at this halt)
python3 tests/gold_harness/run_corpus.py
# (the per-file mirror trace: AC18_MIRROR_DEBUG=1 in the env)

# 4. Layer-4 byte-walk for any writer re-encode path
target/debug/dump_section_bytes <file> <A> <N>
```

## Commit inventory (this halt — all PUSHED)

```
<docs> docs(harness): the post-mirror halt refresh — the H7g landing, the 3,577 residue map, the AC21 follow-ups
<feat> fix(dwg): the H7g container-shape mirror — the author's page space reproduced at write (R2004_Header 2088 -> 963, FILEHEADER 553 -> 104, THUMBNAILIMAGE 442 -> 50, R2007_Header 966 -> 925)
a22e95a <review> docs(harness)/fix(dwg): the 2026-09-26 review pass — the 0x15 unknown-byte mirror + the README identity re-record + the docs consistency replay
10e9423 docs(harness): the halt refresh — the H7e/H7f landings, the container-parity wall, the three §18 walks landed
74a75d2 feat(sh): the loft container and ExtrudeP polyline walks — the per-section fields and the kind-77 CALL body named (§18 walks 2 and 3)
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
through this halt (push after each landing per the maintainer's
loop instruction: `git push origin gold-vs-silver`).

**Session arc, for context**: the halt-state verification (corpus
280 @ 0/0 at 5,584) → the gold container analysis (the −v9 map
dumps: the author's page orders, the box-id gaps, the
maxdecomp-per-descriptor tables) → the reader retention (the shape
struct + the physical map order) → the writer mirror (the shaped
emitter + the gate + the identity overrides) → the slack-edge fix
(gold's descriptor bounds-check) → the XrefManifest retention (the
R2013+ fixture gates) → the AC21 random_seed mirror + the derived-
draws divergence analysis → the full corpus (−2,007, the counted
fallbacks) → the stash-check fallback proofs → the identity
verification → the halt refresh. The corpus held 280 @ 0/0 and the
tests 1592/0 through every step; the write-target key-gap fell
5,584 → 3,577.
