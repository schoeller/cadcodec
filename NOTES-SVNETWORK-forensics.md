# WIP forensics — survey-figure traverse / AECC_SVNETWORK (Worker-ACAD-SVNET, 2026-11-21)

TEMPORARY storepoint notes, NOT for merge. Branch `parity/sv-traverse`, base 3b45720d.
Test file: `C:\Program Files\Autodesk\AutoCAD 2027\C3D\Help\Civil Tutorials\Drawings\Survey-2B.dwg` (READ-ONLY opens).
Oracle: `artifacts/2026-11-20T23-59_workerORACLE/TASK1_VERDICT.md` (LOT1 5 PIs verbatim + length semantics).
Harness: `/tmp/opencode/harness_svnet` ([patch] → this worktree; forensic dumps in
`survey2b_forensic.json`, `survey2b_full.json`, `svnetwork_0x1a8b.bin`).

## VERDICT (D007): join FAILED — the traverse PI x/y are NOT in the AECC_SVNETWORK record

- AECC_SVNETWORK = handle 0x1a8b, 36,024 B record, 1,084 strings (540 nonempty = figure-prefix
  names + point descriptions, 136 unique; NO coordinates as text), 2 typed handles.
- Exhaustive all-bit-offset f64 scans (all 8 shifts = every bit position of the 36 KB record)
  against ALL 15 LOT1 traverse values (v0..v4 × x,y,z):
  - x/y: NOT PRESENT within ±1.0 absolute anywhere in the record (nor exact, nor f32 at any
    bit offset, nor pairwise-PI deltas, nor chord distances, nor bearings, nor fixed-point
    u64 at 1e3/1e4/1e6/1e7/2^32 scales, nor translation by candidate origins
    0/4096/5000/5120/5376/5490).
  - z: EXACTLY ONE hit — v0.z = 257.38900127007406 at bit 145505 (BD with 00 prefix at 145503,
    i.e. bit-coded, non-byte-aligned). v1..v4 z absent.
- Therefore the PIs are not stored numbers in the network record. Region map of the record:
  - bits ~192..5440: byte-aligned RD settings/label block (small value set, ±0.1 pairs),
  - bits ~6535..182325: the survey tables (bit-coded; ~500 coordinate-like doubles at
    62–376-bit spacing; recurring z→x gap = 174 bits; semantics undecoded; NOT the figure PIs),
  - bits ~198832+ / 235762+: 256-quantized preview/extents grid (5120.0625, 4376.0625, ...).
- Dead ends ruled out: f32 (any shift), deltas among PIs, chord distances, bearings,
  fixed-point integers, translated copies, mirrored/swapped axes, strings-as-coordinates.

## AECC_SVFIGURE record (0x1a92 LOT1, 1003 B) — NEW structure beyond PR #560

- [0..184): prefix (sizes, RX class name 'AeccDbSvFigure (AeccSurvey130)', constants).
- bytes 24/32: label point = (bbox xmin+0.1, bbox ymin+0.1) as RDs (same +0.1 idiom as parcels).
- bytes 184..688: byte-aligned run chain [u32 len][u32 kind=6][u32 count] + count×3 RD
  = 2 bbox rings (132 B, 5 verts, z = Min/MaxElevation EXACT) + 4 corner connectors
  (60 B, 2 verts) — documented in #560.
- bytes ~688..777: per-figure differing section (LOT1 holds f32-like 230.175/42.554/170.454 —
  unconfirmed; LOT7 holds ascending 16-bit values 232/194/64/166/208/222/228/488; constant
  20-byte tail + per-figure counter byte 0x48/0x58/0x68/0x78 for LOT1/3/5/7).
- bytes 777 + 33k: VERTEX-SLOT section — [RD] doubles at 33-byte stride, byte-aligned,
  cycling y,z,x,y,z,x per stored vertex; stops at garbage. Counts: LOT1 5, LOT2 5, LOT3 3,
  LOT4 3, LOT5 5, LOT6 5, LOT7 5, LOT8 5, BLDG9 6, EP1 11, SHD1 11, SDWK1 11, EP2 8, TC1 9,
  EP3 12, EP4 12, SHD2 12, SDWK2 12, EP5 5, SHD3 2, SDWK3 2, BLDG8 7, EP6 5, SHD4 2, BLDG1 6.
- Each 33-B slot = [1 B][8 B RD][24 B bit-coded payload]. Payloads contain NO coordinates at
  any bit offset (scanned). Probably point references/flags/arc encoding — GRAMMAR UNDECODED.
- Slot x/y are REDUCED PRECISION vs API (~1e-10, e.g. LOT1 y0 stored 224 ulps low; x3 9 ulps;
  y4 216 ulps) while z slots are EXACT — a graphics-side cache fingerprint.
- CRITICAL unresolved fact: for LOT1 the 5 slots = (v0.y, v1.z, v3.x, v4.y, v0.z) — under
  (y,z,x)-per-vertex grouping the assembled vertices are NOT API PIs (they mix axes across
  PIs); as one-coordinate-per-PI the assignment rule is unknown (v2 gets zero slots despite
  being a full bbox corner). For EP/SHD/SDWK/TC figures the slots DO assemble into plausible
  grid-corner vertices (e.g. EP1: (5125.000,5078.001,263.129), (5324.997,5078.000,260.599),
  (5490.000,5077.999,258.079), (?,5092.645,255.020); BLDG9: two corners 75.0000 apart in y).
- Only a SUBSET of PIs is stored per figure (BLDG9: 2 triples vs 8 PIs; LOT3: 1 triple vs 4).
  LOT3 length check: bbox perimeter 500.0146 ≠ API Length2D 500.00582 → traverse ≠ bbox ring.
  BLDG9: bbox 75.0033×100.0022 perimeter 350.0111 ≠ API 350.00272 (true sides ≈ 75.000 +
  100.0014) → traverse is INSET from the stored bbox; bbox is display-inflated here.
- Tail after slots: bit-coded strings ('AeccImpSvFigure', '', '', name, site) + handles.

## Current hypothesis + next step

The unstored PI coordinates are computed by C3D's survey engine from OBSERVATIONS in the
SVNETWORK record (angles/distances), or referenced through the undecoded 24-B slot payloads.
Next step: decode the 24-B payload bit grammar across all 85 figure records (differential
analysis: straight vs arc figures, 1st vs later vertices); if payloads name survey points whose
coordinates are also absent from the SVNETWORK, close the item as "traverse is engine-computed,
not stored" — final D007 negative. NO PR was shipped (no decode verifies against the oracle).
Suite on this tree: 1938 passed / 0 failed (lib) + all doctests green.
NOTE (orchestrator, 2026-11-21): upstream moved to 534ff8ab (#585–#592); at any future ship,
rebase there and use the ProxyGraphics idiom for type-6 run chains instead of hand-walking.
