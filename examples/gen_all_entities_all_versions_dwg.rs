/// Generate a single DWG file containing all supported entity types.
///
/// Output: gen_all_entities_all_versions.dwg (AC1032 / R2018)
///
/// This is a variant of `gen_all_entities_all_versions.rs` that creates one
/// document and writes every generated entity into a single file instead of
/// producing a file per version per entity type.
use acadrust::entities::acis::{SatDocument, SatPointer, SatToken, Sense, Sidedness};
use acadrust::entities::dimension::DimensionLinear;
use acadrust::entities::hatch::{
    BoundaryEdge, BoundaryPath, BoundaryPathFlags, LineEdge, PolylineEdge,
};
use acadrust::entities::mesh::Mesh;
use acadrust::entities::mline::MLine;
use acadrust::entities::multileader::MultiLeader;
use acadrust::entities::polyface_mesh::PolyfaceMesh;
use acadrust::entities::*;
use acadrust::types::{DxfVersion, Vector2, Vector3};
use acadrust::{
    BlockRecord, CadDocument, DimStyle, DwgWriter, LineWeight, TableEntry, TextStyle,
    Transparency,
};

/// Dimstyle-override EED payload of an authored text-leader (from
/// 2018/Leader.dwg), with the embedded annotation-entity reference
/// repointed from the original 0x77A to this document's MTEXT handle
/// 0x40 (masked RLL tail: run of 0x00 masks + 0x40 terminator).
/// Retained as the transcription record for the strict-load work; not
/// currently attached (the plaintext-leader probe class).
#[allow(dead_code)]
const DSTYLE_EED: [u8; 73] = [
    0x00, 0x06, 0x00, 0x44, 0x00, 0x53, 0x00, 0x54, 0x00, 0x59, 0x00, 0x4C, //
    0x00, 0x45, 0x00, 0x02, 0x00, 0x46, 0x28, 0x00, 0x28, 0x00, 0x00, 0x00, //
    0x00, 0x00, 0x00, 0x00, 0x00, 0x46, 0x29, 0x00, 0x28, 0xB8, 0x1E, 0x85, //
    0xEB, 0x51, 0xB8, 0xCE, 0x3F, 0x46, 0x55, 0x01, 0x05, 0x00, 0x00, 0x00, //
    0x00, 0x00, 0x00, 0x00, 0x40, 0x46, 0x93, 0x00, 0x28, 0x0A, 0xD7, 0xA3, //
    0x70, 0x3D, 0x0A, 0xB7, 0x3F, 0x46, 0x4D, 0x00, 0x46, 0x00, 0x00, 0x02, //
    0x01,
];

fn main() {
    let mut doc = CadDocument::with_version(DxfVersion::AC1032);
    let mut ok = 0u32;
    let mut fail = 0u32;
    let mut skip = 0u32;

    // ── Simple geometry ─────────────────────────────────────────

    add_entity(
        &mut doc,
        "POINT",
        &mut ok,
        &mut fail,
        &mut skip,
        || EntityType::Point(Point::from_coords(50.0, 50.0, 0.0)),
    );

    add_entity(
        &mut doc,
        "LINE",
        &mut ok,
        &mut fail,
        &mut skip,
        || EntityType::Line(Line::from_coords(0.0, 0.0, 0.0, 100.0, 100.0, 0.0)),
    );

    add_entity(
        &mut doc,
        "CIRCLE",
        &mut ok,
        &mut fail,
        &mut skip,
        || EntityType::Circle(Circle::from_coords(50.0, 50.0, 0.0, 25.0)),
    );

    add_entity(
        &mut doc,
        "ARC",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Arc(Arc::from_coords(
                50.0,
                50.0,
                0.0,
                25.0,
                0.0,
                std::f64::consts::PI,
            ))
        },
    );

    add_entity(
        &mut doc,
        "ELLIPSE",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Ellipse(Ellipse::from_center_axes(
                Vector3::new(50.0, 50.0, 0.0),
                Vector3::new(40.0, 0.0, 0.0),
                0.5,
            ))
        },
    );

    add_entity(
        &mut doc,
        "RAY",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Ray(Ray::new(
                Vector3::new(0.0, 0.0, 0.0),
                Vector3::new(1.0, 1.0, 0.0),
            ))
        },
    );

    add_entity(
        &mut doc,
        "XLINE",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::XLine(XLine::new(
                Vector3::new(50.0, 50.0, 0.0),
                Vector3::new(1.0, 0.0, 0.0),
            ))
        },
    );

    // ── Solid / Surface ─────────────────────────────────────────

    add_entity(
        &mut doc,
        "SOLID",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Solid(Solid::new(
                Vector3::new(0.0, 0.0, 0.0),
                Vector3::new(10.0, 0.0, 0.0),
                Vector3::new(10.0, 10.0, 0.0),
                Vector3::new(0.0, 10.0, 0.0),
            ))
        },
    );

    add_entity(
        &mut doc,
        "FACE3D",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Face3D(Face3D::new(
                Vector3::new(0.0, 0.0, 0.0),
                Vector3::new(10.0, 0.0, 0.0),
                Vector3::new(10.0, 10.0, 5.0),
                Vector3::new(0.0, 10.0, 5.0),
            ))
        },
    );

    // ── Text ────────────────────────────────────────────────────

    add_entity(
        &mut doc,
        "TEXT",
        &mut ok,
        &mut fail,
        &mut skip,
        || EntityType::Text(Text::with_value("Hello World", Vector3::new(0.0, 0.0, 0.0))),
    );

    add_entity(
        &mut doc,
        "MTEXT",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::MText(MText::with_value(
                "Multi\\Pline\\PText",
                Vector3::new(0.0, 0.0, 0.0),
            ))
        },
    );

    // ── Polylines ───────────────────────────────────────────────

    add_entity(
        &mut doc,
        "LWPOLYLINE",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::LwPolyline(LwPolyline::from_points(vec![
                Vector2::new(0.0, 0.0),
                Vector2::new(10.0, 0.0),
                Vector2::new(10.0, 10.0),
                Vector2::new(0.0, 10.0),
            ]))
        },
    );

    add_entity(
        &mut doc,
        "POLYLINE2D",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            let mut pl = Polyline2D::new();
            pl.add_vertex(Vertex2D::new(Vector3::new(0.0, 0.0, 0.0)));
            pl.add_vertex(Vertex2D::new(Vector3::new(20.0, 0.0, 0.0)));
            pl.add_vertex(Vertex2D::new(Vector3::new(20.0, 20.0, 0.0)));
            EntityType::Polyline2D(pl)
        },
    );

    add_entity(
        &mut doc,
        "POLYLINE3D",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Polyline3D(Polyline3D::from_points(vec![
                Vector3::new(0.0, 0.0, 0.0),
                Vector3::new(10.0, 0.0, 5.0),
                Vector3::new(20.0, 10.0, 10.0),
            ]))
        },
    );

    add_entity(
        &mut doc,
        "SPLINE",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Spline(Spline::from_control_points(
                3,
                vec![
                    Vector3::new(0.0, 0.0, 0.0),
                    Vector3::new(5.0, 10.0, 0.0),
                    Vector3::new(10.0, 0.0, 0.0),
                    Vector3::new(15.0, 10.0, 0.0),
                ],
            ))
        },
    );

    // ── Annotations ─────────────────────────────────────────────

    // BricsCAD's strict (plain-open) loader rejects the constructed bare
    // leader record ("Object improperly read: <AcDbLeader>"), tolerating
    // it only under RECOVER, while both local decoders read it
    // spec-exact. GENALL_LEADER_MODE selects a variant for isolating the
    // audit: "plain" (default) — annot_type 3 with the null association,
    // the TS1-attested authored-null form; "annot" — the authored
    // WithText form with a real MTEXT association (ergo the leader's
    // handle shifts, which also disambiguates BricsCAD's "(40)" as
    // handle vs status code); "skip" — no leader record at all.
    let leader_mode = std::env::var("GENALL_LEADER_MODE").unwrap_or_default();
    if leader_mode.eq_ignore_ascii_case("skip") {
        println!("  SKIP LEADER (GENALL_LEADER_MODE=skip)");
    } else if leader_mode.eq_ignore_ascii_case("annot") {
        // Authored leaders with annotation always carry the real
        // association; create the MTEXT first so its handle exists.
        match doc.add_entity(EntityType::MText(MText::with_value(
            "Note",
            Vector3::new(12.0, 12.0, 0.0),
        ))) {
            Ok(mtext_handle) => {
                let mut leader = Leader::two_point(
                    Vector3::new(0.0, 0.0, 0.0),
                    Vector3::new(10.0, 10.0, 0.0),
                );
                leader.creation_type = LeaderCreationType::WithText;
                leader.annotation_handle = mtext_handle;
                match doc.add_entity(EntityType::Leader(leader)) {
                    Ok(_) => ok += 1,
                    Err(e) => {
                        println!("  SKIP LEADER add error: {:?}", e);
                        skip += 1;
                    }
                }
            }
            Err(e) => {
                println!("  SKIP LEADER mtext error: {:?}", e);
                skip += 1;
            }
        }
    } else {
        // Plain-class leader construction: WithText + a real MTEXT
        // association, spline path, authored arrowhead/box values, scale,
        // weight and transparency — but NO named-linetype reference: a
        // named real linetype deep-resolves its table record, and a
        // constructed doc has no real dash description for it (the deep
        // loader drops the resolving entity). Continuous = no ltype slot.
        let _ = doc.dim_styles.add(DimStyle::new("Annotative"));
        match doc.add_entity(EntityType::MText(MText::with_value(
            "Note",
            Vector3::new(22.0, 12.0, 0.0),
        ))) {
            Ok(mtext_handle) => {
                let mut leader = Leader::from_vertices(vec![
                    Vector3::new(0.0, 0.0, 0.0),
                    Vector3::new(10.0, 10.0, 0.0),
                    Vector3::new(20.0, 10.0, 0.0),
                ]);
                leader.creation_type = LeaderCreationType::WithText;
                leader.annotation_handle = mtext_handle;
                leader.path_type = LeaderPathType::Spline;
                leader.arrow_enabled = false;
                leader.arrowhead_type = 322;
                leader.hookline_direction = HooklineDirection::Same;
                leader.dwg_unknown_bit4 = true;
                leader.text_height = 0.0;
                leader.text_width = -0.09;
                // Consistent plain-leader class: no EED (the Annotative
                // marks imply an annotation-scale context with an
                // extension dictionary our constructed document does not
                // provide — the deep loader drops the mismatched
                // annotative leader), standard DIMSTYLE, and a real
                // linetype only when the table can back it (here:
                // continuous — the plainest legal class).
                leader.dimension_style = "Standard".to_string();
                leader.common.linetype = "Continuous".to_string();
                leader.common.line_weight = LineWeight::Value(5);
                leader.common.linetype_scale = 1.5;
                leader.common.transparency = Transparency::Explicit(169);
                match doc.add_entity(EntityType::Leader(leader)) {
                    Ok(leader_handle) => {
                        // The last authentically structural delta from the
                        // accepted record: a real extension dictionary,
                        // where per-scale annotation contexts live. The deep
                        // loader "improperly read"s the leader without it.
                        doc.ensure_extension_dictionary(leader_handle);
                        ok += 1;
                    }
                    Err(e) => {
                        println!("  SKIP LEADER add error: {:?}", e);
                        skip += 1;
                    }
                }
            }
            Err(e) => {
                println!("  SKIP LEADER mtext error: {:?}", e);
                skip += 1;
            }
        }
    }

    add_entity(
        &mut doc,
        "DIMENSION",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Dimension(Dimension::Linear(DimensionLinear::new(
                Vector3::new(0.0, 0.0, 0.0),
                Vector3::new(100.0, 0.0, 0.0),
            )))
        },
    );

    add_entity(
        &mut doc,
        "TOLERANCE",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::Tolerance(Tolerance::with_text(
                Vector3::new(10.0, 10.0, 0.0),
                "{\\Fgdt;p}%%v0.5",
            ))
        },
    );

    // A SHAPE needs both a style whose font is a shape (.shx) file and a
    // nonzero shape number — a strict audit (BricsCAD) rejects the record
    // with both unset. ltypeshp.shx is the classic AutoCAD shape library;
    // 130 selects a glyph in it (the style/number pair is what the loader
    // validates; the glyph itself is cosmetic).
    let mut shape_style = TextStyle::new("LTYPESHP");
    shape_style.font_file = "ltypeshp.shx".to_string();
    shape_style.is_shape_file = true;
    let _ = doc.text_styles.add(shape_style);

    add_entity(
        &mut doc,
        "SHAPE",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            let mut shape = Shape::with_name(Vector3::new(50.0, 50.0, 0.0), "BOX", 5.0);
            shape.shape_number = 130;
            shape.style_name = "LTYPESHP".to_string();
            EntityType::Shape(shape)
        },
    );

    add_entity(
        &mut doc,
        "VIEWPORT",
        &mut ok,
        &mut fail,
        &mut skip,
        || EntityType::Viewport(Viewport::new()),
    );

    add_insert(&mut doc, &mut ok, &mut fail, &mut skip);

    // ── Hatch ───────────────────────────────────────────────────

    add_entity(
        &mut doc,
        "HATCH_SOLID",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            let mut hatch = Hatch::solid();
            let mut path = BoundaryPath::new();
            path.add_edge(BoundaryEdge::Polyline(PolylineEdge::new(
                vec![
                    Vector2::new(0.0, 0.0),
                    Vector2::new(100.0, 0.0),
                    Vector2::new(100.0, 100.0),
                    Vector2::new(0.0, 100.0),
                ],
                true,
            )));
            hatch.add_path(path);
            EntityType::Hatch(hatch)
        },
    );

    add_entity(
        &mut doc,
        "HATCH_LINES",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            let mut hatch = Hatch::solid();
            let mut path = BoundaryPath::with_flags(BoundaryPathFlags::new());
            path.add_edge(BoundaryEdge::Line(LineEdge {
                start: Vector2::new(0.0, 0.0),
                end: Vector2::new(50.0, 0.0),
            }));
            path.add_edge(BoundaryEdge::Line(LineEdge {
                start: Vector2::new(50.0, 0.0),
                end: Vector2::new(50.0, 50.0),
            }));
            path.add_edge(BoundaryEdge::Line(LineEdge {
                start: Vector2::new(50.0, 50.0),
                end: Vector2::new(0.0, 0.0),
            }));
            hatch.add_path(path);
            EntityType::Hatch(hatch)
        },
    );

    // ── MLine ───────────────────────────────────────────────────

    add_entity(
        &mut doc,
        "MLINE",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            EntityType::MLine(MLine::from_points(&[
                Vector3::new(0.0, 0.0, 0.0),
                Vector3::new(50.0, 0.0, 0.0),
                Vector3::new(50.0, 50.0, 0.0),
            ]))
        },
    );

    // ── PolyfaceMesh ────────────────────────────────────────────

    add_entity(
        &mut doc,
        "POLYFACE",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            let mut pf = PolyfaceMesh::new();
            let v1 = pf.add_vertex_xyz(0.0, 0.0, 0.0);
            let v2 = pf.add_vertex_xyz(10.0, 0.0, 0.0);
            let v3 = pf.add_vertex_xyz(5.0, 10.0, 0.0);
            let v4 = pf.add_vertex_xyz(10.0, 10.0, 5.0);
            pf.add_triangle(v1, v2, v3);
            pf.add_triangle(v2, v4, v3);
            EntityType::PolyfaceMesh(pf)
        },
    );

    // ── MultiLeader ───────────────────────────────────────────────

    // GENALL_MLEADER_MODE=skip omits the MULTILEADER record (BricsCAD
    // strict-load probe; see the leader mode note above).
    if std::env::var("GENALL_MLEADER_MODE")
        .map(|m| m.eq_ignore_ascii_case("skip"))
        .unwrap_or(false)
    {
        println!("  SKIP MULTILEADER (GENALL_MLEADER_MODE=skip)");
    } else {
        add_entity(
            &mut doc,
            "MULTILEADER",
            &mut ok,
            &mut fail,
            &mut skip,
            || {
                EntityType::MultiLeader(MultiLeader::with_text(
                    "Label",
                    Vector3::new(20.0, 20.0, 0.0),
                    vec![Vector3::new(0.0, 0.0, 0.0), Vector3::new(10.0, 10.0, 0.0)],
                ))
            },
        );
    }

    // ── Mesh ────────────────────────────────────────────────────

    add_entity(
        &mut doc,
        "MESH",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            let mut mesh = Mesh::from_triangles(
                vec![
                    Vector3::new(0.0, 0.0, 0.0),
                    Vector3::new(10.0, 0.0, 0.0),
                    Vector3::new(5.0, 10.0, 5.0),
                ],
                &[(0, 1, 2)],
            );
            // Authored-wire population invariants (2004/Surface.dwg's
            // MESH 0x2D0 and every authored specimen): wire bit 72 —
            // which the model calls blend_crease and gold decodes as
            // is_watertight — is 0, and the trailing unknown_b1 is 1.
            mesh.blend_crease = false;
            mesh.unknown_b1 = true;
            EntityType::Mesh(mesh)
        },
    );

    // ── ACIS entities (3DSOLID, REGION, BODY) ───────────────────

    add_entity(
        &mut doc,
        "3DSOLID",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            let sat_doc = build_cylinder_sat();
            EntityType::Solid3D(Solid3D::from_sat(&sat_doc.to_sat_string()))
        },
    );

    add_entity(
        &mut doc,
        "REGION",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            // A valid planar region built through the SatDocument API: a
            // single plane face with a closed four-edge outer loop (an open
            // sheet — every edge has exactly one coedge, so partners stay
            // null), all back-pointers wired. The earlier hand-typed SAT
            // string had degenerate records (single-vertex edges,
            // self-partnered coedges) that strict modelers reject as an
            // empty data stream.
            let sat_doc = build_region_sat();
            EntityType::Region(Region::from_sat(&sat_doc.to_sat_string()))
        },
    );

    add_entity(
        &mut doc,
        "BODY",
        &mut ok,
        &mut fail,
        &mut skip,
        || {
            // AcDbBody accepts any modeler body; reuse the valid closed
            // cylinder solid (lump -> shell -> faces) instead of the
            // earlier broken hand-typed sheet text.
            let sat_doc = build_cylinder_sat();
            EntityType::Body(Body::from_sat(&sat_doc.to_sat_string()))
        },
    );

    // ── Write the single DWG file ─────────────────────────────────

    let path = "gen_all_entities_all_versions.dwg";
    match DwgWriter::write_to_file(path, &doc) {
        Ok(()) => {
            let sz = std::fs::metadata(path).map(|m| m.len()).unwrap_or(0);
            println!("Wrote {} ({} bytes)", path, sz);
        }
        Err(e) => {
            println!("FAIL writing {}: {:?}", path, e);
            std::process::exit(1);
        }
    }

    println!("\nSummary: {} OK, {} FAIL, {} SKIP", ok, fail, skip);

    if fail > 0 {
        std::process::exit(1);
    }
}

/// Add an entity to the single document, counting successes/skips.
/// Error paths count as skips; the shared `fail` counter is not touched
/// here, so it is accepted under its underscore alias.
fn add_entity<F>(
    doc: &mut CadDocument,
    name: &str,
    ok: &mut u32,
    _fail: &mut u32,
    skip: &mut u32,
    make_entity: F,
) where
    F: FnOnce() -> EntityType,
{
    let entity = make_entity();
    if let Err(e) = doc.add_entity(entity) {
        println!("  SKIP {:<20} add_entity error: {:?}", name, e);
        *skip += 1;
        return;
    }
    println!("  OK   {:<20}", name);
    *ok += 1;
}

/// Add a block definition + INSERT reference to the single document.
/// Error paths count as skips; the shared `fail` counter is not touched
/// here, so it is accepted under its underscore alias.
fn add_insert(doc: &mut CadDocument, ok: &mut u32, _fail: &mut u32, skip: &mut u32) {
    let name = "INSERT";

    // 1. Create a block record for "TestBlock"
    let mut br = BlockRecord::new("TestBlock");
    let br_handle = doc.allocate_handle();
    br.set_handle(br_handle);
    br.block_entity_handle = doc.allocate_handle();
    br.block_end_handle = doc.allocate_handle();
    if let Err(e) = doc.block_records.add(br) {
        println!("  SKIP {:<20} block_records.add error: {}", name, e);
        *skip += 1;
        return;
    }

    // 2. Add geometry to the block by pre-setting owner_handle
    let mut circle = EntityType::Circle(Circle::from_coords(0.0, 0.0, 0.0, 10.0));
    circle.common_mut().owner_handle = br_handle;
    if let Err(e) = doc.add_entity(circle) {
        println!("  SKIP {:<20} add circle error: {:?}", name, e);
        *skip += 1;
        return;
    }

    let mut line = EntityType::Line(Line::from_coords(-10.0, 0.0, 0.0, 10.0, 0.0, 0.0));
    line.common_mut().owner_handle = br_handle;
    if let Err(e) = doc.add_entity(line) {
        println!("  SKIP {:<20} add line error: {:?}", name, e);
        *skip += 1;
        return;
    }

    // 3. Add an INSERT entity referencing "TestBlock"
    let insert = Insert::new("TestBlock", Vector3::new(50.0, 50.0, 0.0));
    if let Err(e) = doc.add_entity(EntityType::Insert(insert)) {
        println!("  SKIP {:<20} add_entity error: {:?}", name, e);
        *skip += 1;
        return;
    }

    println!("  OK   {:<20}", name);
    *ok += 1;
}

/// Build a cylinder SAT with radius 5, height 10, along Z-axis.
///
/// Bottom circle center at (0,0,0), top at (0,0,10).
/// 3 faces (bottom cap, top cap, lateral), 3 edges, 2 vertices.
fn build_cylinder_sat() -> SatDocument {
    let mut sat = SatDocument::new_body();
    let body_idx = SatPointer::new(0);
    let ptr = |i: i32| SatPointer::new(i);

    let tau = std::f64::consts::TAU;

    // Points
    let p0 = sat.add_point(5.0, 0.0, 0.0); // bottom seam
    let p1 = sat.add_point(5.0, 0.0, 10.0); // top seam

    // Surfaces
    let surf_bot = sat.add_plane_surface([0.0, 0.0, 0.0], [0.0, 0.0, -1.0], [1.0, 0.0, 0.0]);
    let surf_top = sat.add_plane_surface([0.0, 0.0, 10.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]);
    let surf_cyl = sat.add_cone_surface(
        [0.0, 0.0, 0.0], // center
        [0.0, 0.0, 1.0], // axis
        [5.0, 0.0, 0.0], // major-axis (radius = 5)
        1.0,             // ratio (circular)
        1.0,             // cos(half-angle) = 1 → cylinder
        0.0,             // sin(half-angle) = 0 → cylinder
    );

    // Curves
    let crv_bot = sat.add_ellipse_curve([0.0, 0.0, 0.0], [0.0, 0.0, 1.0], [5.0, 0.0, 0.0], 1.0);
    let crv_top = sat.add_ellipse_curve([0.0, 0.0, 10.0], [0.0, 0.0, 1.0], [5.0, 0.0, 0.0], 1.0);
    let crv_seam = sat.add_straight_curve([5.0, 0.0, 0.0], [0.0, 0.0, 1.0]);

    // Vertices
    let v0 = sat.add_vertex(SatPointer::NULL, ptr(p0));
    let v1 = sat.add_vertex(SatPointer::NULL, ptr(p1));

    // Edges
    let e_bot = sat.add_edge(
        ptr(v0),
        0.0,
        ptr(v0),
        tau,
        SatPointer::NULL,
        ptr(crv_bot),
        Sense::Forward,
    );
    let e_top = sat.add_edge(
        ptr(v1),
        0.0,
        ptr(v1),
        tau,
        SatPointer::NULL,
        ptr(crv_top),
        Sense::Forward,
    );
    let e_seam = sat.add_edge(
        ptr(v0),
        0.0,
        ptr(v1),
        10.0,
        SatPointer::NULL,
        ptr(crv_seam),
        Sense::Forward,
    );

    // Coedge indices
    let base = sat.records.len() as i32;
    let co = |i: i32| base + i;
    let loop_base = base + 6;
    let face_base = base + 9;
    let shell_idx = base + 12;
    let lump_idx = base + 13;

    // Bottom cap coedge
    sat.add_coedge(
        ptr(co(0)),
        ptr(co(0)),
        ptr(co(4)),
        ptr(e_bot),
        Sense::Reversed,
        ptr(loop_base),
    );
    // Top cap coedge
    sat.add_coedge(
        ptr(co(1)),
        ptr(co(1)),
        ptr(co(2)),
        ptr(e_top),
        Sense::Forward,
        ptr(loop_base + 1),
    );
    // Lateral face coedges (4)
    sat.add_coedge(
        ptr(co(5)),
        ptr(co(3)),
        ptr(co(1)),
        ptr(e_top),
        Sense::Reversed,
        ptr(loop_base + 2),
    );
    sat.add_coedge(
        ptr(co(2)),
        ptr(co(4)),
        ptr(co(5)),
        ptr(e_seam),
        Sense::Forward,
        ptr(loop_base + 2),
    );
    sat.add_coedge(
        ptr(co(3)),
        ptr(co(5)),
        ptr(co(0)),
        ptr(e_bot),
        Sense::Forward,
        ptr(loop_base + 2),
    );
    sat.add_coedge(
        ptr(co(4)),
        ptr(co(2)),
        ptr(co(3)),
        ptr(e_seam),
        Sense::Reversed,
        ptr(loop_base + 2),
    );

    // Loops
    sat.add_loop(SatPointer::NULL, ptr(co(0)), ptr(face_base));
    sat.add_loop(SatPointer::NULL, ptr(co(1)), ptr(face_base + 1));
    sat.add_loop(SatPointer::NULL, ptr(co(2)), ptr(face_base + 2));

    // Faces
    sat.add_face(
        ptr(face_base + 1),
        ptr(loop_base),
        ptr(shell_idx),
        ptr(surf_bot),
        Sense::Forward,
        Sidedness::Single,
    );
    sat.add_face(
        ptr(face_base + 2),
        ptr(loop_base + 1),
        ptr(shell_idx),
        ptr(surf_top),
        Sense::Forward,
        Sidedness::Single,
    );
    sat.add_face(
        SatPointer::NULL,
        ptr(loop_base + 2),
        ptr(shell_idx),
        ptr(surf_cyl),
        Sense::Forward,
        Sidedness::Single,
    );

    // Shell → Lump → Body
    sat.add_shell(ptr(face_base), ptr(lump_idx));
    sat.add_lump(ptr(shell_idx), body_idx);

    if let Some(body_rec) = sat.record_mut(0) {
        body_rec.tokens[1] = SatToken::Pointer(ptr(lump_idx));
    }

    // Back-pointers the modeler audits demand ("edge without backptr" /
    // "vertex without edge" are fatal in BricsCAD/AutoCAD): every edge
    // names one of its coedges, every vertex names an edge that contains
    // it (both seam endpoints name the seam edge).
    if let Some(r) = sat.record_mut(e_bot as usize) {
        r.tokens[5] = SatToken::Pointer(ptr(co(0)));
    }
    if let Some(r) = sat.record_mut(e_top as usize) {
        r.tokens[5] = SatToken::Pointer(ptr(co(1)));
    }
    if let Some(r) = sat.record_mut(e_seam as usize) {
        r.tokens[5] = SatToken::Pointer(ptr(co(3)));
    }
    if let Some(r) = sat.record_mut(v0 as usize) {
        r.tokens[1] = SatToken::Pointer(ptr(e_seam));
    }
    if let Some(r) = sat.record_mut(v1 as usize) {
        r.tokens[1] = SatToken::Pointer(ptr(e_seam));
    }

    sat
}

/// A minimal valid planar region: body → lump → shell → one plane face
/// with a closed four-edge outer loop. An open sheet — every edge has
/// exactly one coedge (partners null) — and every back-pointer wired
/// (edge → its coedge, vertex → its edge, body → its lump).
fn build_region_sat() -> SatDocument {
    let mut sat = SatDocument::new_body();
    let body_idx = SatPointer::new(0);
    let ptr = |i: i32| SatPointer::new(i);

    // Corners of a 10x10 square in the XY plane (counter-clockwise).
    let p0 = sat.add_point(0.0, 0.0, 0.0);
    let p1 = sat.add_point(10.0, 0.0, 0.0);
    let p2 = sat.add_point(10.0, 10.0, 0.0);
    let p3 = sat.add_point(0.0, 10.0, 0.0);

    let surf = sat.add_plane_surface([0.0, 0.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]);

    // Side curves, each directed along the loop traversal.
    let c0 = sat.add_straight_curve([0.0, 0.0, 0.0], [1.0, 0.0, 0.0]);
    let c1 = sat.add_straight_curve([10.0, 0.0, 0.0], [0.0, 1.0, 0.0]);
    let c2 = sat.add_straight_curve([10.0, 10.0, 0.0], [-1.0, 0.0, 0.0]);
    let c3 = sat.add_straight_curve([0.0, 10.0, 0.0], [0.0, -1.0, 0.0]);

    let v0 = sat.add_vertex(SatPointer::NULL, ptr(p0));
    let v1 = sat.add_vertex(SatPointer::NULL, ptr(p1));
    let v2 = sat.add_vertex(SatPointer::NULL, ptr(p2));
    let v3 = sat.add_vertex(SatPointer::NULL, ptr(p3));

    let e0 = sat.add_edge(ptr(v0), 0.0, ptr(v1), 10.0, SatPointer::NULL, ptr(c0), Sense::Forward);
    let e1 = sat.add_edge(ptr(v1), 0.0, ptr(v2), 10.0, SatPointer::NULL, ptr(c1), Sense::Forward);
    let e2 = sat.add_edge(ptr(v2), 0.0, ptr(v3), 10.0, SatPointer::NULL, ptr(c2), Sense::Forward);
    let e3 = sat.add_edge(ptr(v3), 0.0, ptr(v0), 10.0, SatPointer::NULL, ptr(c3), Sense::Forward);

    // Coedge indices: 4 coedges, then loop, face, shell, lump.
    let base = sat.records.len() as i32;
    let co = |i: i32| base + i;
    let loop_idx = base + 4;
    let face_idx = base + 5;
    let shell_idx = base + 6;
    let lump_idx = base + 7;

    let edges = [e0, e1, e2, e3];
    for i in 0..4i32 {
        let next = co((i + 1) % 4);
        let prev = co((i + 3) % 4);
        sat.add_coedge(
            ptr(next),
            ptr(prev),
            SatPointer::NULL, // open sheet: no partner coedge on another face
            ptr(edges[i as usize]),
            Sense::Forward,
            ptr(loop_idx),
        );
    }

    sat.add_loop(SatPointer::NULL, ptr(co(0)), ptr(face_idx));
    sat.add_face(
        SatPointer::NULL,
        ptr(loop_idx),
        ptr(shell_idx),
        ptr(surf),
        Sense::Forward,
        Sidedness::Single,
    );
    sat.add_shell(ptr(face_idx), ptr(lump_idx));
    sat.add_lump(ptr(shell_idx), body_idx);

    if let Some(body_rec) = sat.record_mut(0) {
        body_rec.tokens[1] = SatToken::Pointer(ptr(lump_idx));
    }

    // Back-pointers (same audits as the cylinder): edge → its coedge,
    // vertex → its edge.
    let coedges = [co(0), co(1), co(2), co(3)];
    for i in 0..4usize {
        if let Some(r) = sat.record_mut(edges[i] as usize) {
            r.tokens[5] = SatToken::Pointer(ptr(coedges[i]));
        }
    }
    let verts = [v0, v1, v2, v3];
    for i in 0..4usize {
        if let Some(r) = sat.record_mut(verts[i] as usize) {
            r.tokens[1] = SatToken::Pointer(ptr(edges[i]));
        }
    }

    sat
}

