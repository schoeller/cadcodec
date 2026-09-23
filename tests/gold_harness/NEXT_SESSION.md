# Zero-context prompt — ACS/SH solid-history Phase A (step 3: EXTRUSION)

> Campaign state 2026-09-23 ~17:30Z. The strict-load campaign is closed
> at zero (2026-09-21, user-verified round seven; see IMPLEMENTATION.md
> §18.4). The F2 fixture tree landed (2026-09-23: 28 .dwg + 28 .txt in
> `tests/gold_harness/tests/sh_history/`, all qualified, committed as
> `fc9f235`). Phase A steps 1–2 are DONE (HISTORY + SWEEP un-elided;
> SWEEP carries raw-tail retention). This brief covers step 3 — the
> EXTRUSION un-elide — and the remaining Phase A packets. Read
> `tests/gold_harness/AGENTS.md` first (durable rules), then the
> §F2.1–F2.3 spec and §18.5 in `IMPLEMENTATION.md` (fixture gates +
> the step-2 autopsy record), then this file top to bottom. Read only
> these three files cold — everything routes from here.

## Task

**Phase A step 3**: un-elide `ACSH_EXTRUSION_CLASS`. No reader/writer
work remains — `read_history_sweep` / `write_solid_history_sweep`
already serve the EXTRUSION dxf-name through the step-2 raw-tail
retention (the model's `shsw_raw_tail` + `shsw_raw_tail_bit_len`).
Step 3 is two one-liner guard edits plus the four-gate verification
against `sh_history/Extrude_2018.dwg`.

### What already landed (do not redo)

- `b926053` (step 1): ACSH_HISTORY_CLASS un-elided; layout 6 fields
  (2 BLs + handle + BL + 2 Bs), round-trips at 0/0.
- `ba7d112` (step 2): ACSH_SWEEP_CLASS un-elided with **raw-tail
  retention** — the SWEEP/EXTRUSION wire tail is undocumented (gold
  registers the classes `DEBUGGING_CLASS`, and even a
  `-DDEBUG_CLASSES` build stops the walk at `history_node.color.flag`
  and dumps the remainder as raw unknown_bits — see §18.5). The
  reader captures the whole post-`op.minor` payload to the record's
  main-section end (`DwgMergedReader::main_end_bits()`, text-flag
  aware) into `shsw_raw_tail` (MSB-packed) + `shsw_raw_tail_bit_len`;
  the writer re-emits the bits verbatim (arm gated on
  `shsw_raw_tail_bit_len > 0`; the modeled `shsw_method`/`shsw_text`/
  `shsw_bl93`/`shsw_text2` fields are the DXF / modeled-fallback
  channel only). Verified: layer-4 bit-identical data sections on
  Polysolid_2018 and _2010; corpus 152 files gold 0/0 unchanged,
  fixtures 26/8 unchanged; the only record delta is silver's
  corpus-wide owner-handle form (`(4,2,abs)` vs authored `(6,0,+1)`,
  same identity) — pre-existing everywhere, tolerated.
- `d36e553`: §18.5 step-2 closure (autopsy + design + verification).

### Step 3 mechanics

1. `src/io/dwg/dwg_stream_writers/object_writer/objects.rs` elide
   guard (~line 310): add
   `&& d.dxf_name != "ACSH_EXTRUSION_CLASS"`.
2. `src/io/dwg/dwg_stream_writers/object_writer/entities.rs`
   `solid_history_handle_value()` (~line 5175): the same one-liner.
3. Update the two guard comments (they name the still-elided set).
4. Gates (all four, in order):
   - `cargo test --features serde` (48 ok segments, 0 failed);
   - smoke `sh_history/Extrude_2018.dwg` — expect 0/0 WITH the record
     present: original Size 70 / Hdlsize 0x1F / handle 0x2E5 (dec
     741) / `-v9` frame `Type: 520` in that file; the rewrite should
     be Size ≈ 72 (the same +2 owner-handle form bytes as step 2)
     with a bit-identical data section;
   - full corpus (152 files) — gold tree 0/0 must hold, fixtures
     expected 26/8 unchanged;
   - layer-4 byte-walk: `dump_section_bytes` both record windows
     (Address−9 margin), anchor on the parentid `BLd(-1)` bit pattern
     (`00` + 32 one-bits — the data anchors at frame-end, frame is
     40 bits R2018 / 39 bits R2010), compare [data .. data-end);
     identical is expected (data end: [0..Size×8−40−Hds−1) plus the
     text-flag bit; the handle region may differ by the known form
     delta only).

**After EXTRUSION, the fixture-diff rows it contributes do not
change** — the Extrude-family diffs are the `3DSOLID.wires` stub and
`3DSOLID.point` packets below (the harness clears the SWEEP-class
payload projection on both sides, so elide-vs-un-elide is invisible
to the diff numbers; the operative evidence for the record is the
layer-4 walk + gold's clean decode of the rewrite). Do not expect
26/8 to drop from step 3.

## The 26/8 fixture diffs decompose into three packets

From the 2026-09-23 post-step-2 corpus run (152 files, gold tree at
0/0, fixture tree 28 files):

| packet | rows | files | route |
|---|---|---|---|
| `3DSOLID.wires` stub | 16 (8 read + 8 write) | Extrude/Loft/Revolve/Sphere (R2013+R2018) | the constructed-genus zero-index wire cache — `33ce739` addressed other shape inputs; these may need the node-class blob semantics (Phase B autopsy) to produce real wires |
| `ACSH_SPHERE_CLASS` count + `UNKNOWN_OBJ` count | 8 | all 4 Sphere files | the sphere node-class ordinal alignment: silver produces a different record count than gold on the same drawing |
| `3DSOLID.point` wrong-value | 2 | Revolve_2007/2010 only | silver reads the modeler point at (0.6, 0, 0.6) where gold reads (0, 0, 0) — a constructed-genus default |

## The wire knowledge base (step-2 autopsy; §18.5 has the full record)

- The SH skeleton is verified via gold's live sphere trace: parentid
  `BLd(-1)` ('00'+LE32), eval major/minor BL (33/427), value_code
  BSd (-9999 as `00`+LE16 0xD8F1), nodeid BL(1), hist major/minor
  (33/427), 16 BD transform, CMC (44 bits — index 0, rgb c0000000,
  ByLayer), step_id BL(1), material in the handle stream, then op
  major/minor BL (33/427). The node-class tail after that is
  gold-undocumented.
- Record windows: R2018 frame = 40 bits, R2010 = 39 bits (the data
  section ends at Size×8−frame−Hds−1 with a 1-bit text-present flag
  before the handle stream; `bitsize` in gold's -v9 print is the
  handle-stream start in window bits).
- Raw-short/raw-long/raw-double on the DWG wire are LITTLE-endian;
  BD prefixes `00`/`01`/`10` = raw64/1.0/0.0.
- Payload version-portability: the same record is bit-identical
  across 2007/2010/2013/2018 except handle tails — version diffs
  are a cheap structural check.
- If Phase B (tail autopsy) needs gold traces anyway: a scratch
  `cp -a ~/work/libredwg /tmp/lredwg-debug && ./configure CFLAGS=
  "-g -O0 -DDEBUG_CLASSES" && make -C src && make -C programs
  dwgread` build STILL refuses the SWEEP-family walk (the classes
  are `DEBUGGING_CLASS` in `src/classes.inc`) — it stops at
  `color.flag` and dumps `unknown_bits`; only the skeleton is
  traceable. The scratch build is disposable — NEVER point
  GOLD_DWGREAD at it, and never edit the libredwg checkout.
- The captured tails live in the model (`shsw_raw_tail`) and in
  silver's `unknown_bits_by_handle` side channel for the
  unmodeled-class records; the side-channel hex is bit-exact with
  gold's own `unknown_bits` dump for the same record.

## Environment (complete)

The repo lives in WSL. From Windows:
`\\wsl.localhost\Ubuntu-24.04\home\sebastianschoeller\work\cadcodec`.
Shell commands run via
`wsl.exe -d Ubuntu-24.04 -- bash <script>` — write scripts with
the write tool and run by absolute path (PowerShell quoting caveats:
inline `&&`, heredocs via `wsl.exe -c`, `&&`, `$var`, pipes, and
multi-word grep alternations are all broken; ONE COMMAND PER LINE).

```bash
# Environment (source this):
export PATH="$HOME/.cargo/bin:$PATH"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
```

## Verification gate for every Phase A step

```bash
# 1. Build gates (all segments green)
cargo test --features serde

# 2. Single-fixture smoke
python3 tests/gold_harness/run_roundtrip.py \
    tests/gold_harness/tests/sh_history/<FIXTURE>.dwg /tmp/smoke

# 3. Full corpus (blocking, ~10 min; prints "[i/152]" per file, writes
#    target/gold_harness_corpus/report.md)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 bytewise check (writer form changes only):
target/debug/dump_section_bytes <origin.dwg> <A> <N>
# anchor both windows on the parentid BLd(-1) pattern, compare
# [data .. data end) bit-for-bit; handles compare by identity.
```

## Commit inventory (this halt)

```
c1200a0  docs(harness): Phase A step-3 handover — NEXT_SESSION replaced
d36e553  docs(harness): Phase A step-2 closure — SWEEP layout autopsy + queue update
ba7d112  fix(dwg): un-elide ACSH_SWEEP_CLASS — Phase A step 2, raw-tail retention
1652af2  docs(harness): document the full Phase A/B/C plan — every phase defined
96673ec  docs(harness): zero-context completeness — full Phase A handover in NEXT_SESSION + §18.5 step-2 findings
1f06d9d  chore: retire first-session scratch — the ocs.lock rules and the cylinder example
e686903  docs(harness): Phase A step-2 probe findings — the SWEEP write path loses 113 bytes
989860d  fix(docs): NEXT_SESSION encoding cleanup
086b1f1  docs(harness): ACS/SH Phase A handover — NEXT_SESSION replaced, §18.5 opens
b926053  fix(dwg): un-elide ACSH_HISTORY_CLASS — Phase A step 1
fc9f235  test(harness): F2 in-repo fixture tree — sh_history campaign
459bc74  fix(dwg): elide SH modeler-history class records at save
33ce739  fix(dwg): constructed wireframe guard
2c92b70  fix(acis): SAB restore-file record order
06756bf  fix(acis): SAB class-width completion
96d6707  fix(acis): SAB restore-file body declaration
b9211d0  fix(entities): constructed-genus constructor defaults
94533a3  fix(mleader): constructed-native stance in MultiLeader::new
21889f1  fix(build): plain cargo test clean (feature gates)
34bc702  docs(harness): zero-keeping regression gate
34a0ed9  docs(harness): specimen origin census
9dd2cd5  docs(harness): file-inventory completeness
5891cc1  chore(harness): retire stale scripts and pycache
```

The branch sits at `c1200a0`; `1f06d9d` was the last push to
`origin/gold-vs-silver` (push only when asked).
