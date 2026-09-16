//! Regression test for AcDbVisualStyle pre-R2010 DWG serialization.
//!
//! The legacy (pre-R2010) VisualStyle writer consumes a 24-element property
//! vector in a fixed order.  This test builds a VisualStyle with exactly that
//! legacy property bag, round-trips it through a R2000 DWG write/read, and
//! asserts the recovered properties match the input values and types.

use std::io::Cursor;

use acadrust::objects::{
    ObjectType, VisualStyle, VisualStyleProperty, VisualStylePropertyValue,
};
use acadrust::types::{Color, DxfVersion};
use acadrust::{CadDocument, DwgReader, DwgWriter};

#[test]
fn visualstyle_survives_dwg_roundtrip_r2000() {
    let mut doc = CadDocument::with_version(DxfVersion::AC1015);

    let mut style = VisualStyle::new();
    style.handle = doc.allocate_handle();
    let style_handle = style.handle;
    style.owner = doc.header.named_objects_dict_handle;
    style.description = "TestStyle".to_string();
    style.style_type = 1;
    style.face_lighting_model = 2;
    style.face_lighting_quality = 1;
    style.face_color_mode = 3;
    style.face_modifier = 5;
    style.edge_model = 1;
    style.edge_style = 2;
    style.internal_use_only = true;

    // Pre-R2010 property order, matching the writer in
    // dwg_stream_writers/object_writer/objects.rs::write_visual_style.
    style.properties = vec![
        VisualStyleProperty { value: VisualStylePropertyValue::Double(0.75), enabled: 1 }, // 0 face_opacity
        VisualStyleProperty { value: VisualStylePropertyValue::Double(45.0), enabled: 1 }, // 1 face_specular
        VisualStyleProperty { value: VisualStylePropertyValue::Color(Color::Index(5)), enabled: 1 }, // 2 face_mono_color
        VisualStyleProperty { value: VisualStylePropertyValue::Color(Color::Index(6)), enabled: 1 }, // 3 edge_intersection_color
        VisualStyleProperty { value: VisualStylePropertyValue::Color(Color::Index(7)), enabled: 1 }, // 4 edge_obscured_color
        VisualStyleProperty { value: VisualStylePropertyValue::Long(2), enabled: 1 }, // 5 edge_obscured_ltype
        VisualStyleProperty { value: VisualStylePropertyValue::Double(0.5), enabled: 1 }, // 6 edge_crease_angle
        VisualStyleProperty { value: VisualStylePropertyValue::Long(1), enabled: 1 }, // 7 edge_modifier
        VisualStyleProperty { value: VisualStylePropertyValue::Color(Color::Index(8)), enabled: 1 }, // 8 edge_color
        VisualStyleProperty { value: VisualStylePropertyValue::Double(0.9), enabled: 1 }, // 9 edge_opacity
        VisualStyleProperty { value: VisualStylePropertyValue::Short(4), enabled: 1 }, // 10 edge_width
        VisualStyleProperty { value: VisualStylePropertyValue::Short(12), enabled: 1 }, // 11 edge_overhang
        VisualStyleProperty { value: VisualStylePropertyValue::Long(7), enabled: 1 }, // 12 edge_jitter
        VisualStyleProperty { value: VisualStylePropertyValue::Color(Color::Index(9)), enabled: 1 }, // 13 edge_silhouette_color
        VisualStyleProperty { value: VisualStylePropertyValue::Short(8), enabled: 1 }, // 14 edge_silhouette_width
        VisualStyleProperty { value: VisualStylePropertyValue::Long(1), enabled: 1 }, // 15 edge_halo_gap (written as byte, read as long)
        VisualStyleProperty { value: VisualStylePropertyValue::Short(24), enabled: 1 }, // 16 edge_isolines
        VisualStyleProperty { value: VisualStylePropertyValue::Bool(true), enabled: 1 }, // 17 edge_do_hide_precision
        VisualStyleProperty { value: VisualStylePropertyValue::Short(1), enabled: 1 }, // 18 edge_style_apply
        VisualStyleProperty { value: VisualStylePropertyValue::Short(2), enabled: 1 }, // 19 display_settings
        VisualStyleProperty { value: VisualStylePropertyValue::Long(25), enabled: 1 }, // 20 display_brightness (written/read as BLd)
        VisualStyleProperty { value: VisualStylePropertyValue::Long(1), enabled: 1 }, // 21 display_shadow_type
        VisualStyleProperty { value: VisualStylePropertyValue::Long(0), enabled: 1 }, // 22 reserved long
        VisualStyleProperty { value: VisualStylePropertyValue::Double(0.0), enabled: 1 }, // 23 bd2007_45
    ];

    doc.objects
        .insert(style.handle, ObjectType::VisualStyle(style));

    let bytes = DwgWriter::write_to_vec(&doc).expect("DWG write failed");
    let mut reader = DwgReader::from_stream(Cursor::new(bytes));
    let rt_doc = reader.read().expect("DWG read failed");

    let ObjectType::VisualStyle(rt) = rt_doc.objects.get(&style_handle).expect("VisualStyle missing") else {
        panic!("round-tripped object is not a VisualStyle");
    };

    assert_eq!(rt.description, "TestStyle");
    assert_eq!(rt.style_type, 1);
    assert_eq!(rt.face_lighting_model, 2);
    assert_eq!(rt.face_lighting_quality, 1);
    assert_eq!(rt.face_color_mode, 3);
    assert_eq!(rt.face_modifier, 5);
    assert_eq!(rt.edge_model, 1);
    assert_eq!(rt.edge_style, 2);
    assert!(rt.internal_use_only);

    // After a pre-R2010 round-trip the model stores the 24 legacy properties.
    assert_eq!(rt.properties.len(), 24, "expected 24 legacy properties");

    // The reader stores each field with the type it reads.  Values that are
    // written as wider/narrower integer types are still stored as the reader's
    // native type (Short, Long, Double, Bool, Color).
    let expected: Vec<VisualStylePropertyValue> = vec![
        VisualStylePropertyValue::Double(0.75),
        VisualStylePropertyValue::Double(45.0),
        VisualStylePropertyValue::Color(Color::Index(5)),
        VisualStylePropertyValue::Color(Color::Index(6)),
        VisualStylePropertyValue::Color(Color::Index(7)),
        VisualStylePropertyValue::Long(2),
        VisualStylePropertyValue::Double(0.5),
        VisualStylePropertyValue::Long(1),
        VisualStylePropertyValue::Color(Color::Index(8)),
        VisualStylePropertyValue::Double(0.9),
        VisualStylePropertyValue::Short(4),
        VisualStylePropertyValue::Short(12),
        VisualStylePropertyValue::Long(7),
        VisualStylePropertyValue::Color(Color::Index(9)),
        VisualStylePropertyValue::Short(8),
        VisualStylePropertyValue::Long(1),
        VisualStylePropertyValue::Short(24),
        VisualStylePropertyValue::Bool(true),
        VisualStylePropertyValue::Short(1),
        VisualStylePropertyValue::Short(2),
        VisualStylePropertyValue::Long(25),
        VisualStylePropertyValue::Long(1),
        VisualStylePropertyValue::Long(0),
        VisualStylePropertyValue::Double(0.0),
    ];

    for (i, (actual, exp)) in rt.properties.iter().zip(expected.iter()).enumerate() {
        assert_eq!(
            &actual.value, exp,
            "property {i} mismatch: got {:?}, expected {:?}",
            actual.value, exp
        );
    }
}
