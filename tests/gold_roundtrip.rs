//! Integration test for the gold-vs-silver roundtrip harness.
//!
//! Gated behind the `gold-harness` feature. Requires the env vars:
//!   - GOLD_DWGREAD: path to a built libredwg `dwgread` binary.
//!   - GOLD_TESTDATA: path to libredwg `test/test-data` directory.
//!
//! Shells out to `tests/gold_harness/run_roundtrip.py`. By default only checks
//! that the harness runs without crashing. With GOLD_HARNESS_STRICT=1 it
//! asserts zero `missing_in_silver` diffs for the representative subset and
//! asserts that the storage-only `EntityCommon` fields (`z_is_zero`,
//! `ltype_flags`, `prev_entity`, `next_entity`, `nolinks`) never appear in the
//! read-fidelity or rewrite-fidelity diffs.

use std::path::{Path, PathBuf};
use std::process::Command;

const DRIVER: &str = "tests/gold_harness/run_roundtrip.py";

fn cargo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn run_harness(input: &Path, workdir: &Path) -> std::process::Output {
    let script = cargo_root().join(DRIVER);
    let mut cmd = Command::new("python3");
    cmd.arg(&script)
        .arg(input)
        .arg(workdir)
        .current_dir(cargo_root());
    if let Some(v) = std::env::var_os("GOLD_DWGREAD") {
        cmd.env("GOLD_DWGREAD", v);
    }
    if let Some(v) = std::env::var_os("GOLD_TESTDATA") {
        cmd.env("GOLD_TESTDATA", v);
    }
    cmd.output().expect("failed to execute harness driver")
}

/// Fields that come from `EntityCommon` storage-only values. They must never
/// appear in a read-fidelity diff because they are round-trip metadata, not
/// application-visible entity state.
const PROHIBITED_COMMON_FIELDS: &[&str] = &[
    "z_is_zero",
    "ltype_flags",
    "prev_entity",
    "next_entity",
    "nolinks",
];

#[test]
fn gold_harness_runs_on_representative_files() {
    let testdata = std::env::var_os("GOLD_TESTDATA")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(std::env!("CARGO_MANIFEST_DIR")));

    let representative = [testdata.join("2000/Line.dwg")];
    let workdir = PathBuf::from(std::env::var_os("OUT_DIR").unwrap_or_else(|| "/tmp".into()))
        .join("gold_harness_test");

    for file in representative {
        if !file.exists() {
            eprintln!("skipping missing gold file: {}", file.display());
            continue;
        }
        let out = run_harness(&file, &workdir.join(file.file_stem().unwrap()));
        let stdout = String::from_utf8_lossy(&out.stdout);
        let stderr = String::from_utf8_lossy(&out.stderr);
        assert!(
            out.status.success(),
            "harness failed for {}\nstdout:\n{}\nstderr:\n{}",
            file.display(),
            stdout,
            stderr
        );

        let diff_paths = [
            workdir.join(file.file_stem().unwrap()).join(format!(
                "{}_diff_orig.json",
                file.file_stem().unwrap().to_string_lossy()
            )),
            workdir.join(file.file_stem().unwrap()).join(format!(
                "{}_diff_rt.json",
                file.file_stem().unwrap().to_string_lossy()
            )),
        ];

        for diff_path in &diff_paths {
            assert!(
                diff_path.exists(),
                "diff file missing for {}: {}",
                file.display(),
                diff_path.display()
            );
            let diff: serde_json::Value =
                serde_json::from_reader(std::fs::File::open(diff_path).unwrap()).unwrap();
            let diffs = diff.get("diffs").and_then(|v| v.as_array()).unwrap();

            let prohibited: Vec<&serde_json::Value> = diffs
                .iter()
                .filter(|d| {
                    d.get("field")
                        .and_then(|f| f.as_str())
                        .map(|f| PROHIBITED_COMMON_FIELDS.contains(&f))
                        .unwrap_or(false)
                })
                .collect();
            assert!(
                prohibited.is_empty(),
                "{} contains prohibited EntityCommon fields for {}: {:?}",
                diff_path.file_stem().unwrap().to_string_lossy(),
                file.display(),
                prohibited
            );
        }

        if std::env::var_os("GOLD_HARNESS_STRICT").is_some() {
            let diff: serde_json::Value =
                serde_json::from_reader(std::fs::File::open(&diff_paths[0]).unwrap()).unwrap();
            let diffs = diff.get("diffs").and_then(|v| v.as_array()).unwrap();
            let missing: Vec<&serde_json::Value> = diffs
                .iter()
                .filter(|d| d.get("kind").and_then(|k| k.as_str()) == Some("missing_in_silver"))
                .collect();
            assert!(
                missing.is_empty(),
                "missing_in_silver diffs for {}: {:?}",
                file.display(),
                missing
            );
        }
    }
}
