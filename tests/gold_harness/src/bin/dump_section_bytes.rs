//! Hexdump a byte range of a decompressed DWG section (ground-truth probe).
//!
//! Usage:
//!   cargo run --bin dump_section_bytes -- INPUT_DWG ADDRESS SIZE [SECTION]
//!
//! Default section: "AcDb:AcDbObjects". Writes the raw bytes to stdout as a
//! hex dump with section-relative addresses, plus a bit string (MSB-first).
//! Used by the gold-vs-silver harness to hand-decode object records whose
//! layout diverges between the two decoders (e.g. the R2013+ 3DSOLID-family
//! inline payload).

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 4 {
        eprintln!(
            "usage: dump_section_bytes INPUT_DWG ADDRESS SIZE [SECTION]\n\
             (byte-aligned range of the decompressed section, hexdump to stdout)"
        );
        std::process::exit(2);
    }
    let path = &args[1];
    let addr: usize = args[2].parse().expect("ADDRESS must be a number");
    let size: usize = args[3].parse().expect("SIZE must be a number");
    let section = args.get(4).map(String::as_str).unwrap_or("AcDb:AcDbObjects");

    let mut reader = acadrust::io::dwg::dwg_reader::DwgReader::from_file(path).expect("open");
    let info = reader.read_file_header().expect("read file header");
    let buf = reader
        .get_section_buffer(section, &info)
        .expect("get section buffer");
    eprintln!("section {} len: {}", section, buf.len());
    let start = addr.min(buf.len());
    let end = (addr.saturating_add(size)).min(buf.len());
    let slice = &buf[start..end];
    println!();
    println!("=== dumped range: {}..{} (0x{:X}..0x{:X}) ===", start, end, start, end);
    for (i, chunk) in slice.chunks(16).enumerate() {
        let hex: Vec<String> = chunk.iter().map(|b| format!("{:02X}", b)).collect();
        println!("{:08X}: {}", start + i * 16, hex.join(" "));
    }
    // Bit string (DWG bit order: MSB first within each byte), one line per
    // 32 bits, annotated with the absolute bit position.
    println!();
    println!("=== bit string (MSB-first), absolute bit positions ===");
    for (base, chunk) in slice.chunks(4).enumerate() {
        let bit_str: String = chunk.iter().map(|b| format!("{:08b}", b)).collect();
        println!("bit {}: {}", start * 8 + base * 32, bit_str);
    }
}
