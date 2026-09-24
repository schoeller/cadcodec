//! TEMPORARY BricsCAD probe (2026-09-24, remove after the campaign):
//! the host BOX construction — a Solid3D carrying a box SAT plus the
//! solid-history tree from CadDocument::create_solid_history — written
//! to Downloads for the strict-loader verdict (mirrors Wuerfel.dwg:
//! dims 1x1x2, reference point 0.5/0.5/0).
use acadrust::entities::Solid3D;
use acadrust::objects::{SolidHistoryBox, SolidHistoryOperation};
use acadrust::types::{DxfVersion, Vector3};
use acadrust::{CadDocument, DwgWriter, EntityType};

fn main() {
    let sat = acadrust::entities::acis::primitives::build_planar_body(
        &[
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 2.0],
            [1.0, 0.0, 2.0],
            [1.0, 1.0, 2.0],
            [0.0, 1.0, 2.0],
        ],
        &[
            vec![0, 3, 2, 1],
            vec![4, 5, 6, 7],
            vec![0, 1, 5, 4],
            vec![3, 7, 6, 2],
            vec![1, 2, 6, 5],
            vec![0, 4, 7, 3],
        ],
    )
    .unwrap();

    let mut doc = CadDocument::with_version(DxfVersion::AC1032);
    let mut solid = Solid3D::new();
    // Native genus: the reference point is the box center (the node
    // transform translation) - the Wuerfel autopsy showed the host
    // computing a different value.
    solid.point_of_reference = Vector3::new(0.5, 0.5, 1.0);
    solid.set_sat_document(&sat);
    let handle = doc.add_entity(EntityType::Solid3D(solid)).unwrap();

    doc.create_solid_history(
        handle,
        SolidHistoryOperation::Box(SolidHistoryBox {
            length: 1.0,
            width: 1.0,
            height: 2.0,
            ..SolidHistoryBox::default()
        }),
    )
    .unwrap();

    DwgWriter::write_to_file(
        "/mnt/c/Users/SebastianSchoeller/Downloads/box_history_probe.dwg",
        &doc,
    )
    .unwrap();
    println!("wrote box_history_probe.dwg");
}
