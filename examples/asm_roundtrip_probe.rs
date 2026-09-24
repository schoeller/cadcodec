//! TEMPORARY ASM round-trip validator (2026-09-24, remove after the
//! campaign): reads the authored Box_2018 fixture's SAB through
//! SabReader and re-emits it through SabWriter::write_asm, byte-comparing
//! the result. The reader parses natives correctly (corpus 0/0), so any
//! divergence here is a writer encoding gap - the exact list of forms
//! to_asm_structure must learn.
use acadrust::entities::acis::{SabReader, SabWriter};
use acadrust::{DwgReader, EntityType};

fn main() {
    let document = DwgReader::from_file("tests/gold_harness/tests/sh_history/Box_2018.dwg")
        .unwrap()
        .read()
        .unwrap();
    let mut original = None;
    for entity in document.entities() {
        if let EntityType::Solid3D(value) = entity {
            original = Some(value.acis_data.sab_data.clone());
            break;
        }
    }
    let original = original.expect("fixture solid");
    let parsed = SabReader::read(&original).expect("reader parses native ASM");
    let reemitted = SabWriter::write_asm(&parsed);

    println!("original  len: {}", original.len());
    println!("reemitted len: {}", reemitted.len());
    if original == reemitted {
        println!("ROUND-TRIP: byte-identical");
    } else {
        let mut first = None;
        for (i, (a, b)) in original.iter().zip(reemitted.iter()).enumerate() {
            if a != b {
                first = Some(i);
                break;
            }
        }
        match first {
            Some(i) => {
                fn hex(bytes: &[u8]) -> String {
                    bytes.iter().map(|b| format!("{b:02x}")).collect::<Vec<_>>().join(" ")
                }
                println!("FIRST DIVERGENCE at byte {i}");
                println!("  original : {}", hex(&original[i..(i + 48).min(original.len())]));
                println!("  reemitted: {}", hex(&reemitted[i..(i + 48).min(reemitted.len())]));
                let common = original.iter().zip(reemitted.iter()).take_while(|(a, b)| a == b).count();
                println!("  common prefix: {common}");
            }
            None => println!("prefix identical; length differs by {}", original.len().abs_diff(reemitted.len())),
        }
    }

    // Constructed-form check: a primitive-built box through
    // to_sab_asm_checked — its asmheader/transform must byte-match the
    // native framing.
    let mut box_doc = acadrust::entities::acis::SatDocument::new_body();
    box_doc.add_plane_surface([0.0, 0.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]);
    let asm = box_doc.to_sab_asm_checked().expect("asm");
    let find_sub = |needle: &[u8]| asm.windows(needle.len()).position(|w| w == needle);
    let i = find_sub(b"asmheader").expect("asmheader");
    println!("constructed asmheader: {}", asm[i - 2..i + 40].iter().map(|b| format!("{b:02x}")).collect::<Vec<_>>().join(" "));
    let j = find_sub(b"transform").expect("transform");
    println!("constructed transform : {}", asm[j - 2..j + 24].iter().map(|b| format!("{b:02x}")).collect::<Vec<_>>().join(" "));
    let mut triple = [0u32; 3];
    for (k, slot) in triple.iter_mut().enumerate() {
        *slot = u32::from_le_bytes(asm[19 + k * 4..23 + k * 4].try_into().unwrap());
    }
    println!("constructed header triple: {triple:?}");
}
