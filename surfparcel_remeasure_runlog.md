# SURFPARCEL post-stack re-measure runlog (W3-1 / W4-1 ledger item) — wt_a

Base: parity/units-header @ a39b3c05 (POST-STACK: packet-C C-2/C-3/C-4 +
packet-D + D-1 profile-bands + D-2 units-header + upstream/main d7c71f50).
Data branch (created off a39b3c05, pushed at end): parity/surfparcel-remeasure.

Oracles (read-only copy pattern, md5-verified against C:\Program Files\
Autodesk\AutoCAD 2027\...\Civil Tutorials\Drawings, chmod 444):
- /tmp/opencode/surfparcel_work/Labels-Parcels.dwg  6b09621f6847aa434f99d1ba3cc6af6c
- /tmp/opencode/surfparcel_work/Parcel-2C.dwg       d17f2a95e7dbb8835338784de9803ab5

Recorded (pre-stack) marks:
- W3-1 Labels-Parcels: 54 oracle parcels / 17 built / 38 refused
  (corpus/gap_log_packet3.json; refusal: "the line crosses or touches a
  member it may not meet")
- W4-1 Parcel-2C: 11 oracle parcels / 1 built / 11 manifest refused of 12
  attempts (site record attempt included) → 10 of the 11 real parcels
  refused (corpus/gap_log_packet4.json, gap_closure_d017.json)

## STATE SNAPSHOT (2026-11-28T00:00Z — setup)
- Slot verified on a39b3c05, no branch switch (per dispatch). Data branch
  created at push time off the same HEAD so the measured tree is the
  working tree.
- Oracle copies md5-verified. Disk 35G free (floor 15G OK). wt_a/target
  warm (11G) from the D-2 round on this same tree.
- corpus/gap_log_figsite.json re-read: D018-2 context — Survey-3's 163
  "parcel outlines" were artifacts of site-record proxy graphics; Parcel-2C
  11/12 records carry a site ref, Labels-Parcels 54/55.

## STATE SNAPSHOT (2026-11-28T00:05Z — phase 1: post-stack analyze + build)
- Example rebuilt on the tree (features serde,import; sccache; 4m12s).
- analyze Labels-Parcels: families [block_record 40, site 1, parcel 54,
  parcel_segment 55], gaps 0; codec_census {AECC_PARCEL_SEGMENT:55,
  AeccDbFace:55}; header_units 6/1. All 54 parcel outlines decode as
  closed rings (ring_closed 54/54), zero empty-vertex items.
- analyze Parcel-2C: families [block_record 33, site 1, parcel 11,
  parcel_segment 30], gaps 0; census {30,12}; header_units 2/0;
  ring_closed 11/11; 8/30 segments stored without a graphic-image section.
- build Labels-Parcels → 54 parcel attempts: **11 built / 43 refused**
  (all "the line crosses or touches a member it may not meet").
- build Parcel-2C → 11 parcel attempts: **1 built / 10 refused** (same
  reason). W4-1 mark stands exactly.
- Built-file census (codec decode of the built files):
  labels_parcels.built {AeccDbFace:12, AECC_PARCEL_SEGMENT:66};
  parcel_2c.built {AeccDbFace:2, AECC_PARCEL_SEGMENT:31}.

## STATE SNAPSHOT (2026-11-28T00:20Z — phase 2: reconciliation of 17/38 → 11/43)
- Decoded parcel vertices are BIT-IDENTICAL to the archived packet-3
  manifest (corpus/manifests/labels_parcels.json), order-aligned 54/54 —
  decode unchanged; delta must be writer- or flow-side.
- Archaeology: scratch worktree at parity/corpus-roundtrip@7f34345b (the
  recorded W3-1 base), example built (3m23s), analyze+build re-run on the
  same oracle copy → 55 attempts (site record included as parcel attempt
  #0, 'outline' = the site's bounding-box rectangle) / **38 refused / 17
  built — the recorded mark reproduces exactly on its own tree**.
- The junk bbox rectangle BUILT as attempt #0 and acted as a mid-sequence
  blocker ('Open Space : 7' refused early in the old run, built in the
  new run) — the built/refused split is a chaotic order-dependent cascade.
- PROOF of no writer regression: the POST-STACK writer fed the identical
  55-attempt sequence (hybrid manifest: site-record rectangle re-inserted
  at position 0) reproduces the packet-3 refusal sequence IDENTICALLY —
  same 38 parcels, same order (labels_parcels.hybrid.build.log).
- git diff 7f34345b..a39b3c05 on create/site.rs: the crossing gate
  (join_site_as paths_meet check) textually unchanged; range changes are
  proxy graphics, parcel names, feature_line_vertices, C-4 segment
  records — none touch the gate. Zero writer behavior change.

## STATE SNAPSHOT (2026-11-28T00:45Z — phase 3: reader cross-check)
- Probe (harness_a, read-only): census confirmed; AECC_SVFIGURE = 0 in
  BOTH files (the crossing-figure subclass of D018-2 is empty here).
- Site containers: Labels-Parcels 0x4676, Parcel-2C 0xC38 — both
  AECC_FEATURE_STYLE. Topology walk (instrumented temporarily, reverted;
  tree verified clean at a39b3c05): elevation_keys ok → elements ok →
  gate 0x80000001 ok → node_list reads **0 nodes** (moved-members form) →
  edges walk refuses. **The app's stored post-interaction boundary pieces
  (split lot lines + faces) do NOT decode on parcel sites** — READ gap;
  the topology reader was validated on feature-line/grading containers
  only (Grading-3A et al.).
- On what IS stored: rings 54/54 + 11/11 decode closed; ring-vs-ring
  sharing (corrected parallel-segment test): Labels-Parcels 208/1431
  parcel pairs share an edge/vertex; Parcel-2C 19/55. The app stores the
  shared pieces ONCE (54 parcels vs 55 lot lines; 11 vs 30) → per-record
  rings drawn through shared coordinates ARE the post-interaction
  boundaries → the READER's reconstruction is faithful; the residual
  lives on the WRITER side's representation (independent closed lot lines
  per ring duplicate shared pieces).
- Refusal replay (the writer's gate re-modeled): reproduces 11/43 and
  1/10 exactly. Classes: Labels-Parcels 42/43 refused rings PROPER-cross
  previously-built members, 1/43 (Single-Family : 24) touch-only;
  Parcel-2C 10/10 proper. Unsupported record form: 0. Other: 0.
- Nuisance recorded: Parcel-2C parcel names decode empty (stored empty;
  app reads 'ROAD (LOCAL): 100' via the style name template; the new
  parcel_name() also evaluates to no name in this probe) — flagged,
  separately dispatchable, not a refusal cause.

## STATE SNAPSHOT (2026-11-28T01:00Z — phase 4: verdict + push)
- D018-2 VERDICT: the WITH-LIMITS marks stand in substance; the refusals
  are WHOLLY CORRECT behavior for this writer form (52/53 proper
  interactions with already-placed members, 1 shared-edge touch; no
  survey figures in either file; 65/65 outlines decode).
  - Labels-Parcels restated: 54 oracle parcels / 11 built / 43 refused
    (the recorded 17 included the site-record junk attempt and its
    cascade; reproduced 17/38 exactly at 7f34345b, and identically with
    the post-stack writer at the same attempt set).
  - Parcel-2C stands exactly: 11 / 1 / 10.
- Implementable D015-clean improvement (NOT implemented, re-measure
  round): a meet-aware add_parcel reusing create/site.rs' existing
  add_lot_line_on(meet=true) split machinery; whether it reproduces the
  oracle's exact population needs its own dispatched verification round.
- Gap log: corpus/gap_closure_surfparcel_remeasure.json; manifests
  refreshed (labels_parcels.json, parcel_2c.json — now carry header_units
  per D-2). Pushed as parity/surfparcel-remeasure to origin
  (schoeller/cadcodec).
- Full cargo test NOT re-run: data-only branch (JSON + runlog), no source
  change vs a39b3c05 (which shipped the D-2 round's 3429/0 suite).
