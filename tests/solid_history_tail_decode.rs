//! Phase B blob-autopsy tests: the raw-retained solid-history node
//! tails decode into the typed views, the decode is identical across all
//! four DWG versions of each family (the tails are bit-identical, the
//! Phase A cross-version anchor), and the Phase B write rule holds:
//! untouched records re-emit verbatim while a decoded-field edit lands
//! bit-locally in its raw span (same tail and record length).
//!
//! Specimen provenance: the fixture DWGs authored in the 2026-09-23
//! campaign (Extrude/Polysolid/Loft/Revolve, DWG 2007-2018; see the
//! .txt companions and IMPLEMENTATION.md F2.3). The embedded tails are
//! the captured post-`op.minor` payloads; gold gives no oracle walk for
//! these classes (DEBUGGING_CLASS), so the pinned semantics come from
//! the cross-specimen + live-oracle instruments documented there.

use acadrust::entities::{solid3d::Solid3D, EntityType};
use acadrust::io::dwg::sh_tail_decode::{
    loft_tail_view, revolve_tail_view, sweep_tail_view,
};
use acadrust::objects::{
    SolidHistoryLoft, SolidHistoryLoftTail, SolidHistoryNodeBase, SolidHistoryOperation,
    SolidHistoryRevolve, SolidHistoryRevolveTail, SolidHistorySweep, SolidHistorySweepTail,
};
use acadrust::types::DxfVersion;
use acadrust::{CadDocument, DwgReader, DwgWriter};
use std::io::Cursor;

fn unhex(value: &str) -> Vec<u8> {
    (0..value.len())
        .step_by(2)
        .map(|index| u8::from_str_radix(&value[index..index + 2], 16).unwrap())
        .collect()
}

const POLYSOLID_SWEEP_HEX: &str = "AAA9A812056ACE738225AB193DB3F8346875DD7FE0ECBF8346875DD7FE0ECBF8E738225AB193DBBFA6AA4E738225AB193DB3F8346875DD7FE0ECBF8346875DD7FE0ECBF8E738225AB193DBBFA6AA54D2A008000001020D1A1D775FF83B2FCE738225AB193DBBF9040000000000000440000000000000000000000000000004C0000000000000000000000000000004C0000000000000004000000000000004400000000000000040314D160040001040000000000000510102000000000000000000000000000000005C5B3A1004F2A740684B9EAA0BDE964000";
const POLYSOLID_SWEEP_BITS: u32 = 1738;

const EXTRUDE_SWEEP_HEX: &str = "A00000000000000102A9B2052A9AA6A9AA5AA6A9AA512442A692";
const EXTRUDE_SWEEP_BITS: u32 = 208;

const LOFT_HEX: &str = "442A6911204004000000000000000000400000000000000010000000000000014400CCCCCCCCCCCF4CFE928182D4454FB21F93F060B51153EC87E4FE9D60";
const LOFT_BITS: u32 = 492;

const REVOLVE_HEX: &str = "AA634884CDFDF3644902AA912541A26A666666666724FE90";
const REVOLVE_BITS: u32 = 190;
const REVOLVE_A_HEX: &str = "AA6060B51153EC842502AA9126400000000000000040A26A6666666667A4FE90";
const REVOLVE_A_BITS: u32 = 254;

const REVOLVE_R_HEX: &str = "AA6060B51153EC842502AA9126400000000000000040A0000000000003D0FE90";
const REVOLVE_R_BITS: u32 = 254;



#[test]
fn polysolid_sweep_tail_decodes_the_pinned_semantics() {
    let bytes = unhex(POLYSOLID_SWEEP_HEX);
    let view = sweep_tail_view(&bytes, POLYSOLID_SWEEP_BITS)
        .expect("the polysolid sweep tail must decode");
    // Head: the sweep option spine with the BD('01') scale member.
    assert_eq!(view.option_doubles, vec![0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]);
    // Mid-region raw BD entries: the path unit direction components
    // ([+u_y, -u_x, -u_x, -u_y], twice) — confirmed against the R2010
    // live-oracle anchor geometry (segment end (3065.007936309483,
    // 1463.5113930448078), unit (0.9024047208179184, 0.4308894520007826)).
    assert_eq!(
        view.raw_doubles,
        vec![
            0.4308894520007826,
            -0.9024047208179184,
            -0.9024047208179184,
            -0.4308894520007826,
            0.4308894520007826,
            -0.9024047208179184,
            -0.9024047208179184,
            -0.4308894520007826,
            -0.9024047208179184,
            -0.4308894520007826,
        ]
    );
    // Byte-aligned profile corners: the 5x2 rectangle of the polysolid
    // cross-section ((x, height) pairs; the 3DSOLID anchor z = 1.0 is
    // the pair-height mid).
    assert_eq!(
        view.profile_corners,
        vec![[2.5, 0.0], [-2.5, 0.0], [-2.5, 2.0], [2.5, 2.0]]
    );
    // Segment end in the record frame; gold's R2010 wireframe anchor
    // reads exactly its half (the live-oracle overlap).
    assert_eq!(
        view.segment_end,
        Some([3065.007936309483, 1463.5113930448078])
    );
}

#[test]
fn extrude_tail_decodes_the_pinned_semantics() {
    let view = sweep_tail_view(&unhex(EXTRUDE_SWEEP_HEX), EXTRUDE_SWEEP_BITS)
        .expect("the extrusion tail must decode");
    // The direction is the extrusion length vector (0, 0, 2.0): the
    // circle-extrude fixture stands 2 tall (live-oracle wires z 0..2).
    // `direction` itself is the SolidHistorySweep model field, reused
    // by the writer's render compare; the option spine is shared with
    // the sweep, minus the two trailing zeros.
    assert_eq!(view.option_doubles, vec![0.0, 0.0, 0.0, 0.0, 1.0, 0.0]);
    // The extrusion tail has no frame entries, profile corners or
    // segment end (its payload stays opaque; written verbatim).
    assert!(view.raw_doubles.is_empty());
    assert!(view.profile_corners.is_empty());
    assert_eq!(view.segment_end, None);
}

#[test]
fn loft_tail_decodes_the_pinned_semantics() {
    let view = loft_tail_view(&unhex(LOFT_HEX), LOFT_BITS)
        .expect("the loft tail must decode");
    assert_eq!(view.option_doubles, vec![1.0]);
    // Raw entries in stream order: the loft top height 5.0 (the wires
    // run z 0..5) and the two 90-degree draft angles (pi/2).
    assert_eq!(
        view.raw_doubles,
        vec![
            2.0,
            2.0,
            5.0,
            0.3,
            std::f64::consts::FRAC_PI_2,
            std::f64::consts::FRAC_PI_2,
        ]
    );
}

#[test]
fn revolve_tail_decodes_the_pinned_semantics() {
    let view = revolve_tail_view(&unhex(REVOLVE_HEX), REVOLVE_BITS)
        .expect("the revolve tail must decode");
    // The head is the AXIS PAIR (the REVOLVEDSURFACE twin's order):
    // axis_point then axis_vector - every landed specimen revolves
    // about the +Y axis through the origin.
    assert_eq!(view.axis_point, Some([0.0, 0.0, 0.0]));
    assert_eq!(view.axis_vector, Some([0.0, 1.0, 0.0]));
    // The revolve sweep angle: the original is 3*pi/2 (270 degrees);
    // the typed A/R quads read pi - two independent values.
    assert_eq!(view.revolve_angle, Some(3.0 * std::f64::consts::FRAC_PI_2));
    // The all-zero option run between the angle and the profile CALL.
    assert_eq!(view.option_doubles, vec![0.0; 6]);
    // The embedded profile circle (CALL: [BL 18 = OBJ_CIRCLE]
    // [BL 80][circle]): the original's circle is centered (1.0, 0, 0)
    // - the x a two-bit SHORT form (BD '01' encodes exactly 1.0) -
    // with radius 0.2 (the raw BD the earlier raw-scan mislabeled as
    // "the 0.2 entry") and the plan normal (0, 0, 1). This is the
    // as-drawn profile: the wire regression's torus M 1.0 / m 0.2.
    assert_eq!(view.profile_center, Some([1.0, 0.0, 0.0]));
    assert_eq!(view.profile_radius, Some(0.2));
    assert_eq!(view.profile_normal, Some([0.0, 0.0, 1.0]));
}

#[test]
fn revolve_matrix_stems_decode_the_structural_profile() {
    // The §18.7 RevolveA/R quads (torus M 2.0, m 0.8/1.25 about +Y,
    // wire-ladder-verified): the same CALL grammar with the circle
    // center's x a raw 2.0 (not short-encodable) and the radius raw.
    let view = revolve_tail_view(&unhex(REVOLVE_A_HEX), REVOLVE_A_BITS)
        .expect("the RevolveA tail must decode");
    assert_eq!(view.axis_point, Some([0.0, 0.0, 0.0]));
    assert_eq!(view.axis_vector, Some([0.0, 1.0, 0.0]));
    assert_eq!(view.revolve_angle, Some(std::f64::consts::PI));
    assert_eq!(view.option_doubles, vec![0.0; 6]);
    assert_eq!(view.profile_center, Some([2.0, 0.0, 0.0]));
    assert_eq!(view.profile_radius, Some(0.8));
    assert_eq!(view.profile_normal, Some([0.0, 0.0, 1.0]));

    let view = revolve_tail_view(&unhex(REVOLVE_R_HEX), REVOLVE_R_BITS)
        .expect("the RevolveR tail must decode");
    assert_eq!(view.revolve_angle, Some(std::f64::consts::PI));
    assert_eq!(view.profile_center, Some([2.0, 0.0, 0.0]));
    // The radius-only variable: R's 1.25 lands at A's radius span.
    assert_eq!(view.profile_radius, Some(1.25));
    assert_eq!(view.profile_normal, Some([0.0, 0.0, 1.0]));
}

#[test]
fn revolve_profile_edits_land_bit_locally() {
    // The CALL fields are splice-backed: editing the profile radius
    // on the RevolveA tail lands inside its raw value span only
    // (bits [182..246), bytes 22..=30).
    let tail = unhex(REVOLVE_A_HEX);
    let mut document = CadDocument::with_version(DxfVersion::AC1032);
    let entity = document
        .add_entity(EntityType::Solid3D(Solid3D::new()))
        .unwrap();
    document
        .create_solid_history(
            entity,
            SolidHistoryOperation::Revolve(SolidHistoryRevolve {
                base: SolidHistoryNodeBase::new(1),
                raw_tail: tail.clone(),
                raw_tail_bit_len: REVOLVE_A_BITS,
                tail_decode: revolve_tail_view(&tail, REVOLVE_A_BITS),
                ..SolidHistoryRevolve::default()
            }),
        )
        .unwrap();
    let mut replacement = document.solid_history_operations(entity).unwrap()[0].clone();
    let SolidHistoryOperation::Revolve(revolve) = &mut replacement else {
        panic!("expected a revolve node");
    };
    revolve
        .tail_decode
        .get_or_insert_with(SolidHistoryRevolveTail::default)
        .profile_radius = Some(0.75);
    document.update_solid_history_step(entity, replacement).unwrap();

    let bytes = DwgWriter::write_to_vec(&document).unwrap();
    let roundtrip = DwgReader::from_stream(Cursor::new(bytes)).read().unwrap();
    let SolidHistoryOperation::Revolve(revolve) =
        &roundtrip.solid_history_operations(entity).unwrap()[0]
    else {
        panic!("expected a revolve node");
    };
    let view = revolve.tail_decode.as_ref().unwrap();
    assert_eq!(view.profile_radius, Some(0.75), "the radius edit re-reads");
    // Every grammar neighbor is untouched.
    assert_eq!(view.axis_point, Some([0.0, 0.0, 0.0]));
    assert_eq!(view.axis_vector, Some([0.0, 1.0, 0.0]));
    assert_eq!(view.revolve_angle, Some(std::f64::consts::PI));
    assert_eq!(view.profile_center, Some([2.0, 0.0, 0.0]));
    assert_eq!(view.profile_normal, Some([0.0, 0.0, 1.0]));
    assert_eq!(revolve.raw_tail.len(), tail.len());
    let differing: Vec<usize> = revolve
        .raw_tail
        .iter()
        .zip(tail.iter())
        .enumerate()
        .filter(|(_, (a, b))| a != b)
        .map(|(index, _)| index)
        .collect();
    assert!(!differing.is_empty());
    assert!(
        differing.iter().all(|index| (22..31).contains(index)),
        "radius edits must stay inside the radius span (bytes 22..=30), \
         got {differing:?}"
    );
}

#[test]
fn malformed_and_empty_tails_do_not_decode() {
    // No tail, truncated seed, or a head that never forms — all keep
    // the verbatim-only behavior (None view, no typed claims).
    assert!(sweep_tail_view(&[], 0).is_none());
    assert!(sweep_tail_view(&[0b10101010], 4).is_none());
    assert!(loft_tail_view(&[], 0).is_none());
    assert!(revolve_tail_view(&[], 0).is_none());
    // A reserved pair at the direction head cannot anchor a sweep view.
    assert!(sweep_tail_view(&[0b11000000], 8).is_none());
}

fn sweep_op(tail: &[u8], bit_len: u32) -> SolidHistoryOperation {
    SolidHistoryOperation::Sweep(SolidHistorySweep {
        base: SolidHistoryNodeBase::new(1),
        shsw_raw_tail: tail.to_vec(),
        shsw_raw_tail_bit_len: bit_len,
        ..SolidHistorySweep::default()
    })
}

#[test]
fn raw_tails_round_trip_verbatim_and_decoded() {
    // Full-stack: a DWG-written sweep op with the captured polysolid
    // tail re-reads bit-identically (Phase A rule) and re-derives the
    // Phase B typed view (semantic field parity throughout the stack).
    let tail = unhex(POLYSOLID_SWEEP_HEX);
    let mut document = CadDocument::with_version(DxfVersion::AC1032);
    let entity = document
        .add_entity(EntityType::Solid3D(Solid3D::new()))
        .unwrap();
    document
        .create_solid_history(entity, sweep_op(&tail, POLYSOLID_SWEEP_BITS))
        .unwrap();
    let bytes = DwgWriter::write_to_vec(&document).unwrap();
    let roundtrip = DwgReader::from_stream(Cursor::new(bytes)).read().unwrap();
    let ops = roundtrip.solid_history_operations(entity).unwrap();
    let SolidHistoryOperation::Sweep(sweep) = ops.first().expect("the sweep node survives") else {
        panic!("expected a sweep operation node");
    };
    assert_eq!(sweep.shsw_raw_tail, tail);
    assert_eq!(sweep.shsw_raw_tail_bit_len, POLYSOLID_SWEEP_BITS);
    let view = sweep.tail_decode.as_ref().expect("typed view re-decodes");
    assert_eq!(
        view.segment_end,
        Some([3065.007936309483, 1463.5113930448078])
    );
    assert_eq!(view.profile_corners.len(), 4);
    assert_eq!(view.raw_doubles.len(), 10);
    assert_eq!(view.option_doubles, vec![0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]);
}

#[test]
fn edited_segment_end_lands_bit_locally() {
    // Write rule: a programmatic edit of a decoded field re-encodes ONLY
    // its raw span — every other byte of the tail (and thus the record)
    // stays identical, so the re-encoded record keeps its size.
    let tail = unhex(POLYSOLID_SWEEP_HEX);
    let mut document = CadDocument::with_version(DxfVersion::AC1032);
    let entity = document
        .add_entity(EntityType::Solid3D(Solid3D::new()))
        .unwrap();
    document
        .create_solid_history(entity, sweep_op(&tail, POLYSOLID_SWEEP_BITS))
        .unwrap();

    let mut replacement = document.solid_history_operations(entity).unwrap()[0].clone();
    let SolidHistoryOperation::Sweep(sweep) = &mut replacement else {
        panic!("expected a sweep operation node");
    };
    let view = sweep.tail_decode.get_or_insert_with(SolidHistorySweepTail::default);
    view.segment_end = Some([1000.0, 2000.0]);
    document.update_solid_history_step(entity, replacement).unwrap();

    let bytes = DwgWriter::write_to_vec(&document).unwrap();
    let roundtrip = DwgReader::from_stream(Cursor::new(bytes)).read().unwrap();
    let SolidHistoryOperation::Sweep(sweep) =
        roundtrip.solid_history_operations(entity).unwrap()[0].clone()
    else {
        panic!("expected a sweep operation node");
    };
    assert_eq!(sweep.shsw_raw_tail.len(), tail.len());
    assert_eq!(sweep.shsw_raw_tail_bit_len, POLYSOLID_SWEEP_BITS);
    // The decoded edit is visible through the reader...
    assert_eq!(
        sweep.tail_decode.as_ref().unwrap().segment_end,
        Some([1000.0, 2000.0])
    );
    // ...and bit-locally: the changed bits lie inside the segment-end
    // span (the final 16 bytes of the tail), nothing else moves.
    let differing: Vec<usize> = sweep
        .shsw_raw_tail
        .iter()
        .zip(tail.iter())
        .enumerate()
        .filter(|(_, (a, b))| a != b)
        .map(|(index, _)| index)
        .collect();
    assert!(!differing.is_empty(), "the edit must land somewhere");
    assert!(
        differing.iter().all(|index| *index >= 201 && *index <= 216),
        "edits must stay inside the segment-end span, got {differing:?}"
    );
    // The other decoded anchors keep their values (splices are local).
    let view = sweep.tail_decode.as_ref().unwrap();
    assert_eq!(view.profile_corners.len(), 4);
    assert_eq!(view.raw_doubles.len(), 10);
}

#[test]
fn loft_and_revolve_tails_round_trip_and_edits_land() {
    // Same full-stack rule for the other two families: verbatim survival
    // plus local re-encode of the edited raw spans.
    let loft_tail = unhex(LOFT_HEX);
    let revolve_tail = unhex(REVOLVE_HEX);

    let mut document = CadDocument::with_version(DxfVersion::AC1032);
    let entity = document
        .add_entity(EntityType::Solid3D(Solid3D::new()))
        .unwrap();
    // A loft node and a revolve node on the same solid history chain.
    document
        .create_solid_history(
            entity,
            SolidHistoryOperation::Loft(SolidHistoryLoft {
                base: SolidHistoryNodeBase::new(1),
                raw_tail: loft_tail.clone(),
                raw_tail_bit_len: LOFT_BITS,
                tail_decode: loft_tail_view(&loft_tail, LOFT_BITS),
                ..SolidHistoryLoft::default()
            }),
        )
        .unwrap();
    document
        .append_solid_history(
            entity,
            SolidHistoryOperation::Revolve(SolidHistoryRevolve {
                base: SolidHistoryNodeBase::new(2),
                raw_tail: revolve_tail.clone(),
                raw_tail_bit_len: REVOLVE_BITS,
                tail_decode: revolve_tail_view(&revolve_tail, REVOLVE_BITS),
                ..SolidHistoryRevolve::default()
            }),
        )
        .unwrap();

    let bytes = DwgWriter::write_to_vec(&document).unwrap();
    let roundtrip = DwgReader::from_stream(Cursor::new(bytes)).read().unwrap();
    let ops = roundtrip.solid_history_operations(entity).unwrap();
    assert_eq!(ops.len(), 2);
    let SolidHistoryOperation::Loft(loft) = &ops[0] else {
        panic!("expected a loft node");
    };
    let SolidHistoryOperation::Revolve(revolve) = &ops[1] else {
        panic!("expected a revolve node");
    };
    assert_eq!(loft.raw_tail, loft_tail);
    assert_eq!(revolve.raw_tail, revolve_tail);
    assert_eq!(
        loft.tail_decode.as_ref().unwrap().raw_doubles,
        vec![2.0, 2.0, 5.0, 0.3, std::f64::consts::FRAC_PI_2, std::f64::consts::FRAC_PI_2]
    );
    assert_eq!(
        revolve.tail_decode.as_ref().unwrap().revolve_angle,
        Some(3.0 * std::f64::consts::FRAC_PI_2)
    );

    // Edit the revolve sweep angle: the splice must only touch the 8
    // bytes of its raw span (bits [14..78) -> bytes [1..10) of the tail).
    let mut replacement = ops[1].clone();
    let SolidHistoryOperation::Revolve(revolve) = &mut replacement else {
        panic!("expected a revolve node");
    };
    let view = revolve
        .tail_decode
        .get_or_insert_with(SolidHistoryRevolveTail::default);
    view.revolve_angle = Some(std::f64::consts::PI);
    document.update_solid_history_step(entity, replacement).unwrap();
    let bytes = DwgWriter::write_to_vec(&document).unwrap();
    let roundtrip = DwgReader::from_stream(Cursor::new(bytes)).read().unwrap();
    let SolidHistoryOperation::Revolve(revolve) =
        &roundtrip.solid_history_operations(entity).unwrap()[1]
    else {
        panic!("expected a revolve node");
    };
    assert_eq!(revolve.raw_tail.len(), revolve_tail.len());
    assert_eq!(
        revolve.tail_decode.as_ref().unwrap().revolve_angle,
        Some(std::f64::consts::PI)
    );
    let differing: Vec<usize> = revolve
        .raw_tail
        .iter()
        .zip(revolve_tail.iter())
        .enumerate()
        .filter(|(_, (a, b))| a != b)
        .map(|(index, _)| index)
        .collect();
    assert!(!differing.is_empty());
    assert!(
        differing.iter().all(|index| (1..10).contains(index)),
        "revolve-angle edits must stay inside the angle span, got {differing:?}"
    );

    // Edit a loft raw entry (the 5.0 top height): splice lands inside
    // its 8-byte raw span only.
    let mut replacement = roundtrip.solid_history_operations(entity).unwrap()[0].clone();
    let SolidHistoryOperation::Loft(loft) = &mut replacement else {
        panic!("expected a loft node");
    };
    let view = loft
        .tail_decode
        .get_or_insert_with(SolidHistoryLoftTail::default);
    view.raw_doubles = loft_tail_view(&loft_tail, LOFT_BITS)
        .unwrap()
        .raw_doubles;
    view.raw_doubles[2] = 6.0;
    document.update_solid_history_step(entity, replacement).unwrap();
    let bytes = DwgWriter::write_to_vec(&document).unwrap();
    let roundtrip = DwgReader::from_stream(Cursor::new(bytes)).read().unwrap();
    let SolidHistoryOperation::Loft(loft) =
        &roundtrip.solid_history_operations(entity).unwrap()[0]
    else {
        panic!("expected a loft node");
    };
    assert_eq!(loft.raw_tail.len(), loft_tail.len());
    assert_eq!(loft.tail_decode.as_ref().unwrap().raw_doubles[2], 6.0);
    let differing: Vec<usize> = loft
        .raw_tail
        .iter()
        .zip(loft_tail.iter())
        .enumerate()
        .filter(|(_, (a, b))| a != b)
        .map(|(index, _)| index)
        .collect();
    assert!(!differing.is_empty());
    // The 5.0 entry's raw span: value bits [204..268) -> bytes [25..34].
    assert!(
        differing.iter().all(|index| (25..34).contains(index)),
        "loft edits must stay inside the 5.0 entry span, got {differing:?}"
    );
}

#[test]
fn undecodable_tails_stay_verbatim_never_modeled() {
    // Review regression: a captured tail whose layout does NOT decode
    // (the reserved pair heads this sample) must keep the Phase A
    // behavior — verbatim re-emission — and NEVER fall through to the
    // modeled fallback, which would replace the captured bits with the
    // guess sequence and corrupt the record.
    let opaque: Vec<u8> = vec![0b1100_0000, 0b0101_1010, 0x33, 0x55, 0x11, 0x7F];
    let opaque_bits: u32 = 48;
    assert!(sweep_tail_view(&opaque, opaque_bits).is_none());

    let mut document = CadDocument::with_version(DxfVersion::AC1032);
    let entity = document
        .add_entity(EntityType::Solid3D(Solid3D::new()))
        .unwrap();
    document
        .create_solid_history(
            entity,
            SolidHistoryOperation::Sweep(SolidHistorySweep {
                base: SolidHistoryNodeBase::new(1),
                shsw_raw_tail: opaque.clone(),
                shsw_raw_tail_bit_len: opaque_bits,
                ..SolidHistorySweep::default()
            }),
        )
        .unwrap();
    let bytes = DwgWriter::write_to_vec(&document).unwrap();
    let roundtrip = DwgReader::from_stream(Cursor::new(bytes)).read().unwrap();
    let SolidHistoryOperation::Sweep(sweep) =
        &roundtrip.solid_history_operations(entity).unwrap()[0]
    else {
        panic!("expected a sweep operation node");
    };
    assert_eq!(sweep.shsw_raw_tail, opaque, "the captured bits survive verbatim");
    assert_eq!(sweep.shsw_raw_tail_bit_len, opaque_bits);
    assert!(sweep.tail_decode.is_none(), "no typed view is claimed");
}

