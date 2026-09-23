# Zero-context prompt — ACS/SH solid-history Phase A (step 4: LOFT/REVOLVE)

> Campaign state 2026-09-23 ~18:20Z. The strict-load campaign is closed
> at zero (2026-09-21, user-verified round seven; see IMPLEMENTATION.md
> §18.4). The F2 fixture tree landed (2026-09-23: 28 .dwg + 28 .txt in
> `tests/gold_harness/tests/sh_history/`, committed `fc9f235`).
> Phase A steps 1–3 are DONE (HISTORY, SWEEP, EXTRUSION un-elided —
> SWEEP/EXTRUSION under raw-tail retention). This brief covers step 4:
> the ACSH_LOFT_CLASS / ACSH_REVOLVE_CLASS autopsy, raw-tail extension,
> and un-elide. Read `tests/gold_harness/AGENTS.md` first (durable
> rules), then §F2.1–F2.3 and §18.5 in `IMPLEMENTATION.md` (fixture
> gates + the step-2 autopsy record), then this file top to bottom.

## Task

**Phase A step 4**: bring the remaining sweep-family pair under
control — `ACSH_LOFT_CLASS` and `ACSH_REVOLVE_CLASS`. Their
`read_solid_history_data` arms still model guessed layouts
(LOFT: cross-section/guide counts + embedded entities; REVOLVE:
axis_point 3BD + direction 3raw + revolve/start/draft/twist BDs +
flags + an embedded sweep entity). Both classes are `DEBUGGING_CLASS`
in gold — there is no oracle for their tails, exactly like the SWEEP
case — so the expected outcome of the autopsy is the same one the
step-2 record found: the guessed per-field walk does not match the
authored wires, and the fix is the same raw-tail capture.

### What already landed (do not redo)

- `b926053` (step 1): ACSH_HISTORY_CLASS un-elided (known 6-field
  layout).
- `ba7d112` + `c96355f` (step 2 + review): ACSH_SWEEP_CLASS un-elided
  under raw-tail retention. `SolidHistorySweep` carries
  `shsw_raw_tail` (MSB-packed) + `shsw_raw_tail_bit_len`; the reader
  captures the payload from just after `op.minor` to
  `min(main_end_bits(), record_end_bits())`; the writer re-emits the
  bits verbatim (clamped to `shsw_raw_tail.len() * 8`, fall-through to
  the modeled arm when the tail is empty — i.e. DXF reads). The
  modeled `shsw_*` fields are the DXF / fallback channel only.
- `d36e553`: §18.5 step-2 closure — the full autopsy method record.
- `8c41aa6` + `48ca14a` (step 3, DONE): ACSH_EXTRUSION_CLASS
  un-elided via the shared path — Extrude_2018 record present in the
  rewrite (Size 70→72, only the corpus-wide owner-handle form delta),
  data section bit-identical, corpus 26/8 unchanged.

### Step 4 method

1. **Autopsy first** (never trust a guessed layout — §8.1.4):
   - Regenerate the raw record bits for both calibration targets
     (`target/debug/dwg2json <fixture> out.json`, then take
     `unknown_bits_by_handle[<handle>]`):
     - Loft_2018: handle 746 (0x2EA), Size 102, Hdlsize 0x1B;
     - Revolve_2018: handle 745 (0x2E9), Size 67, Hdlsize 0x19.
   - Check the shared skeleton anchors (§18.5: parentid BLd(-1), eval
     33/427, value_code −9999, nodeid, hist 33/427, 16 BD transform,
     CMC 44 bits, step_id, op 33/427) and the per-class tail after
     `op.minor`. The `'10'-run BL(0)` + real-content pattern exposed
     the sweep guess; watch for the same signature (the LOFT arm's
     cross-section count BL and the REVOLVE axis BD forms are the
     prime suspects — a `'00' + raw32` count where the wire has short
     content would misalign exactly the way shsw did).
   - The Revolve R2007/2010 `3DSOLID.point` wrong-value packet
     (silver reads (0.6, 0, 0.6) where gold reads (0, 0, 0)) is a
     constructed-genus default: it may surface or resolve during this
     autopsy window — record either outcome in §18.5.
2. **If the guessed arms mis-model** (expected): extend the raw-tail
   retention to both classes — add tail fields to `SolidHistoryLoft`
   and `SolidHistoryRevolve` (src/objects/dynamic_block.rs), capture
   in their arms right after `op.minor` (same boundary expression as
   `read_history_sweep`), writer arms gated on the tail (modeled
   fallback preserved for DXF, like the sweep).
3. **Un-elide both** — the two guard sites:
   `src/io/dwg/dwg_stream_writers/object_writer/objects.rs` and
   `entities.rs::solid_history_handle_value` (one class at a time:
   LOFT first, gate it, then REVOLVE).
4. **Gates** (each class): hermetic tests; the single-fixture smoke
   (expect 0 new rows — each file's surviving rows are its
   `3DSOLID.wires` stub pair); full corpus (gold tree 0/0 must hold,
   26/8 expected unchanged); layer-4 compare against the original
   record (anchor on the parentid pattern).

## The wire knowledge base (condensed; §18.5 has the full record)

- SH skeleton, verified via gold's live sphere `-v9` trace: parentid
  `BLd(-1)` = `'00'+LE32(0xFFFFFFFF)`, eval major `BL('01'+RC)` 33 /
  minor `BL('00'+LE32)` 427, `value_code BSd` −9999 (`LE16 0xD8F1`),
  nodeid 1, hist 33/427, 16 BD transform, CMC (44 bits), step_id
  `BL('01'+RC)` 1, material → handle stream, then `op.major/minor`
  33/427. The class-specific tail after that is gold-undocumented for
  every node class (gold stops at `color.flag` and dumps the rest as
  `unknown_bits` even in DEBUG builds).
- Frames: R2018 = 40 bits, R2010 = 39 (MS/UMC/BOT lengths vary with
  Size/Hdlsize encoding; the data anchors a fixed offset after the
  frame — anchor on parentid, not on offsets). Data section ends at
  `Size×8 − frame − Hdlsize − 1` (the −1 is the 1-bit text-present
  flag; `bitsize` in gold's −v9 print = the handle-stream start in
  window bits).
- Wire primitives: raw-short/long/double are LITTLE-endian; BD
  prefixes `00`/`01`/`10` = raw64 / 1.0 / 0.0 (`11` reserved→0.0);
  BL `00`/`01`/`10`/`11` = LE32 / RC / 0 / 256.
- Payloads are version-portable: the same record is bit-identical
  across 2007/2010/2013/2018 except handle tails — a cheap structural
  cross-check for any autopsy.
- Raw-bit captures go through `reader.read_bit()` (clamps at the
  physical end — no panics) and MUST be length-clamped to
  `record_end_bits()` (hostile framing controls the declared splits;
  see commit `c96355f` for the review finding this closed).
- Gold's own `unknown_bits` dump and silver's side channel are
  bit-identical for the same record.

## The 26/8 fixture-diff packets (context; unchanged through step 3)

| packet | rows | files | route |
|---|---|---|---|
| `3DSOLID.wires` stub | 16 (8+8) | Extrude/Loft/Revolve/Sphere (R2013+R2018) | constructed-genus zero-index wire cache — likely needs node-blob semantics (Phase B) |
| `ACSH_SPHERE_CLASS` + `UNKNOWN_OBJ` counts | 8 | all 4 Sphere files | sphere node-class ordinal alignment — likely touched by the Sphere un-elide (after step 4) |
| `3DSOLID.point` wrong-value | 2 | Revolve_2007/2010 | constructed-genus default — inside the step-4 autopsy window |

## Environment (complete)

The repo lives in WSL. From Windows:
`\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`.
Shell commands run via
`wsl.exe -d Ubuntu-24.04 -- bash <script>` — write scripts with the
write tool and run by absolute path (PowerShell quoting caveats:
inline `&&`, `$var`, pipes, and multi-word grep alternations are all
broken; ONE COMMAND PER LINE; `sleep` is capped at 120 s).

```bash
# Environment (source this):
export PATH="$HOME/.cargo/bin:$PATH"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

## Verification gate for every step

```bash
# 1. Build gates (all segments green)
cargo test --features serde

# 2. Single-fixture smoke
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (blocking ~10 min, writes
#    target/gold_harness_corpus/report.md)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 bytewise check:
target/debug/dump_section_bytes <file> <A> <N>
# anchor on parentid BLd(-1); compare [data .. data end) bit-for-bit;
# handles compare by identity (the owner-handle form delta is
# pre-existing and corpus-wide — see §18.5 step 2).
```

## Commit inventory (this halt)

```
48ca14a  docs(harness): Phase A step-3 closure — §18.5 record + step-4 queue
8c41aa6  fix(dwg): un-elide ACSH_EXTRUSION_CLASS — Phase A step 3
c96355f  fix(dwg): clamp sweep raw-tail capture and emit bounds (review)
2416022  fix(docs): NEXT_SESSION commit inventory — include the 14:00Z user doc commits
c1200a0  docs(harness): Phase A step-3 handover — NEXT_SESSION replaced
d36e553  docs(harness): Phase A step-2 closure — SWEEP layout autopsy + queue update
ba7d112  fix(dwg): un-elide ACSH_SWEEP_CLASS — Phase A step 2, raw-tail retention
1652af2  docs(harness): document the full Phase A/B/C plan — every phase defined
96673ec  docs(harness): zero-context completeness — full Phase A handover in NEXT_SESSION + §18.5 step-2 findings
1f06d9d  chore: retire first-session scratch — the ocs.lock rules and the cylinder example
e686903  docs(harness): Phase A step-2 probe findings — the SWEEP write path loses 113 bytes
b926053  fix(dwg): un-elide ACSH_HISTORY_CLASS — Phase A step 1
fc9f235  test(harness): F2 in-repo fixture tree — sh_history campaign
459bc74  fix(dwg): elide SH modeler-history class records at save
33ce739  fix(dwg): constructed wireframe guard
```

The branch head is this handover commit (this file); the commits
above are its parents. `1f06d9d` was the last push to
`origin/gold-vs-silver` (push only when asked).
