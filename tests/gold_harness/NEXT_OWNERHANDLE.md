# Next task: `ownerhandle` handle-code semantics

**STATUS: DONE (2026-09-17).** Differ resolves handles by `absref` and
compares `(code, resolved_target)`; silver emits `code=None` (unknown).
Corpus: `LINE.ownerhandle` 43 778 → 0; read-fidelity 196 252 → 137 823;
write-fidelity 127 737 → 127 172. Residual `ownerhandle` rows (504) are real
silver gaps (UNKNOWN_OBJ/SECTIONVIEWSTYLE/EVALUATION_GRAPH owners silver
does not model). See `IMPLEMENTATION.md` §8.1.6.

---

**Original brief below (kept for the record).**

**Status**: ready to start. **Branch**: `gold-vs-silver` (clean, in sync with
`origin`). **Baseline**: `cargo test --features serde` = 1556 passed / 0 failed.

This file is the cold-start brief for a fresh session. Read it fully, then read
the referenced sections of `IMPLEMENTATION.md` on demand.

---

## 1. Environment (one-time)

```bash
cd ~/work/cadcodec
source "$HOME/.cargo/env"
export GOLD_DWGREAD="$HOME/work/libredwg/programs/dwgread"
export GOLD_TESTDATA="$HOME/work/libredwg/test/test-data"
python3 tests/gold_harness/check_env.py   # must print "Environment looks good"
cargo build --features serde --bins        # must succeed before any edit
```

- Silver repo: `~/work/cadcodec` (Rust crate `acadrust`).
- Gold repo: `~/work/libredwg` (C, **read-only** — never edit).
- Harness: `tests/gold_harness/`. All work happens there.

---

## 2. The problem

Gold (libredwg `dwgread -O JSON`) emits `ownerhandle` as a raw handle tuple
`[code, size, value, absref]` where **`code` is the semantic** (0 = owner is
the root/none, 4 = soft owner, 8 = hard owner, 12 = hard-pointer…). Silver
(cadcodec) stores the owner as a resolved *handle int*, which the differ maps
to the target *type name*.

Result: `gold=[4,1,182,182]` (code 4, target DICTIONARY) vs silver
`DICTIONARY` (type) — a mismatch on **every object**. It's the single largest
remaining divergence: **43 778 diffs** on the corpus (~22% of the read-fidelity
total), and it contaminates every per-type packet (SCALE, XRECORD, LAYOUT, …).

**Current corpus baseline** (`target/gold_harness_corpus/report.md`):

| `(type, field)` | count |
|---|---|
| `LINE.ownerhandle` | 43 778 |
| `SCALE.reactors` | 3 833 |
| `DICTIONARY.reactors` | 1 824 |
| `DICTIONARYVAR.reactors` | 1 552 |
| `XRECORD.ownerhandle` | 1 124 |

A representative per-file baseline (clean, post-packet): `Line.dwg` at
`target/gh_final_2000/Line_diff_orig.json` = **880 read-fidelity diffs**, of
which ~116 are `ownerhandle`.

---

## 3. The fix — design

The comparison rule in `tests/gold_harness/diff_fields.py` must change from
**resolved-type-only** to **`(code, resolved_target)`**. This is a faithful,
data-preserving change — NOT a tolerance. It belongs to the same class as the
existing handle→type resolution.

**Gold side** (`normalize_gold.py`): keep the `code` in the normalized handle
so the differ can compare it. Currently `handle` is flattened to a dict
`{code, size, value, absref}` — verify it's preserved through normalization.

**Silver side** (`normalize_silver.py`): the silver `owner_handle` is a plain
int; it has no `code`. The comparison must therefore treat silver's code as
"unknown/derived" and match on `(gold_code, gold_target_type) == (?, silver_target_type)`
where the code semantics agree. Specifically:
- gold `code=0` (root/none) ↔ silver owner resolving to the root dictionary
- gold `code=4/8/12` (owner) ↔ silver owner resolving to the owning
  DICTIONARY/CONTROL object

**Differ** (`diff_fields.py`): in `resolve_handle` / `values_equal`, compare
handle-valued fields by `(code, target_type)`, not `target_type` alone. A
handle that resolves on one side but not the other is `wrong_value`, not
`missing`.

**Hard rule**: `diff_fields.py` is a protected oracle file. The change must be
a *correct comparison*, never a tolerance that hides real ownership bugs. If
the fix can't be made faithful, stop and document why.

---

## 4. Reading list (do NOT read whole files)

1. `tests/gold_harness/IMPLEMENTATION.md` §3 (handle-comparison design +
   known limitation) and §8.1.6 (work queue).
2. Gold handle semantics: `~/work/libredwg/src/common_object_handle_data.spec`
   (the `ownerhandle` line + code meaning) — grep for `ownerhandle`, read the
   surrounding ~20 lines.
3. The differ: `tests/gold_harness/diff_fields.py` (208 lines — read it fully;
   it's small).
4. The normalizers' handle paths:
   - `normalize_gold.py`: the `handle`/`ownerhandle` flattening (grep `def normalize_value`, read the dict branch).
   - `normalize_silver.py`: `_object_common_fields` and the `owner_handle` → `ownerhandle` projection (grep `ownerhandle`).

---

## 5. Workflow

1. Reproduce the baseline: run `run_roundtrip.py` on `2000/Line.dwg`, confirm
   ~116 `ownerhandle` diffs.
2. Make the differ + normalizer change.
3. Re-run on `2000/Line.dwg` — `ownerhandle` diffs must drop toward 0 and
   `total_diffs` must NOT increase.
4. Run the full corpus (`run_corpus.py`) — the `LINE.ownerhandle` count must
   collapse from 43 778.
5. Regression gate (must all pass):
   - `cargo test`
   - `cargo test --features serde`
   - `cargo test --features gold-harness --test gold_roundtrip`
6. Commit with a message explaining the comparison-rule change and the before/
   after corpus counts. Push.

---

## 6. If it can't be done faithfully

Mark it `BLOCKED: ownerhandle — <reason>` in `IMPLEMENTATION.md` §8.1.6 and
move to the next packet (SCALE/XRECORD/DICTIONARYVAR `reactors` storage, or
BLOCK_HEADER topology). Do NOT force a tolerance into the differ.

---

## 7. Reference: the fix pattern from this session

The EntityCommon/VisualStyle/DIMSTYLE/SCALE/XRECORD/DICTIONARYVAR/LWPOLYLINE
work all followed the same recipe — consult gold spec → locate silver →
minimal version-gated edit → verify on all 6 versions → regression gate →
commit. `IMPLEMENTATION.md` §8.1 has the full operating manual.
