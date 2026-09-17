//! DWG rewrite binary for the silver round-trip harness.
//!
//! Usage:
//!   cargo run --bin dwgrewrite --features serde -- INPUT_DWG [OUTPUT_DWG]
//!
//! Reads a DWG file and writes it back out. The default output path is
//! `<input>_rt.dwg`. This binary intentionally performs *no* semantic
//! comparison; it just exercises the read -> write path.

use std::path::PathBuf;

use acadrust::{CadDocument, DwgReader, DwgWriter};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: dwgrewrite INPUT_DWG [OUTPUT_DWG]");
        std::process::exit(1);
    }
    let input = PathBuf::from(&args[1]);
    let output = args.get(2).map(PathBuf::from).unwrap_or_else(|| {
        let mut p = input.clone();
        let stem = p
            .file_stem()
            .map(|s| s.to_string_lossy().into_owned())
            .unwrap_or_else(|| "output".to_string());
        p.set_file_name(format!("{}_rt.dwg", stem));
        p
    });

    let mut reader = DwgReader::from_file(&input)?;
    let doc: CadDocument = reader.read()?;

    DwgWriter::write_to_file(&output, &doc)?;
    println!("Wrote {}", output.display());
    Ok(())
}
