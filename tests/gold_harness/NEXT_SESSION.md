# Zero-context prompt — gold-vs-silver roundtrip harness (next session)

> Paste this whole file into a fresh session to continue the gold-vs-silver
> roundtrip-fidelity work with no prior context. It is the cold-start brief.
> Replace this file at the next halt (fold landed outcomes into
> IMPLEMENTATION.md §7 + §8.1.6 first).

## Task

Continue the acadrust gold-vs-silver roundtrip harness. The campaign target
(2026-09-20, raised) is read AND write **0** on BOTH sides — land every
remaining family, including the heavy pockets; do not stop at an interim
milestone. Current baseline (2026-09-20, after fix commit `b2955a7` + its
docs commits `2d52ba1`/`0bc2f78`): read **479** / write **455**
(124 corpus files; gh44-error.dwg explicitly out of scope via
`run_corpus.in_scope_files`; gh109_1/gh209_1 ARE in scope).

**Decisive census fact: 98 of the 124 corpus files are ALREADY at 0/0.**
All remaining rows live in 26 files, and this brief carries a per-file,
per-family inventory with gold↔silver key maps captured verbatim from the
fresh artifacts — most remaining families are rename/projection work whose
diagnosis is already done below. Work the levers in the order given; each
one cites its carriers, row counts, kind, and recipe.

**Staleness rule:** re-read `target/gold_harness_corpus/report.json`
(`read/write_fidelity_by_type_field` + per_file) after every landed batch;
families self-resolve as side effects and counts shift fast now.

## Read these first (in order)

1. `tests/gold_harness/AGENTS.md` — durable rules: gold is read-only, grep
   BOTH `dwg.spec` and `dwg2.spec`, verify class-block liveness
   (preprocessor frames, §8.1.1) before any retype, version-gate every
   conditional, differ/ignore-list frozen, regression gates, commit
   conventions.
2. `tests/gold_harness/IMPLEMENTATION.md` — §7 (baseline + Next packets),
   §8.1.0, §8.1.1 (liveness + frame map), §8.1.6 (DONE entries with the
   per-packet recipes of batches 7–23).
3. `target/probes/fullsrc/` — LibreDWG source parse + verbatim spec
   windows (`findings_notes.md` is the per-family spec index).
4. `target/probes/pk16a_full_census.py`, `pk16b_perfile.py`,
   `pk16c_keymaps.py` — THIS session's census/key-map probes; rerun them
   any time to refresh the inventory; their outputs produced the
   inventory below.

## Current state (2026-09-20, session handoff)

- HEAD `0bc2f78` on `gold-vs-silver`, pushed. Tree clean (untracked
  `examples/cylinder_dwg.rs` predates the campaign — leave it).
  Gates green: `cargo test --features serde` all segments ok (roundtrip
  97/0), `gold_roundtrip` ok.
- Corpus: read **479** / write **455**. Top carriers by read+write:
  TS1 178, gh109_1 130, Underlay(2004) 104, gh209_1 96, Surface(2004) 62,
  PolyLine2D 59, Dynblocks(2018) 46, example_2007 43, entities-2d/3d 72,
  LiveSection1 30, example_2013 23, example_2010 23, example_2018 17,
  example_2000 14, example_2004 13, Helix×4 16, Constraints×4 7, Cone 2.
- Batches landed 2026-09-20 (all fix+docs committed and pushed):
  7–14 (`fa2cb0a` PROXY, `b08d346` DIMSTYLE_CONTROL, `b6e6e92` LEADER,
  `45382ec` MULTILEADER attach trio, `b123b4c` TABLECONTENT, `fca5367`
  VERTEX_MESH, `fad3042` ACSH_CONE_CLASS, `543f877` WIPEOUT reactor codes),
  15 `689b14d` SEQEND real handles, 16 `263ab5f` VIEWPORT.status_flag raw,
  17 `9f06d89` LEADEROBJECTCONTEXTDATA retype, 18 `a7e451b` TOLERANCE names,
  19 `257895a` smalls batch, 20 `91e72a3` TRACE/SOLID split, 21 `e90fb77`
  graphic_data pops, 22 `ab0e02f` SORTENTSTABLE.ents, 23 `b2955a7` SURFACE
  retypes + PLANESURFACE projection.

## The route to zero — complete inventory (per lever, counts read+write)

Each lever = one or more packets. Row counts are the CURRENT true per-file
numbers. All shapes below are captured from the fresh pooled artifacts
(these carriers are single-version or collision-free stems — pooled is
fresh) plus `pk16c` gold-raw vs silver-payload key dumps.

### L1. TS1 FIELD object family — ~44/44 rows (biggest single TS1 mass)
4 FIELD records (dwg.spec FIELD / FIELDLIST; the class is OBJECT ACDBFIELD).
Pure name-remap, all field pairs OBSERVED:
`id ← evaluator_id` (gold "id":"_text" == silver evaluator_id), `field_state
← state`, `evaluation_error_msg ← evaluation_error_message`, `value.data_type
+ value.data_long ← value` (silver nests {data_type,data_long}; gold emits
two dotted fields), `childs (BL) ← len(child_fields)` + `childval ←
child_values`, `code/format/evaluation_error_code/evaluation_option/
filing_option/value_string/value_string_length` keep names. POP silver-only:
`referenced_objects`, `state/evaluator_id` twins after rename. Also
`FIELDLIST.fields` wrong_value (1): the FIELDLIST owns the FIELD handles —
emit the resolved list in gold's order. Recipe: objects-loop branch keyed on
silver_type == "Field"-ish payload name (find it in the silver dump: keys
exactly as listed; grep normalize_silver for the current FIELD emission if
one exists — the rows show it emits under silver names).

### L2. gh109_1 PLOTSETTINGS — ~45/45 rows (single record, pure rename)
Gold record keys (33): printer_cfg_file, paper_size, plot_flags,
left/bottom/right/top_margin, paper_width/height, paper_image_origin,
plot_origin, plot_paper_unit, plot_rotation_mode, plot_type, plot_window_ll,
plot_window_ur, plotview, shadeplot [4 subfields: type/reslevel/customdpi],
std_scale_type, std_scale_factor, stylesheet, canonical_media_name,
drawing_units, paper_units. Silver emits the SAME record under different
names (extra_in_silver rows show them): printer_name, page_name, margins,
origin_x/origin_y, rotation, scale_numerator/denominator, scale_type,
shade_plot_mode/resolution/dpi, current_style_sheet, visual_style_handle,
plot_view_handle/name, cached_scale, standard_scale_factor, flags, …
Task: find the emitting branch (grep `printer_name` in normalize_silver —
the PLOTSETTINGS record is emitted from a layout/plot section), then land a
field_map rename projection (one record, ~45 fields, ~130/2 of the file's
mass). Value-verify each rename pair before committing (margins dict → four
fields; shadeplot group; paper_image_origin → _x/_y variants).

### L3. gh209_1 GEODATA — 48/48 rows (single record, pure rename + pops)
Gold keys: class_version, coord_type, design_pt, ref_pt, unit_scale_horiz,
units_value_horiz, unit_scale_vert, units_value_vert, up_dir, north_dir,
scale_est, do_sea_level_corr, sea_level_elev, coord_proj_radius,
coord_system_def (R2010 file; gold also has geo_rss_tag/host_block/
observation_* tags which silver already matches). OBSERVED rename pairs:
`class_version ← version`, `coord_type ← coordinate_type`, `design_pt ←
design_point`, `ref_pt ← reference_point`, `up_dir ← up_direction`,
`north_dir ← north_direction`, `unit_scale_horiz ← horizontal_unit_scale`,
`units_value_horiz ← horizontal_units` (same -vert), `scale_est ←
scale_estimation_method`, `do_sea_level_corr ← sea_level_correction`,
`sea_level_elev ← sea_level_elevation`, `coord_proj_radius ←
coordinate_projection_radius`, `coord_system_def ←
coordinate_system_definition`. POP silver-only extras (gold's R2010
normalized record LACKS them): obsolete_observation_point,
obsolete_scale_vector, coordinate_system_datum, coordinate_system_wkt,
mesh_points, mesh_faces, civil_* (13 keys). Check gold's GEODATA spec block
for whether wkt/datum/mesh are era-gated (value-gate rule) before popping
unconditionally.

### L4. Underlay PDFUNDERLAY + PDFDEF — 52/52 rows
(a) 3 PDFUNDERLAY entities × 17 fields, pure rename (OBSERVED): `ins_pt ←
insertion_point`, `angle ← rotation`, `flag ← flags` (bit composition —
value-verify), `clip_verts ← clip_boundary_vertices`, `definition_id ←
definition_handle`, `scale ←?` (gold has ONE `scale` + contrast + fade;
silver carries x_/y_/z_scale — pull the row VALUES to see which pair and
how the three map), `underlay_type` extra → pop. The existing Underlay
branch (normalize_silver, `underlay_type` kind retyping) already names the
type; extend it with the full field map.
(b) PDFDEF/PDFDEFINITION objects: gold emits ONE AcDbUnderlayDefinition
object (filename "../../../dxf.pdf", name "1"); silver emits ZERO — the
record is dropped or hidden under a wrapper. Find where silver parses
underlay definitions (grep src/objects for PdfDefinition/UnderlayDefinition,
likely under a DataObject/RegisteredClass wrapper or document-level dict),
then retype+project (filename/name/ownerhandle common).

### L5. TS1 OLE2FRAME — 11/11 rows (single record, mostly reader-capture)
Gold AcDbOle2Frame keys: mode, data (315KB hex string!), plus common
(lock_aspect etc.). Silver payload: version, source_application,
ole_object_type, is_paper_space, dwg_mode (≈gold mode?), lock_aspect,
upper_left_corner, lower_right_corner, envelope, storage — it parses a
STRUCTURED Ole wrapper but gold keeps `data` as the RAW OLE blob hex
(805540F9…) plus `mode`. Gold's normalized record поля: mode/data only
(+common). So: project mode ← dwg_mode; `data` needs the RAW OLE bytes —
check whether silver's storage/envelope payloads contain the raw byte
stream (reader capture candidate; if not stored, the reader must retain
the raw data like the PROXY window precedent — Ole2Frame reader in
entities.rs). POP: version/source_application/ole_object_type/
is_paper_space/corners/envelope/storage (gold normalized lacks them —
verify against gold raw first).

### L6. TS1 POLYLINE_MESH — 17/17 rows (single mesh, parent-field names)
Gold AcDbPolygonMesh keys: flag (=16 POLYGON_MESH closed bits — value-
verify), curve_type, m_density, n_density, first_vertex, last_vertex,
seqend (pre-2004 chains — R2000 file), common. Silver payload: flags
("POLYGON_MESH" enum string), m_vertex_count, n_vertex_count,
m_smooth_density, n_smooth_density, smooth_type, elevation, vertices,
seqend_handle. Mapping: `flag ← flags` (enum name → gold raw bits;
POLYGON_MESH→16 per gold's value), `m_density ← m_smooth_density`,
`n_density ← n_smooth_density` (BOTH verify by value on all records;
silver's m_vertex_count 3/n_vertex_count 4 are the M×N grid COUNTS which
gold's normalized record drops — pop), first_vertex/last_vertex from the
kid records' first/last handles (the pre-2004 chain — same machinery as
the seqend synthesis: kid handles are real in silver now), `seqend ←
seqend_handle` ✓ pop the rest. NOTE the kid-synthesis block already
computes `_seq_h_parent` — extend to emit the parent chain fields for the
pre-2004 era only.

### L7. Surface MESH family — 26/26 rows (2 subdivision-mesh records)
Gold AcDbSubDMesh keys: vertex, edges, faces, crease, dlevel,
is_watertight, unknown_b1, unknown_b2 (+preview blob). Silver payload:
version, blend_crease, subdivision_level, override_option, edges, faces,
vertices. Renames: `dlevel ← subdivision_level`, `crease ← blend_crease`
(bool→gold's crease form — value-check), unknown_b1/b2 ← version/
override_option (2 unknown Bs — diff gold's spec dwg2.spec MESH block for
the two unnamed B fields' order), `is_watertight ← ?` (reader gap if silver
doesn't store it — check silver's Mesh reader), `vertex ← ?` (gold's
`vertex` is likely a degenerate [0]*n or handle vector — pull the row
value). edges/faces wrong_value: gold's normalized arrays vs silver's —
compare SHAPES (gold may collapse vectors per the [0]*n pattern).

### L8. Underlay-era + example-era small gates — ~60 rows total across files
- `DIMENSION_*.class_version` extra_in_silver (example_2007: LIN 4+ORD 3+
  ALIGNED/ANG2LN/ARC_DIM 1 each; single-dim pop or era gate — gold's
  normalized DIMENSION records lack class_version on these versions).
- `SEQEND.shadow + shadow_flags` (example_2010/2013 orig 2+2 each,
  SEQEND.plotstyle + plotstyle_flags example_2004 2+2): the SEQEND
  synthesis emits post-2004 common fields the era gates exclude — gate
  shadow R2007+ style / plotstyle R2004+ per the era; find which gate the
  synthesis lacks (compare with how gold gates shadow on SEQEND wires —
  the rows are silver-only emissions).
- `LWPOLYLINE.plotstyle/material` (example_2007 4+1+1+1…, example_2010/13
  1 each): era-gated entity-common emission.
- `POLYLINE_3D.flag` (7 files, 1+1 each; example_2000/04/07/10/13/18 +
  PolyLine-ish): one bitfield expression differs — pull one row's values
  and fix the 3D branch's flag composition (bits vs gold's raw BL).
- `POLYLINE_PFACE.vertex/first_vertex/last_vertex` (example_2004/07/10/13/
  18, 3+3 each): gold's PFACE parent emits `vertex` (the R2004+ vertex
  REPEAT — likely degenerate [0]*n) + first/last_vertex (pre-2007 only for
  2004/2007 files?? — per-era: 2004/2007 rows show first/last extra or the
  2010+ files show vertex missing — split accordingly).
- `VERTEX_3D.reactors` (6 files ×1): synthesized 3D kids lack reactors —
  silver's V3D assembly drops per-vertex reactor lists; add builder
  retention (PendingVertex payload) or emit [] in synthesis per gold's
  shape (check gold's raw — VERTEX_3D records carry reactors lists).
- `MTEXT.text` (3 files wrong_value): one mtext's text differs — likely a
  column/formatting normalization (gold decodes the same string — compare
  and align char for char).
- `VIEW.VIEWMODE / VIEW.camera_plottable / VPORT.VIEWMODE` (LiveSection1
  2+2+…, example_2000, PolyLine2D, example_2018 LIVE...): VIEW entity's
  VIEWMODE bit composition + a VIEWMODE header-field pop.

### L9. entities-2d/3d: SHAPE + TEXT-family — ~36/34 rows (both files identical)
SHAPE renames (OBSERVED): `ins_pt ← insertion_point`, `scale ←
relative_x_scale`, `style_id ← shape_number` (gold style_id 131 ==
silver shape_number 131), `style` = a HANDLE field gold emits style
handle — silver style_handle 56 (normalize_handle_value), `rotation`,
`oblique_angle`, `thickness` keep names; POP silver-only:
shape_name/style_name/size (silver "size": 1.0 is the scale twin —
verify). Gold's `width_factor` and `extrusion` need checking: width_factor
missing_in_silver — silver's Shape model may lack the field (READER GAP —
grep read_shape; the wire carries BS per dwg.spec SHAPE block) → reader
capture or normalizer from payload (silver keys list has no width_factor).
TEXT/ATTRIB/ATTDEF family (~5 rows/file): `dataflags` wrong_value (the
TEXT-era bitfield composition), `elevation` missing_in_silver pre-2004
(silver stores under common?), `alignment_pt` missing (pre-R2010
secondary point — check payload key (maybe in common or a derived
"alignment_point") + `ATTRIB.width_factor/xdicobjhandle` TS1 singles.

### L10. Dynblocks — 23/23 rows
(a) `LWPOLYLINE.flag` 6 wrong_value: the branch builds flag from
is_closed(512)+plinegen(256) — gold's raw flag carries MORE bits (pull a
row: e.g. 8/16 const_width-present, 70-flag group) — fix the composition
against gold's values (six records).
(b) `LWPOLYLINE.vertexids` 6 wrong_value: gold emits a vertexids vector
(likely [0]*n degenerate — verify) — silver emits something else.
(c) `SPLINE.ctrl_pts` 6 wrong_value: compare gold's normalized ctrl_pts
(list-of-triples?) vs silver's control_points — likely container shape
(degenerate or dict-vs-triple) — normalize_value already converts dicts;
probably a [0]*n degenerate or scenario-gated subset (silver includes
fit_points? no row for those...) — pull the values.
(d) `ASSOC2DCONSTRAINTGROUP.nodes` 2 wrong_value: the nodes handle-vector
order/values — compare.
(e) `BLOCK_HEADER.xref_pname` 2 + `BLOCK_HEADER.name` 1: block-header
field values (gh109_1 also has BLOCK_HEADER.name 3+3 — same family:
grep the block header emission; names differ (db-space encoding?) —
compare values).

### L11. PolyLine2D.dwg — 26/33 rows
(a) `POLYLINE_2D` 2 records × 9 fields: same parent-field family as L6:
`flag ← flags` ("POLYLINE_2D" enum → gold's raw flag — gold shows flag 0 +
curve_type 0 here; silver flags "POLYLINE_2D" → probably 0 too BUT the
rows say missing flag/curve_type + extra flags/smooth_surface — mapping:
flag ← flags-bits, curve_type ← smooth_surface (NoSmooth→0)), first/last/
seqend from the chain/kid machinery (same as L6), POP vertices/silver-
only. NOTE `POLYLINE_2D.vertices` extra_in_silver — silver's normalized
record carries the vertices list while gold's does not (gold's parent
raw has no vertices key) — pop from the PARENT record (kid records stay).
(b) `BLOCK_HEADER.first/last_entity` wrong_value (3) + `LINE.handle` (1):
pre-2004 chain pointers — verify the block-chain emission (the
first/last_entity of BLOCK_HEADER entities — ordinal mismatch upstream?).
(c) `LAYOUTPRINTCONFIG._count/_missing` (1+1): dropped record — find
silver's wrapper (like PDFDEF: grep the parse; layout print config class
is probably parsed but unexposed).
(d) `VPORT.VIEWMODE` + `VIEWPORT.vport_entity_header` (rt) + UNKNOWN_ENT
1 missing: small residue — diagnose after (a).

### L12. LiveSection1 — 16/14 rows
SECTION trio recipe (§ queue above, unchanged): MANAGER trivial kind-map +
is_live/sections; SETTINGS REPEAT projection (gold's settings REPEAT is
large — read dwg2.spec SECTION_SETTINGS block from fullsrc; side channel
already holds the tail); SECTIONOBJECT entity = heavy (full AcDbSection
wire + 188-byte preview) — model fields or common+preview projection.
Plus `VIEW.VIEWMODE 2 + has_ds_data 2` + `BLOCK_HEADER.entities 1` —
VIEW gold gates. UNKNOWN_OBJ._missing 2: the SETTINGS/MANAGER records
counted as silver extras until the retypes land — rows die with the trio.

### L13. RAPIDRTRENDERSETTINGS (gh109_1) — 7/7 rows — gold-parity parse
Recipe unchanged from the queue: silver parses CLEAN
(version/render_target 0/render_level 1...) where gold mis-decodes garbage
(849379356/-6.1e+201...) past the AcDbRenderSettings base; land a
gold-bug-compatible read (diff the field counts/gates between gold's
AcDbRenderSettings_fields+RAPIDRT block vs silver's read_render_settings;
also gold has_predefined gate VERSION (R_2013){} vs silver's unconditional
read), then ClassObject kind→RAPIDRTRENDERSETTINGS retype + projection
(base + 7 rapid fields + has_predefined).

### L14. Surface PLANESURFACE residue — 4/4 rows
acis_data (SAB boundary: compare silver's emitted [head, hex-rest] vs
gold element 1 char-for-char — likely off-by-N the NUL or hex case),
acis_empty_bit (gold 1 — set 1 when data present), modeler_format_version
6-vs-1 and v_isolines 8-vs-6 (silver's Plane reader misparses two wire
fields — find the exact divergent reads against the PLANESURFACE spec and
fix the reader; values land for free). Plus rt-side
ASSOCPLANESURFACEACTIONBODY.assocdep/pbsab_status (2 rows rt-only): the
actionbody projection details.

### L15. gh109_1 SORTENTSTABLE nulls — 2/2 rows (orig only)
Gold's sort vectors KEEP null (0,0) pairs at ~3 indices in the 1045
table; silver's sort-table reader drops most (kept exactly ONE at idx 3),
shifting ordinals. Reader fix: retain zero pairs in `entries` (silver's
SortEntitiesTable payload); the emission then flows.

### L16. encr_sat_data (3DSOLID/REGION) — 8/8 rows (Cone 1, example_2000
3, TS1 2, plus example_2004 1 REGION)
Gold emits `encr_sat_data` (encrypted SAT blob) which silver never
stores — silver keeps `acis_data` (SAB/SAT) but drops the encrypted
variant. Check gold's spec (dwg2.spec _3DSOLID/REGION: encr_sat_data
field with its own gate) and silver's 3dsolid reader — retain the blob
(reader capture, struct field, writer echo, normalizer emission), or if
silver's dump already carries it under another key (grep sat/encr keys),
project. This is a reader-capture packet like the previous ACIS-adjacent
ones (version-gate per era).

### L17. Assorted singles (≈15/15 across Cone/TS1/examples/Helix/Constraints)
`VERTEX_2D.ltype_flags` (PolyLine2D rt 4) + `SEQEND.ltype_flags` (2):
pre-2004 ltype bits on synthesized kids — the 2D kid synthesis ltype
emission gate/value. `VERTEX_MESH.prev_entity` (TS1 1): chain field on
the mesh kids. `ATTRIB.dataflags` TS1 + DATAFLAGS family. Helix×4 (2+2
each — pull a pooled Helix diff; likely one HELIX field pair) and
Constraints×4 (1 each). TS1 `DIMENSION_ANG2LN.xline2end_pt` (1) — value
pair fix. example_2007 `VERTEX_3D.reactors` (in L8). Land these as one
"assorted singles" batch at the end.

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
commands through `wsl.exe -d Ubuntu-24.04 -- bash <script>` — wsl.exe
strips embedded quotes AND pipes (regex `\|` alternations die silently:
single search terms through wsl.exe, multi-pattern via the grep *tool*);
this PowerShell has NO `head` and rejects `&&`; put non-trivial shell and
ALL probe python into script files under `target/probes/`. The `read`
tool's `offset` is ignored on SOME UNC paths. To launch the corpus
detached: a script that nohups run_corpus.py with an ABSOLUTE log path
and sleeps ~8s before exiting; confirm the pid via pgrep BEFORE doing
anything else; a bare launch died once.)

## Workflow (per packet)

1. Pick the lever (L1.. in order — biggest first is fine, they are
   orthogonal; re-check the fresh report before starting).
2. Grep the gold spec: BOTH `dwg.spec` and `dwg2.spec` (R2000+ objects in
   dwg2.spec); check liveness frames (§8.1.1) before any retype; read the
   full block (macro + version predicate + value guards).
3. Locate the silver side; pull the row VALUES + both records from the
   fresh pooled artifacts (the carriers in this inventory are all
   stale-safe stems) into a fresh probe dir when in doubt.
4. Minimal, version-gated fix: prefer normalizer projections (the
   inventory shows silver already stores nearly everything); codec only
   when the data is not stored (L5 OLE data, L16 encr_sat_data, L15 null
   retention, L14 Plane reader bits). NEVER touch `diff_fields.py` /
   `ignore_fields.toml`.
5. `cargo build --features serde --bins`.
6. Verify per-file on all versions the family touches (fresh dirs).
7. **Run the corpus LAST**, detached; one bounded `24_wait.sh` call; no
   edits while it runs.
8. Gates: `cargo test --features serde` (count `test result: ok`
   segments) + `cargo test --features gold-harness --test gold_roundtrip`
   (ok). Deep-gate rule: any new raw-retention struct field gets a
   normalize_entity_for_comparison arm (seqend_handle/dwg_status_flag
   precedents).
9. Commit `fix(harness): <packet> — <gold spec ref> + before→after
   counts`, push, fold §7/§8.1.6 (DONE entry with recipe), docs commit,
   push. No backticks in commit-message bodies (bash command substitution).

## Hard-won lessons (do not repeat)

- **dwg2json/dwgread write `<stem>.json` beside the INPUT FILE by
  default** — always redirect or you WRITE INTO THE READ-ONLY GOLD TREE.
- **Write rows = rt-parser-parity pair (gold_rt vs silver_rt); read rows
  = orig pair; a family can be one-sided.**
- **By-type tables are top-N truncated + stem-inflated; per_file (FULL
  paths) is truth. 98/124 files are at 0/0 — per-file probing on the
  named carriers is all that remains.**
- **Families self-resolve as side effects — re-read the fresh report
  per packet; the per-file inventory below WILL go stale after each
  batch.**
- **A reader that eats more bits than its record carries desyncs
  downstream records in the same file.**
- **Raw-retention struct fields must mirror typed enum defaults at
  construction** (dwg_attach_*, status_flag, seqend_handle); the deep
  gate catches splits.
- **Retype by dxf_name/kind ONLY for LIVE blocks** (§8.1.1 liveness;
  dead: EXTRUDED/LOFTED/REVOLVED/SWEPT SURFACE, TABLE/TABLECONTENT,
  ASSOCSWEPTSURFACEACTIONBODY; live: Plane PLANESURFACE, TABLESTYLE,
  TABLEGEOMETRY). Retype must come WITH its field projection.
- **Fabricated constant handle codes are time bombs** (WIPEOUT lesson);
  the differ tolerates absent codes (None) when targets match — use
  normalize_handle_value(0).
- **Typing divergence poisons handle-vector resolution far away**
  (SURFACE mis-typing → SORTENTSTABLE/dep_on rows).
- **Gold-bug parity IS the truth** (RAPIDRT garbage; DXF-code-vs-wire
  orders; the spec block beats intent).
- **Entity-common serde-skipped fields ride `_common_dwg` into
  merge_common — pop from `fields` AFTER the merge.**
- **The `[0]*n` degenerate REPEAT** (gold collapses one value per record:
  PLANESURFACE wires, likely PFACE vertex / LWPOLYLINE vertexids).
- **Bitflags serde joins with " | " (split it); FIELD_CAST BS→BL
  zero-extends (0xFFCE=65486); MATERIAL rgb unsigned; wire codes
  SOLID 31 vs TRACE 32; GROUP wire names live in silver's `description`.**
- **Silver object payloads nest common under `common` inconsistently** —
  location-aware extraction or records silently vanish.
- **Never edit mid-corpus; never busy-poll; never trust pooled corpus
  dirs except the stale-safe single-version stems named here.**

## The commit / push convention

- Branch `gold-vs-silver`, tracks `origin/gold-vs-silver`.
- `fix(harness): <packet> — <gold spec ref> + before→after counts`, then
  a separate `docs(harness): …` commit once §7/§8.1.6 are updated; push
  after each. Batches 7–23 landed 2026-09-20 (see Current state for
  hashes) + the target-raise docs commit `0bc2f78`; the one carrying
  this file follows it.
