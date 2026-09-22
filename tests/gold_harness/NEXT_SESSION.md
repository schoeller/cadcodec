# Zero-context prompt — BricsCAD strict-load campaign (COMPLETE)

> Campaign state 2026-09-21 ~21:45Z: **ZERO ACHIEVED, GOLD-TREE-SOURCED,
> AND USER-VERIFIED THROUGH ROUND SEVEN**.
> `gen_all_entities_all_versions.dwg` (AC1032/R2018, 30 entities,
> md5 0217fbac515a20b90e9c3aea883196e3) opens flawlessly in BricsCAD via
> plain `_open`. Every constructed-mleader wire component now derives
> from the gold tree (2018/Leader.dwg + gh44-error.dwg). This file is
> the post-campaign handover. New campaigns bootstrap from
> `tests/gold_harness/AGENTS.md` (durable rules), `IMPLEMENTATION.md` §7
> (the completed 0/0 fidelity campaign) and §18 (the validation layers
> incl. the layer-4 authored-wire byte-fidelity oracle).

## What the campaign established (do not re-derive)

1. **The strict consumer's real wire spec** is the BINARY convention set
   of the native writers, and it is derivable by byte-comparison:
   - BricsCAD message semantics: modal `Unable to load drawing ...
     Object improperly read: <Class> (N)` = parse-class FATAL at the
     first unparseable record, (N) = HEX handle; bare
     `Object improperly read (N)` = non-fatal deep-load drop.
   - **R2010+ LEADER records use the ODA underlap genus**: bitsize =
     main_end − 6, the no-text flag + handle region park back inside
     the main tail, and the overlapped bits double-read (the authored
     record's arrowhead RS16 tail + unknown_bit_4/5 coincide with the
     xdic form head `00110` by construction). The sequential layout
     parses clean in gold/both strict-blind decoders but BricsCAD
     deep-drops it. Silver now writes the underlap (`set_underlap_tail`
     merge hint, value-preserving-guarded).
   - **R2010+ MULTILEADER records carry a hidden tail bit-group**
     between is_text_extended and the string-stream anchor — a
     CONTENT-CLASS convention (2026-09-22 specimen-stamp census), not a
     writer fingerprint: fresh simple-content mleaders (BricsCAD +
     AutoCAD samples, gh44-error.dwg) carry the constant 9-bit
     `0b000010010`, while the gold tree's Leader drawing family carries
     the 17-bit `00100101000010010` whether saved by AutoCAD 2017/2018
     (the 2007/2010/2013 down-saves, per their SummaryInfo stamps) or by
     the ODA FileConverter (the 2018 variant reproducing them). Silver
     captures-and-echoes on rewrite and defaults constructed entities
     to the simple-content 9-bit (BricsCAD-verified round seven; copying
     the 17-bit onto constructed content made BricsCAD's parser reject
     the record — round five).
   - **Every authored AcDbMLeader carries the entity-common
     proxy-graphics metafile** (the "preview" in gold's trace / the
     `graphic_data` common field): `[u32 total][u32 count]` + records
     `[u32 size][u32 type][payload]`. Census from four specimens
     (authored 2018/Leader.dwg 564 B; mleader_bcad.dwg 448 B;
     mleader_acad.dwg 636 B; gh44-error.dwg): types 18/19 = property
     selectors (dwords 0x3999/0x399A/0x2711/0x1389/1/0x7FFF),
     20/22/23/51/16 = state toggles, 38 = geometry block (f64 pairs +
     zero padding), 6/7/32 = indexed blobs, 21 = FillOff,
     36 = UnicodeText — ODA spec §29 "PROXY ENTITY GRAPHICS" (p. 270;
     the PDF renders that section's body as images, but the envelope
     and types derive cleanly from the specimens).
2. The byte-oracle methodology that closed the campaign: trace gold
   (-v9), dump records (`dump_section_bytes`), bit-compare per-record
   with the corrected frame (window = [Address..Address+Size) from the
   BOT byte; MS at Address−3, UMC at Address−1; bitsize =
   Size*8−Hdlsize = handle-region start), and chase every divergence
   to a named field/form. Silver's rewrite of 2018/Leader.dwg now
   reproduces both problem records BYTE-IDENTICAL (CRC included).

## Specimen origin census (2026-09-22, for future triage)

Each R2004+ gold specimen self-identifies in its `AcDb:SummaryInfo`
ProductInformation string. For specimen triage, attribute bytes by the
origin stamp plus content class — never by "the ODA file said so":

| family | writer stamp | notes |
|---|---|---|
| `2018/Leader.dwg` + the named specimen set (Line, circle, Point, Arc, Ellipse, Spline, Text, Polygon, Donut, Helix, Multiline, Polyline, PolyLine3D, RAY, ConstructionLine, Constraints, Leader, …) | **ODA FileConverter** `Teigha® build 2.0 / registry 4.3, install "ODA"` | 2018/Leader's comments: *"last saved by an Open Design Alliance (ODA) application"* |
| `2007/2010/2013/Leader.dwg` down-saves | **AutoCAD 2017** `N.51.M.5 reg 21.0` / **AutoCAD 2018** `O.48.M.294 reg 22.0` | same drawing as the 2018 variant; SAME wire conventions (17-bit group, underlap) — the conventions are content-class, not writer-class |
| `gh44-error.dwg`, ATMOS-DC22S, gh109_1, `sample_2018`, `LiveSection1`, `example_*` | **AutoCAD**, various builds (C.608.0/17.2, M.x/20.1 2015-era, O.48.M.294/22.0) | 2015-era genera (sequential LEADER tails, 9-bit group on fresh mleaders) |
| `2000/` and `2004/` dirs | no marker in the format | provenance decidable only structurally |

The published ODA spec undersides all of these runtimes (hidden tail
groups, underlap, proxy-graphics metafiles undocumented) — full detail in
README "Origin quality of the gold specimens".

## Verified fix set (committed at this halt)

Committed 2026-09-21 ~22:05Z as
`66c1e57` (fix(dwg): strict-consumer wire compatibility — leader
underlap, mleader tail group, alpha 2-form) and
`bfa0ed8` (feat(harness): proxy-graphics derivation — typed state
records, gold-tree fixture, dump_proxy_graphics bin), with this docs
fold as the third commit of the set.

- `src/types/transparency.rs` — CMC alpha 2-form (authored census).
- `src/entities/multileader.rs` — `dwg_raw_tail_bits: Option<(u64,u8)>`
  capture-echo + native 9-bit default in `new()`.
- `src/io/dwg/dwg_stream_readers/merged_reader.rs` — `main_data_end()`
  + `peek_window_bits()` (tail capture support).
- `src/io/dwg/dwg_stream_readers/object_reader/entities.rs` — the
  R2010+ tail capture between main cursor and string anchor.
- `src/io/dwg/dwg_stream_writers/bit_writer.rs` — readbacks
  (`bits_at`, `first/last_written_bits`).
- `src/io/dwg/dwg_stream_writers/merged_writer.rs` —
  `underlap_bits` + `set_underlap_tail()` + the value-preserving merge
  hook.
- `src/io/dwg/dwg_stream_writers/object_writer/entities.rs` —
  `write_multileader` native group emission + tail;
  `write_leader` underlap request.
- `src/io/dwg/dwg_document_builder.rs` — capture wiring.
- `src/entities/mesh.rs` — `compute_edges` BTreeSet (deterministic
  generation).
- `examples/gen_all_entities_all_versions_dwg.rs` — the mleader
  proxy-graphics blob: **default =
  `MLEADER_PROXY_GRAPHIC_ODA`** (the gold tree's 564-B
  2018/Leader.dwg specimen, round-seven BricsCAD-verified) with
  `GENALL_PROXY_BLOB=bcad` selecting the round-six BricsCAD 448-B
  fallback (`MLEADER_PROXY_GRAPHIC`), + native stance (attach
  0/32/4786, extended=1; also present in the gold tree's gh44).
- `tests/roundtrip.rs` — r2000 filter for the
  version-inherent `dwg_raw_tail_bits` diff.
- `tests/gold_harness/normalize_silver.py` — pops
  `dwg_raw_tail_bits` (entity arm + payload loop) and `graphic_data`
  for MultiLeader.
- `tests/gold_harness/IMPLEMENTATION.md` §18.4 — the full resolution
  record.

## Handoff artifacts (repo root, all regenerated & deterministic)

- `gen_all_entities_all_versions.dwg` — 24986 B, md5
  0217fbac515a20b90e9c3aea883196e3 — the ZERO file in its round-seven
  form (30 entities, the gold-tree ODA blob as the default since the
  round-seven BricsCAD verification). The default generation is
  byte-identical to the user-tested `gen_all_mleader_oda_blob.dwg`.
- `gen_all_mleader_oda_blob.dwg` — the round-seven test artifact
  (byte-identical to the canonical; kept as the tested byte-record).
- `gen_all_all_but_mleader.dwg` — 24507 B (29, LEADER clean at 0x41).
- `gen_all_no_leader_no_mleader.dwg` — 24283 B (28, the control).
- `gen_all_rewrite_authored_2018_leader.dwg` — silver's byte-oracle
  rewrite (LEADER 0x72E / MTEXT 0x731 / MULTILEADER 0x732 all
  byte-identical to the authored records).
- User-provided native samples (KEEP): `mleader_bcad.dwg`,
  `mleader_acad.dwg` — the byte-oracles for native conventions. The
  example's `GENALL_PROXY_BLOB=bcad` fallback selects the round-six
  BricsCAD specimen.

## Follow-up opportunities (none block the zero)

1. **DONE (derivation layer)**: `src/entities/proxy_graphics.rs` now
   types the 12-byte state/selector records (`State { record_type,
   value }`; census selectors 0x3A99/0x3A9A/0x2711/0x1389) with the
   full format + type table in its module docs, the gold tree's own
   564-byte 2018/Leader.dwg AcDbMleader metafile is the embedded
   derivation fixture (decode→encode asserted byte-identical + census
   shape tests), and `dump_proxy_graphics [--verify] FILE [HANDLE]`
   derives the table live from any DWG (verified byte-identical on
   the gold specimen, mleader_bcad/mleader_acad, and the zero-file's
   own record; the gold file's IMAGE type-6 clip polygons decode the
   same way). **Remaining future step**: a content-synthesizing
   generator (model the type-38 header block + 6/7/32 geometry) to
   replace the example's borrowed `MLEADER_PROXY_GRAPHIC` specimen.
2. **DONE (committed 2026-09-21 ~22:05Z)**: the campaign landed as
   `66c1e57` (writer fixes + example + harness arm) and `bfa0ed8`
   (proxy-graphics derivation) plus this docs fold commit. The
   untracked scratch (examples/cylinder_dwg.rs, the .ocs.lock files)
   stays untracked; all *.dwg artifacts are gitignored by the
   established rule and regenerate from the committed tree.
3. The mleader's content stance (attach trio, extended flag) in the
   example now mirrors the natives; the remaining value-differences
   (text "Label" vs the borrowed "bla"-shaped blob) are invisible to
   strict load.

## Environment (unchanged)

Repo in WSL at `~/work/cadcodec`; gold tree at `~/work/libredwg`
(read-only); run via `wsl.exe -d Ubuntu-24.04 -- bash <script>` with
the quoting caveats (write scripts with the write tool, run by
absolute path; heredocs via `wsl.exe -c` BREAK; `read` tool offset
unreliable on UNC paths — use `wsl.exe -- sed -n`). Probes live in
`target/probes/pk30_*` … `pk34_*` (the campaign's analysis toolchain).
