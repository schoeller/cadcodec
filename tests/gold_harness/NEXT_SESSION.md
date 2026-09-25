# Zero-context prompt — the post-surface halt: the three decoder walks

> Campaign state 2026-09-24 (the halt after the surface-parser row).
> **The ACS/SH campaign is COMPLETE at 0/0: the corpus stands at
> 280 files, read 0, write 0** (the 180 campaign baseline + every
> §18.7 differential quad — solid AND surface twins **all landed;
> the quarantine tree no longer exists**). The maintainer's fixture
> surface is EMPTY: no DWG authoring is requested. All remaining
> work is agent decoder code on the four raw-retained SH tails.
> Read `tests/gold_harness/AGENTS.md` first, then §F2.1–F2.3 +
> §18.5–18.7 in `IMPLEMENTATION.md` (§18.6 carries the full decode
> record — including the gold-shadow classes-walk finding that
> closed the surface row — with its evidence chains), then this
> file top to bottom.

## What the surface-parser row established (the load-bearing facts)

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

## The next major arc (planned 2026-09-25, not yet started): §19 — the header & whole-structure campaign

The OBJECTS axis is done (280 files at 0/0). The harness's scope
extends next to everything the reader sees that is not an object
record — a second, separately-gated structure axis with its own
corpus counters, driven to 0 under the same per-packet workflow,
with the whole-structure audit matrix (§19.2's H6) as the standing
deliverable proving every section of a DWG is either diffed or
excluded with a recorded reason. **Arc status (2026-09-25): H0
LANDED** (`d27c0c7` + the `15a4a01` review pass: the axis wired, the
day-one census measured — read key-gap 259,073 / write-target 21,822;
AcDs verbatim 0/0 corpus-wide; two whole-section write drops found —
SecondHeader, FileDepList — now H7 rows), **H2 COMPLETE** (all five sub-rows at zero read gaps: FILEHEADER
4,151 + R2004_Header 5,336 + R2007_Header 1,353 + SecondHeader 386 +
AuxHeader 266 = 11,492 leaves; read key-gap 248,141; the ledgers:
hand-decoded byte positions, the R2007 shape a pure projection of
silver's container metadata, the R2000 pair the family's only NEW
READS — the sentinel-located SecondHeader and the locator-addressed
AuxHeader, both hand-validated before implementation — see §19.2's
H2 row). **H4 LANDED** (the metadata blocks at zero read gaps
corpus-wide: 15,626 leaves matched, the gap −13,450; read key-gap
234,691; the load-bearing findings in §19.2's H4 row). **H5b
LANDED** (CLASSES at zero read gaps corpus-wide: 280/280 files,
60,954 matched, the gap −47,173; read key-gap **187,518**; the full
gold-shadow record carries the desynced tables' garbage
record-for-record; the landing exposed and fixed the latent
wire-color field-type bug — WIRESTRUCT's color is a BS on every
version, the §18 reader/writer had it BL on R2004+ — see §19.2's
H5 row). **Next: H5a AcDs (58,471 — the section-level view; the
embedded-record decode exists, the JSON view needs pinning), H5c
THUMBNAIL (558, the digest), then H3's HEADER ledger (128,489 —
the dominant row).** **The authoritative enumeration is
CLOSED** (the libredwg tree re-analysis + the review passes, all in
§19.1): 17 observed structure keys (16 per R2004+ file, 8 on R2000
— including `R2007_Header`, its OWN 33-field AC1021 system section,
not the R2004 shape's 23) + the declared-absent `VBAProject` and
`Signature` + `created_by` (an EXCLUDED row: gold hardcodes its own
`PACKAGE_STRING` there — an oracle identity stamp, not file content)
+ the not-JSON machinery (object map/Handles — gold's emitter is
`#if 0`'d; the R2004+ container types SECTION_INFO/SYSTEM_MAP;
CRCs/sentinels/padding). **14 spec files** in the gold tree
(`header.spec` … `vbaproject.spec`; `appinfo.spec` covers both
AppInfo and AppInfoHistory) are the authoritative field lists for
the projections, exactly as `dwg2.spec` was for OBJECTS.
Load-bearing facts for the rows: `AppInfoHistory` is located by
section TYPE (12), not by an `AcDb:` name — silver's registry lacks
it (a named H4 row); gold's emission is GATED by FILEHEADER fields
(`sections` locator count on R2000; `summaryinfo_address`/
`vbaproj_address` on R2004+) — a one-side-only key is a structural
diff; `SecondHeader` carries the R2000 locator table and lives
inside the ObjFreeSpace section. First packet: **H0 — the axis
skeleton + the day-one census** (the per-key diff counts over the
280-file corpus that set the attack order; the no-leak assertion
for undeclared keys). The OBJECTS axis stays frozen at 0
throughout; the header comparison may interleave with the three
decoder walks below per maintainer priority.

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
<this halt's handover note: the NEXT_SESSION.md commit-inventory hash fix>   <- HEAD
72xxx docs(harness): the halt refresh — the gold-shadow decode record, the 18.7 landed rows, the queue state
247e8e9's true neighbors below (the halt's three commits, oldest first):
f11f7a1 fix(dwg): the classes gold-shadow walk + the R2013+ surface action-body grammar — the surface-parser row closes
52491d7 test(harness): the 20 surface-twin files land — the quarantine tree closes, the corpus goes 260 -> 280 at 0/0
247e8e9 docs(harness): the halt refresh — the gold-shadow decode record, the 18.7 landed rows, the queue state
5c89b59 fix(dwg): the sweep spine named + the extrusion profile CALL — §18.7 differential decode
57232a6 test(harness): the §18.7 differential set lands — 14 solid stems in-corpus, 3 M-stems quarantined
... (the full session arc: 804e892, daedfb7, 05368b3, 839012c, a656f99,
9d08280, ac5c47e, 86ce5a7, f2891b1, 7f2a77f, 9a260ae, e1dff05)
```

**PUSH STATE**: the halt's four commits (`f11f7a1` fix, `52491d7`
fixture landing, `247e8e9` halt refresh, `6103dcd` handover note)
plus the review follow-up (`62fb7bc`: the halt's code review landed
all six findings — the full-count shadow mirror with gold's exact
plausibility bounds, the shared section prelude, the O(1) block-list
dedupe, the crafted-section invariant pins, the entity-marker
constants; gates 1324 tests + corpus 280 at 0/0) are pushed
(`origin/gold-vs-silver` at `62fb7bc`). After that: the maintainer's
AcDs/constructed-content session(s) landed and REVERTED (codec
restored at the `7a7bd91` state — `96a2d6c`; their docs stand), and
the 2026-09-25 PLAN SESSION added the §19 campaign docs (see the
plan-session inventory below) — check `git log origin/gold-vs-silver..HEAD`
for the current unpushed set and push when the maintainer asks.

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
