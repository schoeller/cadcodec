# D017 PACKET E — corpus roundtrip (3 files × L1/L2/L3) — runlog

- Worker: D010 packet-E worker (per-file L1/L2/L3 + gap log + suite; NO PRs, data-only push)
- Binding: /tmp/opencode/worker_brief.md + dispatch (D017 PACKET E)
- Protocol model: packetD_runlog.md + packetC_runlog.md + c1_fix_runlog.md (the C-1 ownership
  guard 0/0 standard; the C-2/C-3/C-4 + D-1 fixes are the baseline: full L3 census equality
  is the standard).
- Branch: `parity/packetE` (worktree /tmp/opencode/wt_c + harness /tmp/opencode/harness_c),
  created from **origin/parity/packetD-fix @ baaad227** (carries parity/packetC-fix2's C-1..C-4
  fixes AND the D-1 profile-view bands-range fix), then merged upstream/main @ **d7c71f50**
  (the #717 stormwater-context merge + #719 BLOCKROTATEACTION + #721 visibility-reactor +
  #723 properties-table typed values). Merge commit ed2fcdb0: TWO content conflicts, both in
  re-export lists, both resolved as UNION — src/classes/civil/create/mod.rs (HEAD's
  `add_parcel_segment_record` in the site re-export kept; upstream's extended stormwater
  re-export kept) and src/classes/civil/mod.rs (HEAD's list incl. `add_parcel_segment_record`
  + upstream's stormwater items appended). Built clean after (below).
- Env: RUSTC_WRAPPER=sccache, CARGO_PROFILE_TEST_DEBUG=0, CARGO_INCREMENTAL=0. Disk at start
  48 GB free. Harness precedent: `cargo run --example corpus_roundtrip --features serde,import
  --release` inside the worktree (harness src/main.rs not used).
- Corpus: Civil Tutorials Drawings (D013 rule;
  `C:\Program Files\Autodesk\AutoCAD 2027\C3D\Help\Civil Tutorials\Drawings`); the 3 files
  copied read-only (chmod 444) to /tmp/opencode/packetE_work/.
- Bridge: port 7900 ONLY; flock /tmp/opencode/bridge.lock; attrib -r + verify before EVERY
  built-file open; oracle opens readOnly:true; get_civil_context before/after invariants;
  close discardChanges:true; AUTONOMOUS RULE active (known proxy/version modal =
  Win32-dismiss by title/text ONLY, and only when MY session initiated the open; ANY other
  modal or 120 s wedge = STOP that leg). Driver: /tmp/opencode/ct/packetE_verify.py (the
  packetD_verify.py pattern); watcher /tmp/opencode/writere2/mhv/win32/dismiss.ps1.

## THE PICK — the wiring round's 27 eligible files MINUS packet C's three (Parcel-1A,
Align-6C, Points-3) and packet D's three (Labels-2a, Profile-4A, Surface-4A). Coverage ledger
entering this packet: cogo tested ONLY at 2405 (×4 packets), parcel-segment builder proven on
exactly ONE record (the C-4 fix's Align-6C lot line), Face never above 1 at packet level
(57 only in DEFERRED files), lwpolyline at volume once (Parcel-1A 141), the D-1 fix (my merge
base carries baaad227) has ZERO packet-level L3 evidence (Profile-4A's L3 failed exactly there
BEFORE the fix), and the assembly/boundary writer (W1-4/a) has no packet L3 leg at all.

1. **Align-2.dwg** — census {AECC_COGO_POINT:16, AECC_PARCEL_SEGMENT:1, AcDbCircle:6,
   AcDbMText:6, Alignment 1, GeomPoint/MinorStation/Station labeling 1+1+1, AeccDbFace:2,
   Tin:1} + block records. THREE never-packet-tested shapes in one file: (a) cogo at SMALL
   count (16 — every packet to date hit the 2405 mass; the small-store build/verify shape is
   untested); (b) the C-4 parcel-segment builder's first PACKET leg (post-parcel-round viable
   per dispatch — the builder landed in 32e0866b and was proven on exactly 1 record codec-side,
   never through a full packet L1+L3); (c) Face 2 alongside a full alignment-labeling trio +
   circle/mtext 6. Align-3/4 are census twins — one of them is the coverage carrier.
2. **Assembly-1a.dwg** — census {AECC_PARCEL_SEGMENT:102, AcDb3dPolyline:3, AcDbArc:1,
   AcDbLine:1, AcDbPolyline:136, Alignment 2, Minor 2, Station 2, AeccDbFace:57,
   GraphProfile:2, ProfileDataBandLabeling:2, Tin:1, VAlignment:4} + block records. The
   broadest remaining census of the eligible set (12 families): the C-4 builder AT VOLUME
   (102 segments vs the 1 proven), Face 57 at its corpus volume (packets saw 1 only),
   lwpolyline 136 at volume, and the assembly-round families (GraphProfile + bands +
   VAlignment 4) in the assembly shape — never packet-tested. The dispatch's dominant-
   shortfall warning (the wiring round's parcel 56→18 note) is JUDGED FROM FRESH DATA: that
   note predates the C-4 parcel-segment builder; the packet records what the post-C-4 writer
   actually does at 102.
3. **Profile-4B.dwg** — census {AcDbCircle:9, AcDbMText:10, Alignment 1, GeomPoint/
   MinorStation/Station labeling 1+1+1, GraphProfile:1, ProfileDataBandLabeling:1,
   VAlignment:2, Tin:1} + 39 block records. The FIRST L3 packet test of the D-1 FIX: my base
   baaad227 fixed the profile-view bands path to ride the manifest's decoded oracle range —
   exactly the defect that failed Profile-4A's L3 (GraphProfile −1, ProfileDataBand −1) in
   packet D. Profile-4B is that file's twin shape (same banded view) with TWO VAlignments
   (1 more than any packet-tested file) — it verifies the fix live at the app census, which
   no codec-side check covers.

Not picked (from the remaining 18): Align-3/4 (census twins of Align-2 — the pick carries the
shape), Align-6B/6D (twins of the packet-C-tested Align-6C — zero new families), Align-7B/7C
(circle/mtext+alignment, covered at 6/6 volume by the Align-2 pick + 7A night packet),
Labels-1a (1-insert minimal — superseded by Labels-2a's 43-record/3-insert proof),
Labels-Alignments (the East Street alignment still does not rebuild — the recorded curve-fit
build NOTE would dominate the verdict exactly as packet C/D judged; its other families are all
covered elsewhere), Profile-1 (lwpoly 136 is its only marginal family — covered by
Assembly-1a's 136 in this very packet), Surface-4B..5C/7 (identical census to packet D's
Surface-4A — redundant), Surface-8 (30k-point tin + super-linear mix — the wiring round's
honest STOP stands until the retriangulation cost is addressed).

## Checkpoints

- [start] 2026-11-27 ~22:1x UTC: fetched origin+upstream; branch + merge ed2fcdb0 (above);
  disk 48 GB free.
- [SUCCESSOR RESUME] 2026-11-27 23:37–23:5x UTC: previous packet-E worker died silently
  ~23:24Z right after writing Align-2's L1 artifacts (no checkpoint, no report). Resumed
  per the credit-outage successor precedent: HARVEST + re-verify, never redo blindly.
  - ENV VERIFIED: branch parity/packetE @ ed2fcdb0 correct + clean (`git status` empty);
    disk 47 GB free (>15 floor); harness_c intact; sccache/CARGO_PROFILE_TEST_DEBUG=0/
    CARGO_INCREMENTAL=0 on every cargo line.
  - CORPUS md5 VERIFIED: all 3 oracle copies in /tmp/opencode/packetE_work/ match the
    tutorials folder byte-for-byte (Align-2 6056dcfe…, Assembly-1a bdfffe6b…,
    Profile-4B 65cabb1f…). Example binary warm (cargo build no-op, 0.09 s).
  - **Align-2 L1 HARVEST-VERIFIED (re-ran, did not trust the dead worker):**
    - `analyze` re-run: manifest reproduces byte-exact (10 families, gaps 1 =
      tin_surface.triangulation #11 only). Census gate == the pick's eligibility census
      {COGO 16, PARCEL_SEGMENT 1, Circle 6, MText 6, Alignment 1, GeomPoint/MinorStation/
      Station 1+1+1, Face 2, Tin 1} EXACT — gate PASS.
    - `verify` re-run (fresh decode of align_2.built.dwg → *_recheck.json): analysis
      byte-identical to the dead worker's; ownership guard **leaked_members=0
      leaked_into_layout=0, model_space_inserts 0 == analysis_inserts 0** (C-1 guard 0/0).
    - `compare_verify`: **circle 6/6 + mtext 6/6 + block_record 37/37 + cogo_point 16/16 +
      site 1/1 + alignment 1/1 + alignment_label_group 3/3 BIT-EXACT**; tin #11
      (782→786 pts, 1388→1482 tris) pre-existing; parcel 3 RAW diffs (name "Parent_Tract"
      →"" + label placement — the pre-existing parcel-writer notes packet D recorded).
    - **[NEW GAP E-1] parcel_segment double write when a parcel AND its boundary
      parcel_segment share a file**: built AECC_PARCEL_SEGMENT **2 ≠ 1** — the built
      carries (a) the parcel build's own lot-line record (`add_parcel` → `add_lot_line_on`
      → `join_site`'s record closure `write_lot_line(..., None)`, re-analyzes as
      geometry:null) AND (b) the C-4 builder's decoded record (geometry == the oracle's).
      In the oracle the single segment IS the parcel boundary (corners == parcel vertices).
      Code-pinned (site.rs:1790/1446/1309 + example 1926-1961). First live leg of the C-4
      builder at packet level where both families coexist (Align-6C had no parcel family).
      WRITER/example class, implementable; NOT fixed this round (data-only).
  - NEXT: Assembly-1a L1 (the heavy one), then Profile-4B L1, then L2/L3 ×3, suite, ship.
- [L1 Assembly-1a] 2026-11-28 ~00:0x UTC:
  - analyze: 13 families; census gate == the pick's eligibility census EXACT (13/13:
    PARCEL_SEGMENT 102, 3dPolyline 3, Arc 1, Line 1, LwPolyline 136, Alignment 2,
    Minor 2, Station 2, Face 57, GraphProfile 2, ProfileDataBand 2, Tin 1, VAlignment 4);
    gaps 1 (tin #11 only).
  - build: **1.77 s wall** (minutes expected — the post-C-4 writer is far cheaper), **38
    NOTEs, all identical**: `parcel : Parse error: the line crosses or touches a member it
    may not meet`. Bytes 2240299.
  - verify/ownership guard: leaked_members=0 leaked_into_layout=0, inserts 0/0.
  - compare_verify: **arc 1/1 + polyline3d 3/3 + lwpolyline 136/136 + line 1/1 +
    block_record 40/40 + site 1/1 + profile 4/4 + profile_view 2/2 (BOTH banded views
    BIT-EXACT — the D-1 fix rides codec-side at L1 here) + alignment_label_group 4/4
    BIT-EXACT**; tin #11 (23126→23130, 45934→46233) and alignment 6 RAW (2 last-ulp
    vertex pairs + curves[1..2] None≠arc — the recorded curve-fit gap) pre-existing.
  - **parcel 18 ≠ 56 — the wiring round's dominant shortfall CONFIRMED FROM FRESH DATA**:
    the 38 meet-rejections are exactly the 56−18 unbuilt; the post-C-4 writer still
    cannot build parcels whose lot lines touch fellow members (add_parcel rides
    add_lot_line_on meet=false; site.rs:1423/1505). NEW TO THE CORPUS RECORD as fresh
    packet evidence (pre-existing note, never packet-verified) — recorded as E-2.
  - **parcel_segment 120 ≠ 102 — E-1's mechanism AT VOLUME**: 102 decoded records + one
    extra lot-line record per BUILT parcel (18) = 120; built Face 19 = 1 site + 18
    parcels vs oracle 57 = 1 + 56. Consistent with Align-2's +1.
- [L1 Profile-4B] 2026-11-28 ~00:1x UTC — the FIRST live packet test of the D-1 fix:
  - analyze: 8 families; census gate EXACT (10/10); gaps 1 (tin #11 only). PV0 carries
    the oracle range stations [-20, 1120] / elevations [50, 74] + bands ["ProfileData"].
  - build: **zero NOTEs, 0.29 s — PV0 BUILT WITH BANDS** (pre-fix, Profile-4A failed
    exactly here with `the profiles have no elevations within the stations`).
  - verify/ownership guard: 0/0, inserts 0/0.
  - compare_verify: **circle 9/9 + mtext 10/10 + block_record 39/39 + profile 2/2 +
    profile_view 1/1 + alignment_label_group 3/3 BIT-EXACT**; built census carries
    GraphProfile 1 + ProfileDataBandLabeling 1 (the D-1 objects present); tin #11
    (10158→10162, 16868→20287 — EXACTLY packet D's Profile-4A numbers) and alignment
    curve-fit (curves 4≠6, vertices 6≠8) pre-existing.
  - ALL THREE L1 DONE. NEXT: L2/L3 bridge legs ×3 (attrib -r protocol, flock, watcher).
- [BRIDGE NOTE] 2026-11-28 00:0x–00:2x UTC: two false-start legs (900 s + 1500 s timeouts,
  ZERO side effects — no d008 entries, no opens, no dialogs) were a SELF-DEADLOCK in MY
  invocation, not a host wedge: I wrapped the driver in the CLI `flock /tmp/opencode/bridge.lock`
  while the driver takes the same flock itself (packetE_verify.py main) — it blocked forever
  on its own lock. The dead worker's protocol (run the driver bare) is correct; recorded so
  no successor repeats it. Bridge probe during diagnosis: session up 0.11 s, ctx Drawing1
  all-0 — host healthy throughout; watcher silent.
- [L2/L3 Align-2] leg 1, 00:19:58–00:20:10 UTC:
  - attrib -r verified ('A', no R) before the built open; flock held (driver-internal);
    oracle open readOnly:true NO dialog; units oracle 'Feet'.
  - oracle census: AUDIT 36/0/0 {Circle 6, MText 6, Alignment 1, GeomPoint 1, MinorStation 1,
    Station 1, CogoPoint 16, Face 2, **LotLine 1**, Tin 1}; TIN name=[EG] 778/1388;
    COGO0 num=1 readable (E=4934.870765300845 N=3478.5644648740818 Z=703.3246514941502).
  - built census: **AUDIT 37/0/0** {same 9 classes ALL EXACT, **LotLine 2**};
    TIN [EG] BOTH sides (N-1 closure live), 782/1482 (#11); COGO0 num=16 first (C-5
    order, count-exact).
  - **L3 INEQUALITY — the delta is EXACTLY gap E-1**: LotLine +1 (the parcel build's own
    geometry-null lot-line record alongside the decoded boundary segment); every other
    class app-exact; audit delta 37−36 = that 1 record; ZERO leaks, guard 0/0.
  - ctx Drawing1 all-0 before == mid == after; closes discardChanges:true, both returned
    discardedChanges:false (nothing flagged modified); watcher silent.
  - Built units 'Undefined' vs oracle 'Feet' — the D-2 observation repeats (3rd packet).
- [L2/L3 Assembly-1a] leg 2, 00:20:21–00:20:33 UTC:
  - attrib -r verified; oracle open readOnly:true NO dialog; units oracle 'Meters'.
  - oracle census: AUDIT 315/0/0, 13 classes {3dPolyline 3, Arc 1, Line 1, LwPolyline 136,
    Alignment 2, MinorStation 2, Station 2, Face 57, GraphProfile 2, LotLine 102,
    ProfileDataBand 2, Tin 1, VAlignment 4}; TIN name=[EG] 23092/45934.
  - built census: **AUDIT 295/0/0**; **11 of 13 classes EXACT** — incl. LwPolyline 136 AT
    CORPUS VOLUME, VAlignment 4 == 4 (first packet leg at 4), GraphProfile 2 + 
    ProfileDataBand 2 == (the D-1 fix VERIFIED LIVE at the app census), Arc/Line/3dPolyline
    exact; TIN [EG] BOTH sides, 23126/46233 (#11, exactly the codec numbers).
  - **L3 INEQUALITY — the delta is EXACTLY E-2 + E-1**: Face **19 ≠ 57** (−38: the 38
    meet-rejected parcels of E-2) and LotLine **120 ≠ 102** (+18: E-1's one extra lot-line
    record per BUILT parcel; the rejected 38 contribute none). Audit 295 vs 315 = −38+18 =
    −20 — the two deltas close the audit exactly. ZERO leaks, guard 0/0, no erased.
  - ctx Drawing1 all-0 before == mid == after; closes discardChanges:true (both
    discardedChanges:false); watcher silent. Built units 'Undefined' (D-2 repeats).
- [L2/L3 Profile-4B] leg 3, 00:20:38–00:20:50 UTC — the round's headline leg:
  - attrib -r verified; oracle open readOnly:true NO dialog; units oracle 'Meters'.
  - oracle census: AUDIT 28/0/0 {Circle 9, MText 10, Alignment 1, GeomPoint 1,
    MinorStation 1, Station 1, GraphProfile 1, ProfileDataBand 1, Tin 1, VAlignment 2};
    TIN name=[Existing Ground] 8572/16868.
  - built census: AUDIT 28/0/**1** — `ID-EXCN id=311 class=AcRxObject msg=
    ePermanentlyErased` (REAL BUILT-FILE CONTENT, the packet-C C-2 lesson — not a client
    bug); **9 of 10 classes EXACT**; TIN [Existing Ground] BOTH sides, 10158/20287 (#11,
    exactly the codec numbers).
  - **HEADLINE — the D-1 FIX VERIFIED LIVE AT THE APP CENSUS: GraphProfile 1 == 1 AND
    ProfileDataBandLabeling 1 == 1.** Packet D's Profile-4A failed L3 on exactly these
    two (−1/−1); Profile-4B, the twin banded shape, shows FULL equality on them. Zero
    build NOTEs codec-side, zero app-side deltas there.
  - **[NEW GAP E-3] MinorStationLabeling 1→0 app-side**: the built's codec census carries
    AeccDbAlignmentMinorStationLabeling 1 (alignment_label_group 3/3 BIT-EXACT codec-side)
    but the APP census lacks the class entirely, and the audit's null=1 (id=311,
    ePermanentlyErased) is the physical evidence — the app cannot open the object where
    the MinorStation group should be. Same class as packet C's C-2 (station-group +
    erased-id; Parcel-1A's id=451), NEW occurrence on a fresh file shape (Profile-4A in
    packet D had NO such delta — MinorStation 1==1 clean there). WRITER, uncertain.
  - ctx Drawing1 all-0 before == mid == after; closes discardChanges:true
    (discardedChanges:false); watcher silent. Built units 'Undefined' (D-2 repeats).

- [bridge summary] 3 legs × (ctx_before + oracle open + read-only census + close +
  ctx_mid + built open + read-only census + close + ctx_after) = **27 calls, ALL
  done/ok=True** (d008-logged to /tmp/opencode/writere2/d008_log_packetE.jsonl); 6 opens
  (all NO dialog), 6 read-only census executes, 9 ctx probes (Drawing1 all-0 throughout),
  6 closes (all discardChanges:true, all returned discardedChanges:false — nothing was
  ever flagged modified); port 7900 only; every session under flock (driver-internal);
  attrib -r verified before every built open (all 'A', no R); **ZERO dialogs of any kind,
  watcher matched nothing (pktE_watcher.log: start 23:39:30, zero DISMISSED /
  NONMATCHING-DIALOG lines), no wedge, ZERO writes**. Two earlier zero-side-effect
  timeouts were my own CLI-flock self-deadlock (recorded above), not host events.

## Verdicts (summary)

| file | L1 (codec compare) | L2 (audit) | L3 (app census equality) | verdict |
|---|---|---|---|---|
| Align-2 | PASS-with-notes (7 fams BIT-EXACT incl. cogo SMALL-count 16/16 + block_record 37; tin #11 + parcel name/label pre-existing; E-1: parcel_segment 2≠1) | audit 37/0/0 | **FAIL by exactly the E-1 delta** (LotLine 2 vs 1; other 9 classes ==; TIN [EG] both sides) | FAIL at L3 — E-1 only |
| Assembly-1a | PASS-with-notes (9 fams BIT-EXACT incl. lwpoly 136 + VAlignment 4 + both banded views; E-2: parcel 18≠56; E-1 at volume: 120≠102) | audit 295/0/0 | **FAIL by exactly E-2 + E-1** (Face 19≠57, LotLine 120≠102; other 11 classes ==; audit −20 closes exactly) | FAIL at L3 — E-2/E-1 only |
| Profile-4B | PASS zero-NOTE (circle 9 + mtext 10 + block_record 39 + profile 2 + banded view 1 + label groups 3 BIT-EXACT; tin #11 + curve-fit pre-existing) | audit 28 total, null=1 (erased id=311) | **D-1 CLOSED LIVE: GraphProfile 1==1, ProfileDataBand 1==1**; 9/10 classes ==; E-3: MinorStation 1→0 app-side (erased id=311) | FAIL at L3 — E-3 only; **the packet's headline purpose achieved** |

**Headline for the findings report:** the D-1 profile-view bands fix — this branch's reason
to exist — is CLOSED with live packet evidence: Profile-4B (the exact twin shape that failed
in packet D) builds its banded view with zero NOTEs and shows full app-census equality on
GraphProfile/ProfileDataBand. The C-1 leak class stays EXTINCT (guard 0/0 + zero app-side
leaks on 3 more files). Three NEW/refreshed writer findings recorded, all code-pinned:
E-1 (parcel+boundary-segment double write, first seen where the families coexist),
E-2 (the 56→18 parcel meet-rejection shortfall, fresh-data-confirmed UNCHANGED post-C-4),
E-3 (a MinorStation group the app treats as permanently erased — the C-2 class is NOT fully
closed; new occurrence on a fresh shape).

- [suite] cargo test (sccache, CARGO_PROFILE_TEST_DEBUG=0, CARGO_INCREMENTAL=0) on
  parity/packetE post-legs (data-only changes): **3449 passed / 0 failed, exit 0**
  (incl. 14 doc-tests; full log: /tmp/opencode/packetE_work/suite_packetE_full.log) —
  packetD baseline 3437 + the merged upstream wave's tests, as expected for a data-only
  diff on this merge base.

- [SHIP] committed **8033c06b** on parity/packetE (align_2/assembly_1a/profile_4b
  manifests + gap_closure_packetE.json + the runlog copy as corpus/packetE_runlog.md;
  data-only, on top of ed2fcdb0) and pushed schoeller/cadcodec:parity/packetE —
  **origin ref == HEAD verified** (8033c06b). NO PRs, no matrix/PM edits. Disk after:
  36 GB free (>15 GB floor held). Artifacts: d008 log
  /tmp/opencode/writere2/d008_log_packetE.jsonl; watcher log /tmp/opencode/ct/
  pktE_watcher.log (start 23:39:30, end 00:24:58, matched NOTHING); built files +
  analyses /tmp/opencode/packetE_work/ and C:\Temp\corpus_built\packetE\.
- [SUCCESSOR HANDOFF NOTES] (1) run packetE_verify.py BARE — it takes
  /tmp/opencode/bridge.lock itself; a CLI flock wrapper self-deadlocks (two zero-side-effect
  timeouts recorded above). (2) The user's Acad instance carries another session's leftover
  open drawing (C:\Temp\mhvadopt\mhv-pad.dwg visible in openDrawings) — untouched, Drawing1
  invariants held on every probe. (3) E-3's erased id=311 in profile_4b.built.dwg is real
  file content; an app-side owner-chain probe of that id is the next diagnostic step.
