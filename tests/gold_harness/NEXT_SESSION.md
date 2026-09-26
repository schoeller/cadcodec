# Zero-context prompt — the post-H3 halt: the structure READ axis at zero + the three decoder walks + the H7 write rows

> Campaign state 2026-09-26 (the halt after the H3 row).
> **The ACS/SH campaign is COMPLETE at 0/0: the corpus stands at
> 280 files, read 0, write 0** (the 180 campaign baseline + every
> §18.7 differential quad — solid AND surface twins **all landed;
> the quarantine tree no longer exists**). The maintainer's fixture
> surface is EMPTY: no DWG authoring is requested. **The §19
> structure READ axis is now at ZERO gaps corpus-wide** (the H3
> HEADER row landed 2026-09-26: 138,021 matched + 0 + 0; the read
> key-gap 128,489 → 0). All remaining work is agent code: the three
> SH decoder walks (§18.6's queue) and the §19 H7 write-target rows
> (21,822 — the only open structure surface), per maintainer
> priority. Read `tests/gold_harness/AGENTS.md` first, then
> §F2.1–F2.3 + §18.5–18.7 in `IMPLEMENTATION.md` (§18.6 carries
> the full decode record), then §19.1–19.3 (the structure campaign
> — §19.2's H3 row carries the header landing), then this file top
> to bottom.

## What the H3 landing established (the load-bearing facts)

**The gap was a TOTAL NAMING SPLIT, as scoped**: silver's modeled
`header` prints its own snake_case names (267 unversioned keys,
bare-handle/shape serialization) while gold prints the ALLCAPS
spec names with component tuples — the 280-file gold harvest
pinned the emission as purely version-determined (identical key
sets per class: 228 R2000 / 246 R2004 / 291 R2007 / 296 R2010 /
298 R2013+, a 300-key union).

**The design — the raw-mirror summary**: `DwgHeaderRaw` on the
document (~300 `Option` fields, one per gold key, serde-renamed to
gold's spelling, skip-if-none so the version gates fall out of the
reader walk's population), retained by TWIN assignments in
`read_header_fields` — every wire read taken once, assigned to the
model where silver models the field and stored raw under gold's
key (the `let _ =` discards became `raw.x = Some(..)`; the walk's
bit consumption is unchanged — the write axis at 0/0 had already
proven it per-version on all 280 files). Handles retain the wire
form `[code, size, value, absolute]` (`DwgRawHandle` — gold's
FORMAT_HREF), points `[f64; 3]`, limits `[f64; 2]`, TIMEBLL
`[days, ms]`, colors the post-decode CMC parts (`DwgRawCmc`).
struct_axis projects `dwg_header_raw` key-for-key (the modeled
`header` stays the API surface; the writer is untouched — the H7
write-target row stands at 21,822).

**The "gold is unique" re-analysis (the print-exactness rules,
pinned in the libredwg src BEFORE landing — every one
load-bearing, and the H7 writer row will need them again):**
- `FORMAT_BS` is `PRIu16` **UNSIGNED** (include/dwg.h:152) while
  `FORMAT_BSd` is signed — the d-suffixed emitted fields are
  exactly TREEDEPTH/USERI1-5/DIMLWD/DIMLWE; all eight `FIELD_CAST`
  fields (DIMALTD/DIMZIN/DIMTOLJ/DIMJUST/DIMTZIN/DIMALTZ/
  DIMALTTZ/DIMTAD) cast to plain BS (the third macro arg —
  unsigned); OBSCOLOR/INTERSECTIONCOLOR are plain BS.
- `FORMAT_BL`/`BLx` are `PRIu32` unsigned (FLAGS,
  unknown_8/9/12–17/21/22); TIMEZONE is `BLd` signed;
  `FIELD_TIMEBLL` prints `[days, ms]` as unsigned BL;
  REQUIREDVERSIONS is BLL unsigned.
- BD prints `%.14f` with trailing-zero trim (out_json.c
  `_VALUE_RD`) — inside the axis float tolerance (`_REL_TOL`
  1e-6), no normalization needed.
- **The CMC post-decode state** (bits.c `bit_read_CMC`): decode
  OVERWRITES the wire BS index with `dwg_find_color_index(rgb)`
  (gold's 256-entry palette — 222 entries differ from silver's ACI
  table; embedded hex in struct_axis), ZEROES a flag ≥ 4 without
  reading the name/book strings, and forces an out-of-range method
  nibble to 0xC2 keeping the low 24 bits; the emitter
  (out_json.c `field_cmc`) prints the index iff non-zero —
  **INCLUDING 256** (INTERFERECOLOR `{index: 256, rgb:
  c3000001}`), the rgb as `%06x`, the flag iff non-zero, name/book
  behind bits 0/1; the emitter's else-branch derivations are DEAD
  (a zero lookup implies rgb&0xFFFFFF==0 so they yield 0 too);
  pre-R2004 prints the bare wire index via `%d` over the uint16
  (0..65535). Silver's `read_cm_color_raw` mirrors the decode
  validations exactly (the modeled `read_cm_color` is untouched).
- Every spec `FIELD_VALUE` transform (FLAGS |= lweight, TSTACK
  defaults, unit1_ratio = 412148564080.0, unknown_8 = 24) is
  `ENCODER`/`IF_ENCODE_FROM_EARLIER` gated — decode emits wire
  values verbatim.
- The null-ref 2-element `[0,0]` handle emitter branch is
  unreachable (every handle read creates a ref — the corpus shows
  only 4-tuples).

**Verification**: the six-version probe set (one file per class:
2000/Line, example_2004/2007/2010/2013, sample_2018) at
401/419/489/494/499/499 leaves — 0 diffs, 0 missing, 0 extra on
every class; cargo test 1588/0; gold_roundtrip ok; the sh_history
smokes 0/0 with the structure read key-gap 0; the full corpus 280
@ 0/0 with the read key-gap 0.

## What the surface-parser row established (still standing)

**The gold-shadow classes walk** (§18.6's surface-parser decode
record): gold (libredwg) reads the R2004+ class-record tails as
`BS, BS` for `dwg_version`/`maint_version` where the real encoding
uses `BL` — on the AutoCAD-2027.1-authored fixture set (all four
versions AC1021–AC1032) its numeric cursor derails from the 10th
class entry on, so its `item_class_id`s degrade to garbage (never
`0x1F2`) and the surface ENTITY records (EXTRUDEDSURFACE /
LOFTEDSURFACE / REVOLVEDSURFACE) route through gold's
unknown-OBJECT walk: object-common data + the full raw tail as
`unknown_bits`. Silver lands parity NOT by typing the surfaces
(their spec blocks are DEBUG_CLASSES-dead in the built oracle)
but by walking the classes section exactly as gold does
(`classes_reader::gold_shadow_item_ids` →
`DxfClass::gold_item_class_id`) and keying the pass-2 entity set
on the **RAW** class number (the internal map resolves
EXTRUDEDSURFACE to the `-7` sentinel, which would bypass the
shadow). The surface records therefore decode as `UNKNOWN_OBJ`
records with bit-exact raw tails on both sides — the semantic
naming maps (the SWEEPOPTIONS/lofting/revolving field lists in
dwg2.spec 3952–4152) remain available for FUTURE typed modeling of
those retained tails, with the fixtures now in-corpus as
specimens.

**The ASSOC surface grammar is version-split at PRE(R_2013b)**:
pre-R2013 files keep the full pab block (version/minor/deps/l4/
l5 + the named `pab.values` — ExtrusionHeight/ExtrusionTaperAngle
on ExtrudeM, Continuity/Bulge on LoftM, RevolveAngle on RevolveM
— all printing gold's degenerate `[0]*count` REPEAT collapse);
R2013+ files read NO pab fields and `assocdep` IS the sab slot.
`ASSOCACTION` SINCE R_2013 (class_version > 1) carries the
trailing values REPEAT (gold prints `[0]*count` — same collapse
class as deps); `ASSOCPATHACTIONPARAM` prints `aap_version` (the
R2013 BL after is_r2013).

## The work: the three decoder walks (no new fixtures)

1. **The post-corner singles walk (sweep)**: the entries are
   CLASSIFIED (§18.7's Polysolid rows: the width single at bit
   1084, the record constant 4.00024414192312, the
   profile-derived 2.0109/@900/@1092, the path-derived segment
   end) but stay raw — extend `sh_tail_decode.rs` past the corner
   blocks with a proper BD walk and pin the spans.
2. **The loft container walk**: the raw-run reading is CLOSED
   (per-section `[center.x][center.y][height][radius]` runs +
   the `[π/2, π/2]` draft pair) but the model keeps `raw_doubles`
   positional — walk the inter-value regions so the per-section
   fields can be exposed as named model fields.
3. **The ExtrudeP polyline header**: the profile CALL kind 77
   body (length 544) holds the packed (x, y) vertex array; the
   grammar is ALREADY in-repo (`read_embedded_lwpolyline` in the
   object readers) — wire it into the CALL body decode.

**Dead / no-path rows (do not re-litigate)**: `LoftD` (no settings
path in the authoring release; the `[π/2, π/2]` name now runs
through the loft container walk or LoftM's raw tail, NOT typed
gold fields); the SH revolve option shorts + flags through the
REVOLVE command (the typed anchor is in-corpus via RevolveM's
bit-retained raw tail); **BREP stays deferred** — only an
external authentic `ACSH_BREP_CLASS` specimen re-opens it.

## The §19 arc state (the read axis CLOSED; H7 next on the structure side)

The OBJECTS axis is done (280 files at 0/0). The structure axis —
everything the reader sees that is not an object record — is now
**at ZERO read gaps corpus-wide**: H0 (the axis + day-one census,
read key-gap 259,073), H2 (FILEHEADER/R2004_Header/R2007_Header/
SecondHeader/AuxHeader — 11,492 leaves), H4 (the metadata blocks
— 15,626 leaves), H5b (CLASSES — 60,954), H5c (THUMBNAILIMAGE —
558), H5a (AcDs — 58,471), and **H3 (HEADER — 138,021: the raw
mirror, landed 2026-09-26, `e7ead8f`; the full record in §19.2's
H3 row)**. **The structure read key-gap stands at 0; every
observed key reads at gold parity** (HEADER 138,021+0+0,
CLASSES 60,954+0+0, AcDs 58,471+0+0, every H2/H4 row 0/0). The
authoritative enumeration is CLOSED (§19.1): 17 observed
structure keys + the declared-absent `VBAProject`/`Signature` +
`created_by` (EXCLUDED: gold hardcodes its own `PACKAGE_STRING`
there) + the not-JSON machinery. **The remaining structure
surface is the H7 WRITE-TARGET axis (key-gap 21,822)**: HEADER
6,366 value-diffs + 268 missing (gold's unknown slots + the time
fields — silver's writer re-emits defaults for the unmodeled
fields; the H3 raw mirror now carries the wire values the writer
needs), ObjFreeSpace 2,453+30, CLASSES 3,246, R2004_Header
1,771, AppInfo 1,651, SummaryInfo 1,533, FILEHEADER 1,205,
R2007_Header 979, THUMBNAILIMAGE 442, AppInfoHistory 342,
AuxHeader 95 — **plus the two whole-section write drops:
SecondHeader (386) and FileDepList (1,055)**. The H7 work follows
the same per-packet workflow (the write axis changes need the
layer-4 byte-walk gate); the three decoder walks above interleave
per maintainer priority. The OBJECTS axis stays frozen at 0
throughout.

## The standing facts (the decode authority is §18.6)

- The four raw-retained SH tails decode to typed views with the
  captured bits as the write authority (the Phase B write rule:
  `render_*_tail` splices only differing same-form spans;
  untouched records re-emit bit-identically — pinned by the
  hermetic suite). The unknown-object records (the SURFACE twins,
  the ACSH node classes) re-emit verbatim through the raw
  passthrough arm — the rewritten surface record was verified
  bit-identical at landing (gold_rt @731: same size/bitsize, the
  full 1708-hex unknown_bits equal, eed/ownerhandle/xdic equal).
- REVOLVE is fully closed (the CALL grammar); SWEEP/EXTRUSION
  through the spine + the profile CALL; LOFT through the
  per-section raw run. The hermetic cover is
  `tests/solid_history_tail_decode.rs` (15 tests) + the module
  tests in `sh_tail_decode.rs` — all run under gate 1.
- The un-quarantined C first attempts live as
  `ExtrudeCSurf_<v>`/`LoftCSurf_<v>` (their Solid re-authors
  kept the bare C names).

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
cargo test --features serde

# 2. Family smokes (any sh_history fixture must stay 0/0)
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (must stay 280 files 0/0)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 byte-walk for any writer re-encode path
target/debug/dump_section_bytes <file> <A> <N>
```

## Commit inventory (this halt)

```
<this halt's handover note: the NEXT_SESSION.md refresh>   <- HEAD
e7ead8f fix(dwg): the header raw mirror — the H3 HEADER read row at gold parity (138,021 @ 0/0)
721c22a docs(harness): the halt refresh — the H5c + H5a landings, the HEADER-only read gap, the queue state
ea8e731 fix(dwg): the AcDs section-level view — the H5a read row at gold parity (58,471 @ 0/0)
83d9819 fix(dwg): the preview section-first read + the no-image retention + the AC1021 tail rule — the H5c THUMBNAILIMAGE read row closes
... (the 2026-09-25/26 §19 arc below, oldest first: the plan-session
docs e1f75cd/0740827/bb73e72/3f490bd, the H0 axis skeleton + day-one
census d27c0c7 with the 15a4a01 review, the H2 header rows through
9e945fe + the 902eadc review, the H4 metadata rows 50c246d + the
745b7af review, the H5b CLASSES landing 5bbd79c, the H5c partial
35e3a9f — the corpus held 280 files at 0/0 through every commit)
```

**PUSH STATE (2026-09-26)**: the remote currently has NO
`gold-vs-silver` ref (only `origin/main`) — the entire local
`gold-vs-silver` branch (the §18 campaign + the §19 packets through
this halt) is unpushed relative to the remote. Push when the
maintainer asks (`git push origin gold-vs-silver`).

**PLAN-SESSION COMMIT INVENTORY (2026-09-25, docs-only — the codec
untouched, the corpus 280 @ 0/0 stood through each commit)**:

```
<NEXT_SESSION.md refresh: the 19 section synced to the committed plan facts>   <- this session's last
3f490bd docs(harness): the 19 completeness fixes — the duplicate created_by row, the vbaproject.spec miss, the Signature table row
bb73e72 docs(harness): the 19 libredwg tree re-analysis — the structural enumeration closed, created_by reclassified, the emission gates recorded
0740827 docs(harness): the 19 review pass — the inventory corrected, the completeness gaps pre-populated
e1f75cd docs(harness): the 19 plan — the header & whole-structure campaign scoped, the rows ordered
```

(The session's arc, for context: the environment check confirmed
the remote head == the previous handover; the 20 quarantined
files surveyed — the diffs decomposed into FOUR fix families; the
gold -v4 trace + a byte-level python emulation of the classes
walk pinning gold's desync at the 10th class entry on every
2027.1-authored file; the gold-shadow reader landing + the
pass-2 raw-class-number flip + the block-chain wire-vector fix +
the four ASSOC grammar projections; the 20 fixtures at 0/0
(read AND write, all four versions each); cargo test 49 suites
ok; the 260-file corpus green across the change; the tree move
with the ExtrudeCSurf/LoftCSurf renames; the corpus 280 at 0/0;
the bit-identical rewrite verified on the surface record.
The corpus's last 20 rows are closed; the tail-decode walks
remain.)
