use opencadcodec::entities::EntityType;
use opencadcodec::{DwgReader, DwgWriter};

fn probe(label: &str, doc: &opencadcodec::CadDocument) {
    for entity in doc.entities() {
        if let EntityType::Solid3D(solid) = entity {
            let a = &solid.acis_data;
            println!(
                "{label}: sab={}B wf={} point_present={} isolines={} isol_present={} empty_bit={} wires={}",
                a.sab_data.len(),
                a.wireframe_data_present,
                a.wireframe_point_present,
                a.wireframe_isolines,
                a.wireframe_isoline_present,
                a.acis_empty_bit,
                solid.wires.len(),
            );
        }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let src = &args[1];
    let dst = &args[2];
    let mut reader = DwgReader::from_file(src).unwrap();
    let mut document = reader.read().unwrap();
    probe("after load", &document);

    // Simulate the OCS properties edit: rebuild the solid through the
    // modeler and set_sat_document — the modify.rs path.
    let sat = opencadcodec::entities::acis::primitives::build_cylinder([0.0, 0.0, 0.0], 1.0, 3.0);
    let handles: Vec<_> = document
        .entities()
        .filter_map(|e| match e {
            EntityType::Solid3D(_) => Some(e.common().handle),
            _ => None,
        })
        .collect();
    for h in handles {
        if let Some(EntityType::Solid3D(entity)) = document.get_entity_mut(h) {
            entity.set_sat_document(&sat);
        }
    }
    probe("after set_sat_document", &document);

    let bytes = DwgWriter::write_to_vec(&document).unwrap();
    std::fs::write(dst, &bytes).unwrap();
    println!("wrote {} bytes", bytes.len());

    let mut r2 = DwgReader::from_file(dst).unwrap();
    let d2 = r2.read().unwrap();
    probe("reloaded", &d2);
}
