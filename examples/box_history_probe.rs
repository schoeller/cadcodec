//! BricsCAD probe ladder (2026-09-24): two extraction probes that
//! isolate the failing variable of the BOX campaign. The elided +
//! rank-ordered host-chain probe was still refused ("General modeling
//! failure / Object improperly read: <AcDb3dSolid> / Invalid input")
//! with zero SH records and the native class ranking, so the remaining
//! variables are the SAT CONTENT and the embedding container.
//!
//! 1. box_nativeblob_probe.dwg - the byte-proven SAB of the authored
//!    Box_2018 fixture injected VERBATIM (Solid3D::from_sab) into a
//!    fresh single-entity document: if this fails, the container or
//!    embedding is the culprit; if it passes, the SAT content is.
//! 2. cyl_control_probe.dwg    - the byte-proven SAB of gen_all's
//!    cylinder (the Solid3D BricsCAD accepts inside the gen_all file)
//!    injected into the same minimal container: the passing control
//!    that validates the probe methodology itself.
use acadrust::entities::Solid3D;
use acadrust::types::{DxfVersion, Vector3};
use acadrust::{CadDocument, DwgReader, DwgWriter, EntityType};

fn extract_first_solid(path: &str) -> Option<(Vec<u8>, Vector3)> {
    let document = DwgReader::from_file(path).ok()?.read().ok()?;
    for entity in document.entities() {
        if let EntityType::Solid3D(value) = entity {
            let sab = value.acis_data.sab_data.clone();
            return Some((sab, value.point_of_reference));
        }
    }
    None
}

fn single_solid_probe(sab: Vec<u8>, reference: Vector3, out: &str) {
    let mut doc = CadDocument::with_version(DxfVersion::AC1032);
    let mut solid = Solid3D::from_sab(sab);
    solid.point_of_reference = reference;
    doc.add_entity(EntityType::Solid3D(solid)).expect("add");
    DwgWriter::write_to_file(out, &doc).expect("write");
    println!("wrote {out}");
}

fn main() {
    let out = "/mnt/c/Users/SebastianSchoeller/Downloads";

    // 1. Native-box SAB verbatim (authored, BricsCAD-accepted bytes).
    if let Some((sab, reference)) =
        extract_first_solid("tests/gold_harness/tests/sh_history/Box_2018.dwg")
    {
        single_solid_probe(sab, reference, &format!("{out}/box_nativeblob_probe.dwg"));
    } else {
        println!("Box_2018 fixture: no Solid3D found");
    }

    // 2. gen_all cylinder SAB verbatim (the BricsCAD-accepted control).
    if let Some((sab, reference)) =
        extract_first_solid("gen_all_entities_all_versions.dwg")
    {
        single_solid_probe(sab, reference, &format!("{out}/cyl_control_probe.dwg"));
    } else {
        println!("gen_all: no Solid3D found");
    }
}
