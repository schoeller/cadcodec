//! BricsCAD probe pair (2026-09-25, old-entity-stream restoration round).
//!
//! The verdict matrix: gen_all @ 9ed5e42 (OLD entity stream + classic
//! SAB + ds_version=1 container) opened clean in BricsCAD, while every
//! probe carrying the 37a0675 entity-stream "fixes" failed — so the
//! fixes were reverted (66d25bf) and these probes restore the passing
//! form. The gold oracle MISPARSES native R2013+ 3DSOLID records too
//! (its "clean" Box_2018 decode carried garbage revision_major /
//! end_marker values); BricsCAD is the authority, not libredwg.
//!
//! 1. cyl_control_probe.dwg - gen_all's own cylinder SAB (the
//!    BricsCAD-accepted content) through a single-solid document.
//!    Expected: PASS (this is byte-equivalent to the passing gen_all
//!    solid's form).
//! 2. box_nativeblob_probe.dwg - the authored Box_2018 fixture's SAB
//!    injected VERBATIM. Discriminates the blob-dialect pairing
//!    question independently of the entity stream.
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

    if let Some((sab, reference)) =
        extract_first_solid("gen_all_entities_all_versions.dwg")
    {
        single_solid_probe(sab, reference, &format!("{out}/cyl_control_probe.dwg"));
    } else {
        println!("gen_all: no Solid3D found");
    }

    if let Some((sab, reference)) =
        extract_first_solid("tests/gold_harness/tests/sh_history/Box_2018.dwg")
    {
        single_solid_probe(sab, reference, &format!("{out}/box_nativeblob_probe.dwg"));
    } else {
        println!("Box_2018 fixture: no Solid3D found");
    }
}
