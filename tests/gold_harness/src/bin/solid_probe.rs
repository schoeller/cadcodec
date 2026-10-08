use opencadcodec::entities::EntityType;
use opencadcodec::DwgReader;

fn describe(path: &str) {
    let mut reader = DwgReader::from_file(path).unwrap();
    let document = reader.read().unwrap();
    println!("== {path} (source {:?})", document.dwg_source_version);
    for entity in document.entities() {
        if let EntityType::Solid3D(solid) = entity {
            let a = &solid.acis_data;
            println!(
                "Solid3D h={} sat={}B sab={}B binary={} wf={} point_present={} isolines={} isol_present={} empty_bit={} wires={} silhouettes={} hist={:?} materials={}",
                solid.common.handle.value(),
                a.sat_data.len(),
                a.sab_data.len(),
                a.is_binary,
                a.wireframe_data_present,
                a.wireframe_point_present,
                a.wireframe_isolines,
                a.wireframe_isoline_present,
                a.acis_empty_bit,
                solid.wires.len(),
                solid.silhouettes.len(),
                solid.history_handle.map(|h| h.value()),
                a.materials.len(),
            );
            println!(
                "  revision: guid={} major={} m1={} m2={} end={}",
                a.revision.has_guid, a.revision.major, a.revision.minor1, a.revision.minor2, a.revision.end_marker
            );
        }
    }
}

fn main() {
    for p in std::env::args().skip(1) {
        describe(&p);
    }
}
