//! Derive + dump entity proxy-graphics metafiles from a DWG file.
//!
//! Usage:
//!   cargo run --bin dump_proxy_graphics -- [--verify] INPUT_DWG [HANDLE_HEX]
//!
//! The entity-common graphic blob ("preview" in gold's trace parlance) is
//! the ODA Proxy Entity Graphics metafile; its envelope and record-type
//! census are documented in `acadrust::entities::proxy_graphics`. Derived
//! from the gold tree's authored specimens (2018/Leader.dwg and the
//! native mleader samples), the stream is `[u32 total][u32 count]` plus
//! `[u32 record_size][u32 record_type][payload]` records, little-endian.
//!
//! Without a handle argument every entity carrying a metafile is listed.
//! With a handle (hex, `0x` optional) the decoded record table is printed.
//! `--verify` re-encodes the decode and asserts byte-equality against the
//! wire bytes — the derivation round-trip proof.

use acadrust::entities::{EntityType, ProxyGraphicRecord, ProxyGraphics};
use acadrust::DwgReader;

fn entity_type_name(entity: &EntityType) -> &'static str {
    match entity {
        EntityType::Point(_) => "POINT",
        EntityType::Line(_) => "LINE",
        EntityType::Circle(_) => "CIRCLE",
        EntityType::Arc(_) => "ARC",
        EntityType::Ellipse(_) => "ELLIPSE",
        EntityType::Polyline(_) => "POLYLINE",
        EntityType::Polyline2D(_) => "POLYLINE2D",
        EntityType::Polyline3D(_) => "POLYLINE3D",
        EntityType::LwPolyline(_) => "LWPOLYLINE",
        EntityType::Text(_) => "TEXT",
        EntityType::MText(_) => "MTEXT",
        EntityType::Spline(_) => "SPLINE",
        EntityType::Helix(_) => "HELIX",
        EntityType::Dimension(_) => "DIMENSION",
        EntityType::Hatch(_) => "HATCH",
        EntityType::Solid(_) => "SOLID",
        EntityType::Face3D(_) => "FACE3D",
        EntityType::Insert(_) => "INSERT",
        EntityType::Block(_) => "BLOCK",
        EntityType::BlockEnd(_) => "BLOCKEND",
        EntityType::Ray(_) => "RAY",
        EntityType::XLine(_) => "XLINE",
        EntityType::Viewport(_) => "VIEWPORT",
        EntityType::AttributeDefinition(_) => "ATTDEF",
        EntityType::AttributeEntity(_) => "ATTRIB",
        EntityType::Leader(_) => "LEADER",
        EntityType::MultiLeader(_) => "MULTILEADER",
        EntityType::MLine(_) => "MLINE",
        EntityType::Mesh(_) => "MESH",
        EntityType::RasterImage(_) => "IMAGE",
        EntityType::Solid3D(_) => "3DSOLID",
        EntityType::Region(_) => "REGION",
        EntityType::Body(_) => "BODY",
        EntityType::Surface(_) => "SURFACE",
        EntityType::Table(_) => "ACAD_TABLE",
        EntityType::Tolerance(_) => "TOLERANCE",
        EntityType::PolyfaceMesh(_) => "POLYFACEMESH",
        EntityType::Wipeout(_) => "WIPEOUT",
        EntityType::Shape(_) => "SHAPE",
        EntityType::Underlay(_) => "UNDERLAY",
        _ => "OTHER",
    }
}

fn print_records(data: &[u8], verify: bool) -> bool {
    let Some(graphics) = ProxyGraphics::decode(data) else {
        println!("  !! metafile does not decode (envelope mismatch)");
        return false;
    };
    println!(
        "  envelope: total={} bytes, {} records",
        data.len(),
        graphics.records.len()
    );
    for (index, record) in graphics.records.iter().enumerate() {
        let line = match record {
            ProxyGraphicRecord::FillOff => "FillOff".to_string(),
            ProxyGraphicRecord::UnicodeText(text) => format!(
                "UnicodeText height={} text={:?}",
                text.height, text.text
            ),
            ProxyGraphicRecord::State { record_type, value } => {
                format!("state word 0x{value:08X} (type {record_type})")
            }
            ProxyGraphicRecord::Unknown { record_type, data } => {
                let head = data
                    .iter()
                    .take(16)
                    .map(|b| format!("{b:02X}"))
                    .collect::<Vec<_>>()
                    .join(" ");
                if data.len() >= 16 {
                    format!(
                        "opaque type {record_type}, {} bytes; head: {head} ..",
                        data.len()
                    )
                } else {
                    format!("opaque type {record_type}, {} bytes: {head}", data.len())
                }
            }
        };
        println!("  [{index:2}] {line}");
    }
    if verify {
        match graphics.encode() {
            Some(reencoded) if reencoded == data => {
                println!("  verify: decode -> encode is byte-identical ({})", data.len());
                true
            }
            Some(_) => {
                println!("  verify: FAILED — re-encode differs from the wire bytes");
                false
            }
            None => {
                println!("  verify: FAILED — encode declined");
                false
            }
        }
    } else {
        true
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let verify = args.first().is_some_and(|a| a == "--verify");
    let args = if verify { args[1..].to_vec() } else { args };
    if args.is_empty() {
        eprintln!(
            "usage: dump_proxy_graphics [--verify] INPUT_DWG [HANDLE_HEX]\n\
             \n\
             Lists every entity carrying an entity-common graphic metafile,\n\
             or dumps (and with --verify byte-checks) the one with HANDLE_HEX."
        );
        std::process::exit(2);
    }
    let path = args[0].clone();
    let handle_filter = args.get(1).map(|raw| {
        let trimmed = raw.trim_start_matches("0x").trim_start_matches("0X");
        u64::from_str_radix(trimmed, 16)
            .unwrap_or_else(|_| panic!("handle {raw:?} is not hex"))
    });

    let mut reader = match DwgReader::from_file(&path) {
        Ok(reader) => reader,
        Err(error) => {
            eprintln!("cannot open {path}: {error}");
            std::process::exit(1);
        }
    };
    let document = match reader.read() {
        Ok(document) => document,
        Err(error) => {
            eprintln!("cannot read {path}: {error}");
            std::process::exit(1);
        }
    };

    let mut found = 0;
    let mut verified = true;
    for entity in document.entities() {
        let common = entity.common();
        if common.graphic_data.is_none() {
            continue;
        }
        found += 1;
        let handle = common.handle.value();
        if let Some(want) = handle_filter {
            if handle != want {
                continue;
            }
        }
        println!("{:#X} {} ({} bytes):", handle, entity_type_name(entity), {
            common.graphic_data.as_ref().map_or(0, |d| d.len())
        });
        if !print_records(common.graphic_data.as_deref().unwrap(), verify) {
            verified = false;
        }
    }
    if found == 0 {
        println!("no entity carries a graphic metafile in {path}");
    } else if let Some(want) = handle_filter {
        let _ = want;
    }
    if !verified {
        std::process::exit(1);
    }
}
