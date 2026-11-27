//! Block-member ownership: a member entity lives in exactly ONE block-record
//! chain — never also in model space.
//!
//! Packet C's C-1 (found by the L3 app census, invisible to the codec family
//! compare): a builder that registers the block record AFTER adding its
//! members — or owns them by the BLOCK marker handle instead of the record
//! handle — falls through `CadDocument::add_entity`'s owner routing into the
//! `*Model_Space` fallback. The written file then lists every member under
//! both its record and model space: the record chain still compares
//! bit-exact, but any host that walks model space sees the members twice
//! (Parcel-1A +343, Align-6C/Points-3 +371 native entities, and the member
//! INSERTs as extra model-space block references).

use std::io::Cursor;

use acadrust::entities::{Circle, Insert, Line};
use acadrust::tables::BlockRecord;
use acadrust::types::{DxfVersion, Handle, Vector3};
use acadrust::{CadDocument, DwgReader, DwgWriter, EntityType};

/// The wiring the corpus builder uses (examples/corpus_roundtrip.rs): the
/// record is registered FIRST and owns its members by the record handle, so
/// `add_entity` routes each member into the record's chain.
fn wired() -> CadDocument {
    let mut doc = CadDocument::with_version(DxfVersion::AC1032);
    let mut record = BlockRecord::new("leak_probe");
    record.handle = doc.allocate_handle();
    record.block_entity_handle = doc.allocate_handle();
    record.block_end_handle = doc.allocate_handle();
    let record_handle = record.handle;
    doc.block_records.add(record).unwrap();

    let mut line = Line::from_points(Vector3::ZERO, Vector3::new(1.0, 0.0, 0.0));
    line.common.owner_handle = record_handle;
    let mut circle = Circle::from_center_radius(Vector3::ZERO, 1.0);
    circle.common.owner_handle = record_handle;
    doc.add_entity(EntityType::Line(line)).unwrap();
    doc.add_entity(EntityType::Circle(circle)).unwrap();

    let mut ins = Insert::new("leak_probe", Vector3::ZERO);
    ins.common.owner_handle = Handle::NULL; // model space by default
    doc.add_entity(EntityType::Insert(ins)).unwrap();
    doc
}

/// A handle must be listed by at most one block record, and model space must
/// carry exactly the one insert (the reference) — no duplicated members.
fn check_ownership(doc: &CadDocument, what: &str) {
    let mut chains: std::collections::HashMap<u64, Vec<&str>> = Default::default();
    for r in doc.block_records.iter() {
        for h in &r.entity_handles {
            chains.entry(h.value()).or_default().push(r.name.as_str());
        }
    }
    let doubled: Vec<(u64, Vec<&str>)> = chains.iter()
        .filter(|(_, n)| n.len() > 1)
        .map(|(h, n)| (*h, n.clone()))
        .collect();
    assert!(
        doubled.is_empty(),
        "{what}: entity handle(s) reachable from more than one block-record chain: {doubled:?}"
    );

    let ms = doc.header.model_space_block_handle;
    let ms_record = doc
        .block_records
        .iter()
        .find(|r| r.handle == ms)
        .unwrap_or_else(|| panic!("{what}: no model-space record"));
    for h in &ms_record.entity_handles {
        assert!(
            !matches!(
                doc.get_entity(*h),
                Some(EntityType::Line(_)) | Some(EntityType::Circle(_))
            ),
            "{what}: a block member ({h:?}) is reachable from model space — the C-1 leak"
        );
    }
    let inserts = ms_record
        .entity_handles
        .iter()
        .filter(|h| matches!(doc.get_entity(**h), Some(EntityType::Insert(_))))
        .count();
    assert_eq!(inserts, 1, "{what}: model-space insert count (one per reference)");
}

#[test]
fn block_members_live_only_in_their_record() {
    let doc = wired();
    check_ownership(&doc, "built document");

    let dwg = DwgWriter::write_to_vec(&doc).unwrap();
    let read = DwgReader::from_stream(Cursor::new(dwg)).read().unwrap();
    check_ownership(&read, "dwg roundtrip");
}
