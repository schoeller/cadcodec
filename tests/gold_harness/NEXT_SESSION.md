# Zero-context prompt — the surface-parser row: un-quarantining the differential twins

> Campaign state 2026-09-24 (final halt of the ACS/SH campaign).
> **The three-phase campaign is COMPLETE at 0/0: the corpus stands
> at 260 files, read 0, write 0** (the 180 campaign baseline + the
> landed §18.7 differential quads — every solid-history stem the
> recipe ever asked for). The maintainer's fixture surface is
> EMPTY: no new DWG authoring is requested. **Twenty files sit in
> `tests_quarantine/sh_history/` behind one parser gap — closing
> that gap is this session's primary task.** Read
> `tests/gold_harness/AGENTS.md` first, then §F2.1–F2.3 and
> §18.5–18.7 in `IMPLEMENTATION.md` (§18.6 is the decode record
> with every grammar finding and its evidence chain; §18.7 the
> differential recipe with every row's OBSERVED outcome), then
> this file top to bottom.

## The task: the surface-parser row (the primary work)

**What is quarantined and why**: 20 valid AutoCAD-authored files —
the 3 surface-twin stems (`ExtrudeM`/`LoftM`/`RevolveM`, 12 files,
authored with `MOde` = Surface deliberately) and the 8
surface-mode first attempts of `ExtrudeC`/`LoftC` (the sticky
option; their Solid re-authors are in-corpus). Gold reads every
one cleanly, but silver lacks the parsers for what they contain:
the R2007+ **surface entities** and the **ASSOC surface action
bodies** — 14 read+write diffs per extrude/revolve file, 12–13 per
loft file. The corpus zero-keeping rule excludes them until silver
parses those classes.

**The oracle is ready and typed**: gold's spec blocks are LIVE for
all of it (in `~/work/libredwg/src/dwg2.spec`):

- `EXTRUDEDSURFACE` / `SWEPTSURFACE` read the full SWEEPOPTIONS
  macro (sweep_vector, the 16-BD sweep transmatrix, draft angles,
  twist, `sweep_alignment_flags` with its 0–3 enum, `path_flags`,
  `base_point_set`, the `*_transform_computed` flags,
  `reference_vector_for_controlling_twist`);
- `REVOLVEDSURFACE` reads axis_point / axis_vector /
  revolve_angle / start_angle / the 16-BD transmatrix /
  draft_angle / draft distances / twist / solid / close_to_axis;
- `LOFTEDSURFACE` reads the loft transmatrix,
  `plane_normal_lofting_type`, the start/end draft angle+magnitude
  pair, `arc_length_parameterization`, `no_twist`,
  `align_direction`;
- the `ASSOC* SURFACEACTIONBODY` objects parse with NAMED
  pab-values the fixtures already show: `ExtrusionHeight = 2.0`,
  `ExtrusionTaperAngle = 0.0` (ExtrudeM), `Continuity = 1,1`,
  `Bulge = 0.5, 0.5` (LoftM), `RevolveAngle = π` (RevolveM).

**The work**: add the surface-entity readers and the ASSOC surface
action-body parsers to silver (the campaign's established method —
gold is the oracle, the spec field lists are the layouts, the
quarantined fixtures are the specimens; see how the SH classes
were done in §18.5/§18.6). Then move the 20 files into
`tests/gold_harness/tests/sh_history/` (drop the
`tests_quarantine` gitignore negation when the tree is empty),
regenerate their `.txt` companions' quarantine notes to the
landed state, and run the four gates — the corpus goes 260 → 280
at 0/0.

**The payoff beyond the count**: the un-quarantined twins are
typed semantic anchors for the last unnamed slots — LoftM's
LOFTEDSURFACE start/end draft fields name the SH loft tail's
`[π/2, π/2]` pair (the LoftD stem died: no settings path in the
authoring AutoCAD); RevolveM's REVOLVEDSURFACE post-angle fields
are the candidates for the SH revolve tail's six option shorts
and two flag bits (which have NO authoring path through the
REVOLVE command itself).

## The secondary rows (decoder work, no new fixtures needed)

1. **The post-corner singles walk** (sweep): the entries are
   CLASSIFIED (§18.7's Polysolid rows: the width single at bit
   1084, the record constant 4.00024414192312, the
   profile-derived 2.0109/@900/@1092, the path-derived segment
   end) but not yet collected as typed model fields — extend
   `sh_tail_decode.rs` past the corner blocks with a proper BD
   walk and pin the spans.
2. **The loft container walk**: the raw-run reading is CLOSED
   (per-section `[center.x][center.y][height][radius]` runs +
   the `[π/2, π/2]` draft pair; §18.6) but the model keeps
   `raw_doubles` positional — the inter-value regions need a
   walk before the per-section fields can be exposed as named
   model fields.
3. **The ExtrudeP polyline header**: the profile CALL kind 77
   body (length 544) holds the packed (x, y) vertex array; the
   embedded-lwpolyline grammar is ALREADY in-repo
   (`read_embedded_lwpolyline` in the object readers) — wire it
   into the CALL body decode.

**Dead / no-path rows** (do not re-litigate): `LoftD` (no
settings path in the authoring release); the SH revolve option
shorts + flags through the REVOLVE command (they close via
RevolveM above or stay marked); **BREP stays deferred** — only an
external authentic `ACSH_BREP_CLASS` specimen re-opens it.

## The standing facts (the decode authority is §18.6)

- The four raw-retained SH tails decode to typed views with the
  captured bits as the write authority (the Phase B write rule:
  `render_*_tail` splices only differing same-form spans;
  untouched records re-emit bit-identically — pinned by the
  hermetic suite).
- REVOLVE is fully closed (the CALL grammar); SWEEP/EXTRUSION
  through the spine + the profile CALL; LOFT through the
  per-section raw run. The hermetic cover is
  `tests/solid_history_tail_decode.rs` (15 tests) + the module
  tests in `sh_tail_decode.rs` — all run under gate 1.

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

# 3. Full corpus (must stay 260 files 0/0; 280 after the
#    un-quarantine lands)
python3 tests/gold_harness/run_corpus.py

# 4. Layer-4 byte-walk for any writer re-encode path
target/debug/dump_section_bytes <file> <A> <N>
```

## Commit inventory (this halt)

```
<this handover pair: the AGENTS.md pointer fix + the NEXT_SESSION.md rewrite>                                 <- HEAD (see the push note)
55922b9 docs(harness): the halt refresh — the session inventory through PolysolidL, the push state recorded
122d607 test(harness): PolysolidL lands — the probe is decisive, the maintainer fixture surface closes
3a03b80 test(harness): the re-authored ExtrudeC/LoftC land — the pre-CALL region resolved, the loft raw run fully named
c051597 docs(harness): the PolysolidL P2 row — the path-length probe on the last unnamed sweep single
9ee3614 test(harness): the closing-set review — Polysolid W-quad lands naming the width single; the surface-mode C-quads quarantine; LoftD dead
1bafae7 docs(harness): the closing set — four stems to finish Phase B, plus the wire-verified loft reading
21ebde4 docs(harness): the post-landing review pass — stale decoder-state claims cleared, the halt records refreshed   <- PUSHED (origin/gold-vs-silver)
5c89b59 fix(dwg): the sweep spine named + the extrusion profile CALL — §18.7 differential decode
57232a6 test(harness): the §18.7 differential set lands — 14 solid stems in-corpus, 3 M-stems quarantined
... (the full session arc: 804e892, daedfb7, 05368b3, 839012c, a656f99,
9d08280, ac547e7, 86ce5a7, f2891b1, 7f2a77f, 9a260ae, e1dff05)
```

**PUSH STATE**: `origin/gold-vs-silver` sits at the pushed
`21ebde4`; the eight local commits after it (`1bafae7` through
this handover pair) are unpushed — **push first** so the session
starts from the remote head (push only when the maintainer asks;
they have asked for pushes at every halt so far).

(The session's arc, for context: the Phase B halt + review pass;
the §18.7 differential recipe; the RevolveA/R quads; the plan-view
axis correction; the crossing-class theory dead on the
maintainer's refusal; the full-tree libredwg scan closing the
revolve family; the maintainer authoring the full 17-stem §18.7
set; the sweep spine + extrusion profile CALL decode; the closing
set — PolysolidW naming the width single, the surface-mode
C-quads quarantined then re-authored Solid (ExtrudeC resolving the
pre-CALL region, LoftC naming the loft raw run), LoftD dead, and
PolysolidL's decisive profile-derived probe emptying the
maintainer fixture surface. Corpus 260 files, read 0, write 0;
cargo test 49 suites ok; the quarantine holds 20 files behind the
surface-parser row — the next session's work.)
