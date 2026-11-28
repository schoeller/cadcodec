# D017 PACKET F — the fix-regression packet (3 files × L1/L2/L3) — runlog

- Worker: D010 packet-F worker (per-file L1/L2/L3 + gap log + suite; NO PRs, data-only push).
- Binding: /tmp/opencode/worker_brief.md + dispatch (D017 PACKET F — THE FIX-REGRESSION PACKET).
- Protocol model: packetE_runlog.md (packets C/D precedents) — per file: L1 (analyze →
  census-gate → build → verify/ownership-guard → compare_verify) · L2 (readOnly app open +
  ctx invariants + read-only census/audit + close discardChanges:true) · L3 (oracle-vs-built
  app census equality — FULL EQUALITY is the standard).
- Branch: `parity/packetF` (worktree /tmp/opencode/wt_c), created from origin/parity/packetE
  @ **1ef1bfda** (pushed), then:
  - MERGE 1: `git merge origin/d010/e1-parcel-segment` (the E-1 fix, PR #728, tip 56b499ac
    "the parcel build adopts the file's parcel-segment record for its boundary") → merge
    commit **0424b3c1**. THREE content conflicts, resolved:
    - src/classes/civil/create/mod.rs re-export list: UNION (HEAD's packetE list incl.
      `add_parcel_segment_record` + the fix's `add_parcel_without_segment`).
    - src/classes/civil/mod.rs re-export list: UNION (same rule; `add_parcel_without_segment`
      inserted after `add_parcel_segment_record`).
    - src/classes/civil/create/site.rs `add_lot_line_on` body call line: took the FIX side
      (`…, meet, layer, member_record, record`) — HEAD's side was the always-record closure
      `|doc, common, edge, container| write_lot_line(doc, common, edge, container, None)`,
      i.e. the E-1 mechanism itself. The enclosing fn signature (with `member_record,
      record` params) had auto-merged from the fix branch, so the fix side is the only
      compiling resolution. (Precedent: packetE's merge ed2fcdb0 = unions of re-export
      lists; here one conflict was the mechanism line itself.)
  - MERGE 2: `git merge origin/d010/e3-minorstation-erased` (the E-3 fix, PR #730, tip
    328fcde3 "a minor-station label group points at its sibling station group") → CLEAN
    auto-merge (only src/classes/civil/create/alignment_labels.rs, +52 lines; commit
    **5dfa3a33**).
  - UPSTREAM: fetched; upstream/main still @ **d7c71f50** — NOT newer than packetE's merge
    base, so no upstream merge (dispatch: "merge it if newer" — it isn't).
- Env: RUSTC_WRAPPER=sccache, CARGO_PROFILE_TEST_DEBUG=0, CARGO_INCREMENTAL=0 on every
  cargo line. Disk at start 57 GB free (>15 floor).
- Harness note: harness_c intact, [patch] → /tmp/opencode/wt_c verified (Cargo.toml line
  12). L1 runs through the worktree's `examples/corpus_roundtrip.rs` — the packetE
  precedent (`cargo run --example corpus_roundtrip --features serde,import --release`;
  packetE runlog: "harness src/main.rs not used") — dispatch says "exactly packets C/D/E",
  so the harness main.rs (packet-C probe code) is left untouched and the proven example
  path is used; recorded here as the deliberate deviation from the dispatch's literal
  "rewrite src/main.rs" phrasing.
- Corpus: Civil Tutorials Drawings (D013 rule); oracle copies read-only (444) in
  /tmp/opencode/packetF_work/: Align-3.dwg c3a66f2a…, Align-4.dwg 7c1d7dcf…,
  Align-7B.dwg fb837719… — ALL md5-MATCH the tutorials folder byte-for-byte.
- Bridge: port 7900 ONLY; driver /tmp/opencode/ct/packetF_verify.py (packetE_verify.py
  pattern: takes /tmp/opencode/bridge.lock ITSELF — run BARE, never wrapped in CLI flock,
  the packetE self-deadlock lesson); attrib -r + verify before EVERY built-file open;
  oracle opens readOnly:true; close discardChanges:true; watcher loop (15 s) with
  C:\Temp\packetF\dismiss.ps1 (title/text match ONLY: 'newer version' / Civil 3D + proxy),
  log /tmp/opencode/ct/pktF_watcher.log; >3 min wedge = dialog signal; >21 min or host
  error = STOP + checkpoint. A BRIDGE-HARVEST worker runs concurrently on wt_d — flock
  serializes; dismissal ownership: only dialogs from opens MY session initiated (flock
  state + d008/runlog correlation before any dismissal).

## THE PICK — fix-regression carriers (verify-first from the manifests)

- **Align-3.dwg** — Align-2's census twin, ELIGIBLE, families {COGO 16, PARCEL_SEGMENT 1,
  Circle 6, MText 6, Alignment 1, GeomPoint/MinorStation/Station 1+1+1, Face 2, Tin 1} —
  EXACT match to Align-2's eligibility census. The E-1 fix's cleanest fresh carrier
  (parcel + boundary-segment coexist; packet E measured the PRE-fix writer here: 2≠1).
- **Align-4.dwg** — the other twin, same EXACT census. Also carries the legacy BestFitArc
  record (the #683 decoder's fresh L1 leg). Second E-1 regression carrier.
- **Align-7B.dwg — SUBSTITUTED for the dispatch's Align-7A, reason recorded**: Align-7A's
  eligibility manifest has NO alignment and NO labeling trio at all (families {Circle 5,
  MText 5, Tin 1} only, reasons: [] — it is not the circle/mtext+alignment shape the
  dispatch describes). The dispatch's own substitution rule names the nearest twins that
  HAVE the trio: Align-7B/7C. **Align-7B** picked (first-listed twin): {Circle 5, MText 5,
  Alignment 1, GeomPoint 1, MinorStation 1, Station 1, Tin 1} — the E-3 fix's fresh
  carrier (MinorStation group + sibling station group; the fix adds the trailing sibling
  reference the app walks per label). No parcels in 7B — not required for the E-3 gate.
  Align-7C recorded as the spare (identical census).

## Checkpoints

- [start] 2026-11-28 02:1x UTC: fetched origin+upstream; branch + both merges (above);
  oracle copies md5-verified; disk 57 GB free; watcher/dismiss.ps1 staged to
  C:\Temp\packetF\.

- [MERGE-BUILD] 02:2x UTC: example build green in 4m29s post-merge — both fixes compile
  integrated.

- [E-1 WIRING DISCOVERY + EXAMPLE COMMIT] 02:3x UTC: Align-3's FIRST build (pre-wiring)
  still showed parcel_segment 2≠1 — the E-1 fix branch (56b499ac) changed ONLY src/; the
  composed build path in examples/corpus_roundtrip.rs still called add_parcel. Committed
  **eb6326e1**: the composed parcel build now writes the parcel_segment records FIRST and
  calls `add_parcel_without_segment` when the manifest carries the parcel_segment family
  (solo shape — no parcel_segment family — keeps add_parcel). Precedent: baaad227 wired
  the D-1 fix through the example the same way. Clippy: my edit introduces ZERO new
  lints; clippy on the lib has 2 PRE-EXISTING deny-level lints (approximate FRAC_PI_2
  at src/classes/civil/create/profile_view.rs:623 and src/io/dwg/dwg_stream_writers/
  object_writer/mod.rs:1795 — deliberate schema-word style values, files untouched by
  this packet), recorded, not mine.

- [L1 Align-3] 02:3x UTC — POST-FIX:
  - analyze: 10 families; census gate == eligibility census EXACT (COGO 16,
    PARCEL_SEGMENT 1, Circle 6, MText 6, Alignment 1, label trio 3, parcel 1 + site 1
    = Face 2, Tin 1); gaps 1 (tin #11 only).
  - build: ZERO NOTEs (124338 bytes; the wired composed path).
  - verify/ownership guard: leaked_members=0 leaked_into_layout=0, inserts 0/0.
  - compare_verify: **circle 6/6 + mtext 6/6 + block_record 37/37 + cogo_point 16/16 +
    site 1/1 + parcel_segment 1/1 BIT-EXACT + alignment_label_group 3/3 BIT-EXACT**;
    **GATE (a) HEADLINE: parcel_segment 1==1 — the E-1 double-write is GONE codec-side**
    (pre-fix packet E measured 2≠1 on the twin Align-2); census AECC_PARCEL_SEGMENT 1==1.
  - pre-existing (Align-2's recorded notes, unchanged): tin #11 (782→786, 1388→1482);
    parcel name/label RAW (Parent_Tract→'' + label placement); alignment curve-fit
    (curves 4≠6, vertices 6≠8).

- [L1 Align-4] 02:4x UTC — POST-FIX:
  - analyze: 10 families; census gate EXACT (Align-3's twin, same counts); gaps 1
    (tin #11 only).
  - BestFitArc leg (#683): probe3b decodes the legacy BestFitArc element LIVE —
    FixedLine×3 + FreeArc(199.99999999999943) + FreeSCS(in=50,r=200,out=50) +
    **BestFitArc{radius 334.3905128049457, 16 BestFitPoints with offsets/projections}** +
    FloatingSpiralSpiralCurve — the decoder's fresh L1 leg is REAL on this file.
  - build: ZERO NOTEs (124497 bytes).
  - verify/ownership guard: 0/0, inserts 0/0.
  - compare_verify: **circle 6/6 + mtext 6/6 + block_record 37/37 + cogo_point 16/16 +
    site 1/1 + parcel_segment 1/1 BIT-EXACT + alignment_label_group 3/3 BIT-EXACT**;
    **GATE (a) holds on the second twin**; pre-existing: tin #11 (same numbers as
    Align-3), parcel name/label, alignment curve-fit (curves 4≠6 — the rebuild path
    curve-fits the BestFitArc+Spiral elements; the DECODE leg is clean — the recorded
    curve-fit gap, now confirmed on the BestFitArc shape).

- [L1 Align-7B] 02:4x UTC — POST-FIX (the E-3 carrier):
  - analyze: 6 families + block_record; census gate == eligibility EXACT (Circle 5,
    MText 5, Alignment 1, label trio Station/MinorStation/GeomPoint 1+1+1, Tin 1);
    gaps 1 (tin #11 only). NOTE: the trio's alignments string carries the standards
    XML path (C:\ProgramData\...\_Autodesk Civil 3D Metric Roadway Design Standards.xml)
    — decoded as stored.
  - build: ZERO NOTEs (786637 bytes).
  - verify/ownership guard: 0/0, inserts 0/0.
  - compare_verify: **circle 5/5 + mtext 5/5 + block_record 45/45 + alignment_label_group
    3/3 BIT-EXACT (MinorStation group present and bit-exact codec-side)**; census carries
    AeccDbAlignmentMinorStationLabeling 1; tin #11 (10158→10162, 16868→20287 — EXACTLY
    packet E's Profile-4B numbers) + alignment curve-fit (curves[1] None≠arc — the
    recorded gap) pre-existing.
  - ALL THREE L1 DONE — every build zero-NOTE, every guard 0/0. NEXT: L2/L3 bridge legs
    ×3 (attrib -r protocol, driver BARE — it takes the flock itself, watcher loop).

- [BRIDGE LEGS L2/L3] 2026-11-28 01:32–01:33 UTC — attrib -r verified on ALL THREE built
  files BEFORE any open (all 'A', no R, cp850 output); driver run BARE (takes the flock
  itself — no CLI-flock wrapper, the packetE self-deadlock lesson); watcher loop live
  (pktF_watcher.log start 01:32:07). The wt_d harvest worker's legs serialized cleanly
  behind the flock (no contention observed — each of my legs ran 9 calls in ~11 s).

  - LEG 1 [L2/L3 Align-3] 01:32:16–01:32:28 UTC:
    - oracle open readOnly:true NO dialog; units oracle 'Feet'.
    - oracle census: AUDIT 36/0/0 {Circle 6, MText 6, Alignment 1, GeomPoint 1,
      MinorStation 1, Station 1, CogoPoint 16, Face 2, LotLine 1, Tin 1}; TIN [EG]
      778/1388; COGO0 num=1.
    - built census: **AUDIT 36/0/0 — ZERO exceptions both sides**; TIN [EG] BOTH sides
      782/1482 (#11); COGO0 num=16 first (C-5 order, count-exact); built units
      'Undefined' (D-2 repeats, 4th packet).
    - **L3 = FULL EQUALITY — ALL 11 CLASSES ==, HEADLINE GATE (a): LotLine 1==1** (the
      E-1 fix holds at the app census: packet E measured LotLine 2 vs 1 on the twin
      Align-2 PRE-fix — the double-write is GONE, zero double-writes) **AND GATE (b):
      MinorStation 1==1 MANAGED app-side, not erased** (the E-3 fix's sibling-reference
      tail is what the app walks).
  - LEG 2 [L2/L3 Align-4] 01:32:36–01:32:47 UTC:
    - oracle open NO dialog, units 'Feet'.
    - oracle AUDIT 36/0/0 (same 11-class census as Align-3 — twins at the app too);
      TIN [EG] 778/1388.
    - built **AUDIT 36/0/0, ZERO exceptions**; TIN [EG] BOTH sides 782/1482 (#11); COGO0
      num=16 first; units 'Undefined' (D-2).
    - **L3 = FULL EQUALITY — ALL 11 CLASSES ==; gates (a) LotLine 1==1 and (b)
      MinorStation 1==1 hold on the second twin.**
  - LEG 3 [L2/L3 Align-7B] 01:32:52–01:33:04 UTC — the E-3 carrier's headline leg:
    - oracle open NO dialog, units 'Meters'.
    - oracle census: AUDIT 15/0/0 {Circle 5, MText 5, Alignment 1, GeomPoint 1,
      MinorStation 1, Station 1, Tin 1}; TIN [Existing Ground] 8572/16868.
    - built census: **AUDIT 15/0/0 — ZERO exceptions** (packet E's Profile-4B built had
      null=1 ePermanentlyErased here — NONE on this fix lineage); TIN [Existing Ground]
      BOTH sides 10158/20287 (#11, exactly Profile-4B's numbers); units 'Undefined' (D-2).
    - **L3 = FULL EQUALITY — ALL 7 CLASSES ==, GATE (b) HEADLINE: MinorStationLabeling
      1==1 app-side — the E-3 fix HOLDS on its fresh carrier: the group is MANAGED, not
      erased** (the sibling station-group reference the fix adds is the tail the app
      walks; the packet-E erase does not reproduce).
  - ctx invariants: Drawing1 ALL-0 on all 9 probes (before == mid == after, all legs);
    6 closes discardChanges:true — ALL returned discardedChanges:false (nothing was ever
    flagged modified); watcher matched NOTHING (zero DISMISSED / NONMATCHING-DIALOG
    lines); no wedge, no dialog signal, ZERO writes; 27 calls ALL done/ok=True (d008:
    /tmp/opencode/writere2/d008_log_packetF.jsonl).
  - GATE (c) — no regressions in any other family: every non-LotLine/MinorStation class
    app-exact on all three files; the recorded caveat (the PARITY-BUILD erase — a
    MinorStation erased app-side on a parity-branch build, upstream clean) did NOT
    reproduce: this lineage carries C-3/D-1 + BOTH fixes and shows ZERO app-side
    erasures on all three files. The open item stays open but unobserved here.

## STATE SNAPSHOT (2026-11-28 ~01:5x UTC — post-suite, pre-ship)

- Branch parity/packetF: merges 0424b3c1 (E-1) + 5dfa3a33 (E-3) + wiring eb6326e1;
  suite 3452/0; disk 56 GB free (>15 floor); watcher running (zero matches); all legs
  green; no blocker of any kind.

- [SHIP] committed **6ad4f26e** on parity/packetF (align_3/align_4/align_7b manifests +
  gap_closure_packetF.json + the runlog copy; data-only, on top of eb6326e1) and pushed
  schoeller/cadcodec:parity/packetF — **origin ref == HEAD verified (6ad4f26e)**. NO PRs,
  no matrix/PM edits. THIS completed runlog copy (SHIP section + handoff notes) pushed as
  the follow-up data-only commit (the packetE 1ef1bfda precedent). Artifacts: d008 log /tmp/opencode/writere2/d008_log_packetF.jsonl;
  watcher log /tmp/opencode/ct/pktF_watcher.log (start 01:32:07, matched NOTHING);
  built files + analyses /tmp/opencode/packetF_work/ and C:\Temp\corpus_built\packetF\
  (attrib -r carried); oracle copies 444 in /tmp/opencode/packetF_work/.
- [SUCCESSOR HANDOFF NOTES] (1) The E-1 fix (56b499ac) ships ONLY src/ — any composed
  corpus build needs the example wiring (eb6326e1, in this branch) or it re-measures the
  PRE-fix writer; already merged here, nothing to do. (2) The recorded PARITY-BUILD
  erase caveat (packet E's E-3 profile-view occurrence) did NOT reproduce on this
  lineage — if a successor sees an anomalous app-side erasure, record it precisely; the
  item stays open. (3) packetF_verify.py takes /tmp/opencode/bridge.lock itself — run
  BARE (packetE's self-deadlock lesson stands). (4) The user's leftover open drawing
  (C:\Temp\mhvadopt\mhv-pad.dwg) was visible in openDrawings on every open — untouched,
  Drawing1 invariants held on every probe.


## Verdicts (summary)

| file | L1 (codec compare) | L2 (audit) | L3 (app census equality) | verdict |
|---|---|---|---|---|
| Align-3 | PASS zero-NOTE (circle 6 + mtext 6 + block_record 37 + cogo 16 + site 1 + **parcel_segment 1/1 BIT-EXACT — E-1 GONE codec-side** + label groups 3/3 BIT-EXACT; guard 0/0; tin #11 + parcel name/label + curve-fit pre-existing) | audit 36/0/0, zero exceptions | **FULL EQUALITY — 11/11 classes ==** (LotLine 1==1, MinorStation 1==1) | **PASS at L3** |
| Align-4 | PASS zero-NOTE (same families 1/1 BIT-EXACT incl. parcel_segment 1/1 + label groups 3/3; guard 0/0; BestFitArc decodes live — radius 334.39 + 16 pts; tin #11 + parcel name/label + curve-fit pre-existing) | audit 36/0/0, zero exceptions | **FULL EQUALITY — 11/11 classes ==** (LotLine 1==1, MinorStation 1==1) | **PASS at L3** |
| Align-7B | PASS zero-NOTE (circle 5 + mtext 5 + block_record 45 + label groups 3/3 BIT-EXACT incl. the MinorStation record; guard 0/0; tin #11 + curve-fit pre-existing) | audit 15/0/0, zero exceptions | **FULL EQUALITY — 7/7 classes == (MinorStation 1==1 MANAGED — the E-3 fix holds)** | **PASS at L3** |

**Headline for the findings report:** BOTH fixes VERIFIED on fresh files, at FULL L3 census
equality — the packet's standard — on all three carriers: (a) the E-1 parcel/boundary
double-write is GONE (parcel_segment 1/1 codec BIT-EXACT + LotLine 1==1 app-side on both
twins; required the composed-build example wiring, commit eb6326e1 — the fix branch shipped
only src/), and (b) the E-3 MinorStation erase does not reproduce — the group is MANAGED
app-side on all three files (the fix's sibling-reference tail). ZERO anomalies of any kind:
no parity-build erase (the recorded open item did not reproduce on this lineage), no leaks
(guard 0/0 ×3), zero dialogs, zero writes, ctx invariants throughout. The only remaining
deltas are the recorded pre-existing notes (tin #11 on all three; parcel name/label on the
twins; alignment curve-fit incl. the BestFitArc rebuild on Align-4; C-5 cogo order; D-2
units header).


