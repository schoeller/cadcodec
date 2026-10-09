use opencadcodec::DwgReader;

fn gold_types_entity_class(dxf_name: &str) -> bool {
    matches!(
        dxf_name,
        "ARC_DIMENSION"
            | "CAMERA"
            | "DGNUNDERLAY"
            | "DWFUNDERLAY"
            | "HATCH"
            | "HELIX"
            | "IMAGE"
            | "LARGE_RADIAL_DIMENSION"
            | "LAYOUTPRINTCONFIG"
            | "LIGHT"
            | "LWPOLYLINE"
            | "MESH"
            | "MULTILEADER"
            | "OLE2FRAME"
            | "PDFUNDERLAY"
            | "PLANESURFACE"
            | "POINTCLOUD"
            | "POINTCLOUDEX"
            | "SECTIONOBJECT"
            | "WIPEOUT"
    )
}

fn main() {
    let path = std::env::args().nth(1).expect("file");
    let mut reader = DwgReader::from_file(&path).unwrap();
    let document = reader.read().unwrap();
    println!("== {path}: {} classes", document.classes.len());
    for c in document.classes.iter() {
        let in_set = if c.class_number < 500 {
            false
        } else {
            match c.gold_shadow.as_ref() {
                Some(sh) => {
                    sh.item_class_id == 498u16
                        || (document.version >= opencadcodec::DxfVersion::AC1021
                            && gold_types_entity_class(&c.dxf_name)
                            && c.is_an_entity)
                }
                None => c.is_an_entity,
            }
        };
        let shadow = c
            .gold_shadow
            .as_ref()
            .map(|sh| format!("num={} item=0x{:x} zombie={}", sh.number, sh.item_class_id, sh.is_zombie))
            .unwrap_or_else(|| "no-shadow".into());
        let flag = if in_set { "  <== ENTITY-SET" } else { "" };
        println!(
            "class {} num={} is_entity={} item_id=0x{:x} {}{}",
            c.dxf_name,
            c.class_number,
            c.is_an_entity,
            c.item_class_id,
            shadow,
            flag
        );
    }
}
