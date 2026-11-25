//! Corpus roundtrip pilot (wave 0): a manifest-driven builder.
//!
//! Two modes:
//!
//! ```text
//! cargo run --example corpus_roundtrip -- analyze <oracle.dwg> <manifest.json>
//! cargo run --example corpus_roundtrip -- build <manifest.json> <out.dwg>
//! ```
//!
//! `analyze` decodes an oracle drawing codec-side and produces a JSON
//! manifest: one entry per family (a class of entities) with the parameters
//! this crate's writers can reproduce, plus a `gaps` list for everything
//! present in the oracle that no writer covers. `build` reads a manifest and
//! writes a new drawing from it through the `create` writers (unknown
//! families are skipped — they are already gaps).
//!
//! Verification happens Civil 3D-side (bridge): the built drawing must open
//! and audit clean, and its census must show the manifest's written
//! families with the same counts.

use acadrust::classes::civil::{add_alignment_with_curves, add_cogo_point, add_parcel, add_pipe, add_pipe_network, add_profile, add_profile_view_with_range, add_sample_line, add_sample_line_group, add_section_view, add_sections, add_site, add_structure, add_surface_profile, add_tin_surface, cpp_class_name, VertexCurve};
use acadrust::entities::{Arc, Circle, EntityType, Line, LwPolyline, LwVertex, MText, Polyline3D, Vertex3DPolyline};
use acadrust::io::dwg::{DwgReader, DwgWriter};
use acadrust::tables::Layer;
use acadrust::types::{Handle, Vector2, Vector3};
use std::collections::BTreeMap;

type Json = serde_json::Value;

fn jf(v: f64) -> Json {
    serde_json::json!(v)
}
fn j2(v: Vector2) -> Json {
    serde_json::json!([jf(v.x), jf(v.y)])
}
fn j3(v: Vector3) -> Json {
    serde_json::json!([jf(v.x), jf(v.y), jf(v.z)])
}
fn v2(v: &Json) -> Vector2 {
    Vector2::new(v[0].as_f64().unwrap_or(0.0), v[1].as_f64().unwrap_or(0.0))
}
fn v3(v: &Json) -> Vector3 {
    Vector3::new(v[0].as_f64().unwrap_or(0.0), v[1].as_f64().unwrap_or(0.0), v[2].as_f64().unwrap_or(0.0))
}

/// The census key of a native entity (the RX class the application shows).
fn native_key(e: &EntityType) -> Option<&'static str> {
    Some(match e {
        EntityType::Line(_) => "AcDbLine",
        EntityType::Circle(_) => "AcDbCircle",
        EntityType::Arc(_) => "AcDbArc",
        EntityType::Point(_) => "AcDbPoint",
        EntityType::Ellipse(_) => "AcDbEllipse",
        EntityType::Polyline(_) => "AcDb3dPolyline",
        EntityType::Polyline2D(_) => "AcDb2dPolyline",
        EntityType::Polyline3D(_) => "AcDb3dPolyline",
        EntityType::LwPolyline(_) => "AcDbPolyline",
        EntityType::MText(_) => "AcDbMText",
        EntityType::Text(_) => "AcDbText",
        EntityType::Spline(_) => "AcDbSpline",
        EntityType::Helix(_) => "AcDbHelix",
        EntityType::Dimension(_) => "AcDbDimension",
        EntityType::Hatch(_) => "AcDbHatch",
        EntityType::Solid(_) => "AcDbSolid",
        EntityType::Face3D(_) => "AcDbFace",
        EntityType::Insert(_) => "AcDbBlockReference",
        EntityType::Ray(_) => "AcDbRay",
        EntityType::XLine(_) => "AcDbXline",
        EntityType::Viewport(_) => "AcDbViewport",
        EntityType::AttributeDefinition(_) => "AcDbAttributeDefinition",
        EntityType::AttributeEntity(_) => "AcDbAttribute",
        EntityType::Leader(_) => "AcDbLeader",
        EntityType::MultiLeader(_) => "AcDbMLeader",
        EntityType::MLine(_) => "AcDbMline",
        EntityType::Mesh(_) => "AcDbSubDMesh",
        EntityType::RasterImage(_) => "AcDbRasterImage",
        EntityType::Solid3D(_) => "AcDb3dSolid",
        EntityType::Region(_) => "AcDbRegion",
        EntityType::Body(_) => "AcDbBody",
        EntityType::Surface(_) => "AcDbSurface",
        EntityType::Table(_) => "AcDbTable",
        EntityType::Tolerance(_) => "AcDbFcf",
        EntityType::PolyfaceMesh(_) => "AcDbPolyFaceMesh",
        EntityType::Wipeout(_) => "AcDbWipeout",
        EntityType::Shape(_) => "AcDbShape",
        EntityType::Underlay(_) => "AcDbUnderlayReference",
        EntityType::Ole2Frame(_) => "AcDbOle2Frame",
        EntityType::PolygonMesh(_) => "AcDbPolygonMesh",
        EntityType::Light(_) => "AcDbLight",
        EntityType::SectionSymbol(_) => "AcDbSectionSymbol",
        EntityType::ViewBorder(_) => "AcDbViewBorder",
        EntityType::Seqend(_) | EntityType::Block(_) | EntityType::BlockEnd(_) => return None,
        EntityType::Extended(_) => return None,
        EntityType::Unknown(_) => "AcDbUnknown",
    })
}

/// DXF name → the RX class the application shows, for classes the crate's
/// `cpp_class_name` table does not carry.
fn rx_fallback(dxf: &str) -> Option<&'static str> {
    Some(match dxf {
        "AECC_GRAPH_SECTION_VIEW" => "AeccDbGraphCrossSection",
        "AECC_SECTIONDATABAND_LABELGROUP" => "AeccDbSectionDataBandLabeling",
        "AEC_MVBLOCK_REF" => "AecDbMvBlockRef",
        "AECC_SAMPLELINE_LABELING" => "AeccDbSampleLineLabeling",
        _ => return None,
    })
}

fn census(doc: &acadrust::CadDocument) -> BTreeMap<String, usize> {
    let ms = doc.header.model_space_block_handle;
    let mut c: BTreeMap<String, usize> = BTreeMap::new();
    for e in doc.entities() {
        // Model space only — the application's census counts the same.
        let owned = match e {
            EntityType::Extended(x) => x.common.owner_handle.value() == ms.value(),
            other => other.common().owner_handle.value() == ms.value(),
        };
        if !owned {
            continue;
        }
        let key = match e {
            EntityType::Extended(x) => match &x.data {
                acadrust::entities::ExtendedEntityData::Arch(a) => cpp_class_name(&a.dxf_name)
                    .or_else(|| rx_fallback(&a.dxf_name))
                    .unwrap_or(&a.dxf_name)
                    .to_string(),
                _ => continue,
            },
            other => native_key(other).unwrap_or("AcDbUnknown").to_string(),
        };
        *c.entry(key).or_default() += 1;
    }
    c
}

/// Doc-wide class histogram of the non-graphical Civil objects (part
/// definitions, parts lists, styles, survey records): what the model-space
/// census does not show. Recorded in the manifest; build writes none of it.
fn object_census(doc: &acadrust::CadDocument) -> BTreeMap<String, usize> {
    let mut c: BTreeMap<String, usize> = BTreeMap::new();
    for o in doc.objects.values() {
        if let acadrust::objects::ObjectType::Arch(a) = o {
            *c.entry(a.dxf_name.clone()).or_default() += 1;
        }
    }
    c
}

/// Doc-wide entity histogram (every owner, model space or not).
fn doc_census(doc: &acadrust::CadDocument) -> BTreeMap<String, usize> {
    let mut c: BTreeMap<String, usize> = BTreeMap::new();
    for e in doc.entities() {
        let key = match e {
            EntityType::Extended(x) => match &x.data {
                acadrust::entities::ExtendedEntityData::Arch(a) => cpp_class_name(&a.dxf_name)
                    .or_else(|| rx_fallback(&a.dxf_name))
                    .unwrap_or(&a.dxf_name)
                    .to_string(),
                _ => continue,
            },
            other => native_key(other).unwrap_or("AcDbUnknown").to_string(),
        };
        *c.entry(key).or_default() += 1;
    }
    c
}

fn arch_of(doc: &acadrust::CadDocument, handle: Handle) -> Option<acadrust::classes::arch::ArchEntityData> {
    match doc.get_entity(handle) {
        Some(EntityType::Extended(x)) => match &x.data {
            acadrust::entities::ExtendedEntityData::Arch(a) => Some(a.clone()),
            _ => None,
        },
        _ => None,
    }
}

fn all_of(doc: &acadrust::CadDocument, dxf: &str) -> Vec<Handle> {
    let ms = doc.header.model_space_block_handle;
    doc.entities()
        .filter(|e| match e {
            EntityType::Extended(x) => x.common.owner_handle.value() == ms.value(),
            _ => false,
        })
        .filter_map(|e| match e {
            EntityType::Extended(x) => match &x.data {
                acadrust::entities::ExtendedEntityData::Arch(a) if a.dxf_name == dxf => Some(x.common.handle),
                _ => None,
            },
            _ => None,
        })
        .collect()
}

fn gap(family: &str, count: usize, missing: &str, implementable: &str) -> Json {
    serde_json::json!({ "family": family, "count": count, "missing": missing, "implementable": implementable })
}

// ---------------- analyze ----------------

fn analyze(doc: &acadrust::CadDocument, source: &str, mcp_census: Option<Json>) -> Json {
    let mut families: Vec<Json> = Vec::new();
    let mut gaps: Vec<Json> = Vec::new();

    // ---- native families ----
    let ms = doc.header.model_space_block_handle;
    let mut plines = Vec::new();
    let mut lwplines = Vec::new();
    let mut circles = Vec::new();
    let mut arcs = Vec::new();
    let mut lines = Vec::new();
    let mut mtexts = Vec::new();
    let mut native_gaps: BTreeMap<String, usize> = BTreeMap::new();
    for e in doc.entities() {
        let owned = match e {
            EntityType::Extended(_) => true, // civil families filter by class below
            other => other.common().owner_handle.value() == ms.value(),
        };
        if !owned {
            continue;
        }
        match e {
            EntityType::Polyline3D(p) => plines.push(p),
            EntityType::LwPolyline(p) => lwplines.push(p),
            EntityType::Circle(c) => circles.push(c),
            EntityType::Arc(a) => arcs.push(a),
            EntityType::Line(l) => lines.push(l),
            EntityType::MText(m) => mtexts.push(m),
            EntityType::Extended(_) => {}
            other => {
                let key = native_key(other).unwrap_or("AcDbUnknown");
                *native_gaps.entry(key.to_string()).or_default() += 1;
            }
        }
    }
    if !arcs.is_empty() {
        families.push(serde_json::json!({ "family": "arc", "count": arcs.len(), "items": arcs.iter().map(|a| serde_json::json!({
            "layer": a.common.layer, "center": j3(a.center), "radius": jf(a.radius),
            "start_angle": jf(a.start_angle), "end_angle": jf(a.end_angle),
        })).collect::<Vec<_>>() }));
    }
    if !plines.is_empty() {
        families.push(serde_json::json!({ "family": "polyline3d", "count": plines.len(), "items": plines.iter().map(|p| serde_json::json!({
            "layer": p.common.layer,
            "closed": p.flags.closed,
            "vertices": p.vertices.iter().map(|v| j3(v.position)).collect::<Vec<_>>(),
        })).collect::<Vec<_>>() }));
    }
    if !lwplines.is_empty() {
        families.push(serde_json::json!({ "family": "lwpolyline", "count": lwplines.len(), "items": lwplines.iter().map(|p| serde_json::json!({
            "layer": p.common.layer, "closed": p.is_closed, "elevation": jf(p.elevation),
            "vertices": p.vertices.iter().map(|v| serde_json::json!([jf(v.location.x), jf(v.location.y), jf(v.bulge)])).collect::<Vec<_>>(),
        })).collect::<Vec<_>>() }));
    }
    if !circles.is_empty() {
        families.push(serde_json::json!({ "family": "circle", "count": circles.len(), "items": circles.iter().map(|c| serde_json::json!({
            "layer": c.common.layer, "center": j3(c.center), "radius": jf(c.radius),
        })).collect::<Vec<_>>() }));
    }
    if !lines.is_empty() {
        families.push(serde_json::json!({ "family": "line", "count": lines.len(), "items": lines.iter().map(|l| serde_json::json!({
            "layer": l.common.layer, "start": j3(l.start), "end": j3(l.end),
        })).collect::<Vec<_>>() }));
    }
    if !mtexts.is_empty() {
        families.push(serde_json::json!({ "family": "mtext", "count": mtexts.len(), "items": mtexts.iter().map(|m| serde_json::json!({
            "layer": m.common.layer, "text": m.value, "location": j3(m.insertion_point), "height": jf(m.height),
        })).collect::<Vec<_>>() }));
    }
    for (key, count) in native_gaps {
        gaps.push(gap(&key, count, "no native writer wired into this bin", "uncertain — the crate writes some of these natively; the pilot bin does not"));
    }

    // ---- civil families ----
    // COGO points: number, position, raw description and name (the fields
    // the writer + decoder round-trip; styles are defaults).
    let cogo = acadrust::classes::civil::cogo_points(doc);
    if !cogo.is_empty() {
        families.push(serde_json::json!({ "family": "cogo_point", "count": cogo.len(), "items": cogo.iter().map(|p| serde_json::json!({
            "number": p.number,
            "position": j3(p.position),
            "description": p.description,
            "name": p.name,
        })).collect::<Vec<_>>() }));
    }

    // Gravity pipe networks: the parts the writers reproduce. The network
    // record itself is rebuilt implicitly by add_pipe_network (its name is
    // not carried — a parameter gap); connectors and part lists are app-side.
    let structures = all_of(doc, "AECC_STRUCTURE");
    if !structures.is_empty() {
        let items: Vec<Json> = structures
            .iter()
            .enumerate()
            .map(|(i, h)| {
                let a = arch_of(doc, *h).unwrap();
                let pos = a.structure_position().map(j3).unwrap_or(Json::Null);
                let rot = a.network_part_rotation().map(jf).unwrap_or(Json::Null);
                serde_json::json!({ "key": format!("ST{i}"), "position": pos, "rotation": rot })
            })
            .collect();
        families.push(serde_json::json!({ "family": "structure", "count": structures.len(), "items": items }));
    }
    let pipes = all_of(doc, "AECC_PIPE");
    if !pipes.is_empty() {
        let items: Vec<Json> = pipes
            .iter()
            .enumerate()
            .map(|(i, h)| {
                let a = arch_of(doc, *h).unwrap();
                match a.pipe_ends() {
                    Some((s, e)) => serde_json::json!({ "key": format!("PP{i}"), "start": j3(s), "end": j3(e) }),
                    None => serde_json::json!({ "key": format!("PP{i}"), "start": null, "end": null }),
                }
            })
            .collect();
        families.push(serde_json::json!({ "family": "pipe", "count": pipes.len(), "items": items }));
    }

    // TIN surfaces: points and triangle list (the points writer rebuilds the
    // TIN; the stored triangulation itself is a parameter gap).
    let surfaces = all_of(doc, "AECC_TIN_SURFACE");
    if !surfaces.is_empty() {
        let mut items = Vec::new();
        let mut empties = Vec::new();
        for h in &surfaces {
            let a = arch_of(doc, *h).unwrap();
            let name = a.decode().strings.get(2).cloned().unwrap_or_default();
            if let Some(t) = a.tin_surface() {
                let tris: Vec<Json> = t
                    .triangles
                    .iter()
                    .filter(|t| t.is_visible())
                    .map(|t| serde_json::json!([t.vertices[0], t.vertices[1], t.vertices[2]]))
                    .collect();
                items.push(serde_json::json!({
                    "name": name,
                    "points": t.vertices.iter().map(|v| j3(v.position)).collect::<Vec<_>>(),
                    "triangles": tris,
                }));
            } else {
                // D017 verification adaptation (recorded): keep the name of
                // an undecodable surface so the build can emit an empty
                // shell (#656 add_empty_tin_surface) with a faithful name.
                empties.push(name);
            }
        }
        families.push(serde_json::json!({ "family": "tin_surface", "count": surfaces.len(), "items": items, "empty": empties }));
        // Triangulation note: the points writer retriangulates; triangle
        // identity is compared in verify and expected to differ.
        gaps.push(gap("tin_surface.triangulation", surfaces.len(), "parameter: the stored triangle list (the points writer retriangulates)", "uncertain — check whether TinOperation has a faces op"));
    }

    // AECC_PARCEL holds sites and parcels in one record form: the
    // application shows both as AeccDbFace and casts the record to Site or
    // Parcel by its site reference — a parcel carries its site as the
    // record's second reference ([`ArchEntityData::parcel_site`]), a site
    // carries none. Survey-3 was the lesson (W1-6): its 163 AECC_PARCEL
    // records are 163 sites and no parcels — the application's site names
    // match the record names exactly (captured through the bridge,
    // 2026-11-25) — and the outlines the proxy graphics of site records
    // sketch are not parcel boundaries. So the parcel outline is only read
    // for records that carry a site, and site records are reported as their
    // own family (name + description; a site has no outline).
    let faces: Vec<(Handle, acadrust::classes::arch::ArchEntityData)> = all_of(doc, "AECC_PARCEL")
        .into_iter()
        .filter_map(|h| arch_of(doc, h).map(|a| (h, a)))
        .collect();
    if !faces.is_empty() {
        let sites: Vec<&(Handle, _)> = faces.iter().filter(|(_, a)| a.parcel_site().is_none()).collect();
        if !sites.is_empty() {
            let items: Vec<Json> = sites.iter().map(|(_, a)| {
                let (name, desc) = a.face_name().unwrap_or_default();
                serde_json::json!({ "name": name, "desc": desc })
            }).collect();
            families.push(serde_json::json!({ "family": "site", "count": sites.len(), "items": items }));
        }
        let parcels: Vec<&(Handle, _)> = faces.iter().filter(|(_, a)| a.parcel_site().is_some()).collect();
        if !parcels.is_empty() {
            let site_names: BTreeMap<u64, String> = sites.iter().filter_map(|(h, a)| {
                Some((h.value(), a.face_name()?.0))
            }).collect();
            let items: Vec<Json> = parcels.iter().map(|(_, a)| {
                let (name, _alt) = a.face_name().unwrap_or_default();
                let site = a.parcel_site().and_then(|s| site_names.get(&s).cloned()).unwrap_or_default();
                // W3-3: whether the outline re-decodes as a CLOSED ring
                // (first vertex repeated at the end) — the writer #665
                // embeds the face boundary ring; the manifest carries the
                // flag so the built file's ring is checked, not assumed.
                let mut outline = a.profiles.first().cloned().unwrap_or_default();
                let ring_closed = outline.len() > 1 && outline.first() == outline.last();
                if ring_closed {
                    outline.pop();
                }
                serde_json::json!({ "name": name, "site": site, "label": a.parcel_label().map(|p| j2(p)).unwrap_or(Json::Null), "ring_closed": ring_closed, "vertices": outline.iter().map(|p| j2(Vector2::new(p.x, p.y))).collect::<Vec<_>>() })
            }).collect();
            families.push(serde_json::json!({ "family": "parcel", "count": parcels.len(), "items": items }));
        }
    }

    // Feature lines: name plus the vertices of the line's edge in its site
    // container's topology (reader #666; PARTIAL FILL by design — only the
    // records whose site container, topology and edge id all decode return
    // vertices; Grading-3A ships 2 of 14, its second topology section is
    // unmapped). The bin wires no feature-line writer this round: the
    // family is decode-only ("write": false; compare_verify skips it).
    let flines = all_of(doc, "AECC_FEATURE_LINE");
    if !flines.is_empty() {
        let mut items = Vec::new();
        let mut undecoded = Vec::new();
        for h in &flines {
            let a = arch_of(doc, *h).unwrap();
            let (name, _desc) = a.feature_line_name().unwrap_or_default();
            match acadrust::classes::civil::feature_line_vertices(doc, *h) {
                Some(vs) => items.push(serde_json::json!({
                    "name": name,
                    "vertices": vs.iter().map(|v| serde_json::json!([jf(v.point.x), jf(v.point.y), jf(v.point.z), jf(v.bulge), v.elevation_point])).collect::<Vec<_>>(),
                })),
                None => undecoded.push(name),
            }
        }
        families.push(serde_json::json!({ "family": "feature_line", "count": flines.len(), "write": false, "items": items, "undecoded": undecoded }));
    }

    // Survey figures: name, site, the traverse-vertex cache the class body
    // keeps and the bbox solid's elevation range (reader #664; the
    // elevations are bit for bit the live application's Min/MaxElevation,
    // the vertices within the shared solved-point tolerance). Decode-only
    // this round ("write": false).
    let sfigs = all_of(doc, "AECC_SVFIGURE");
    if !sfigs.is_empty() {
        let mut items = Vec::new();
        let mut undecoded = Vec::new();
        for h in &sfigs {
            let a = arch_of(doc, *h).unwrap();
            let Some(f) = a.survey_figure() else { undecoded.push(Json::Null); continue };
            match a.survey_figure_geometry() {
                Some(g) => items.push(serde_json::json!({
                    "name": f.name, "site": f.site,
                    "vertices": g.vertices.iter().map(|v| j3(*v)).collect::<Vec<_>>(),
                    "elevations": [jf(g.min_elevation), jf(g.max_elevation)],
                })),
                None => undecoded.push(Json::from(f.name)),
            }
        }
        families.push(serde_json::json!({ "family": "survey_figure", "count": sfigs.len(), "write": false, "items": items, "undecoded": undecoded }));
    }

    // Alignments: PIs from the solved pieces, curve radius at a vertex from
    // the piece curvature. Non line/arc elements cannot round-trip through
    // the PI writer — logged per occurrence.
    let alignments = all_of(doc, "AECC_ALIGNMENT");
    let mut align_keys: Vec<(Handle, String)> = Vec::new();
    if !alignments.is_empty() {
        let mut items = Vec::new();
        for (i, h) in alignments.iter().enumerate() {
            let a = arch_of(doc, *h).unwrap();
            let name = a.alignment_name().unwrap_or_default();
            let key = if name.is_empty() { format!("AL{i}") } else { name.clone() };
            let key = if align_keys.iter().any(|(_h, k)| *k == key) { format!("{key}#{i}") } else { key };
            align_keys.push((*h, key.clone()));
            let pieces = a.alignment_pieces_with_curvature();
            // PIs: a line piece contributes its end unless the next piece
            // is an arc (the arc's PI replaces it); an arc between two
            // lines contributes their intersection and its radius.
            let mut vertices: Vec<Vector2> = Vec::new();
            let mut radii_at: Vec<(usize, f64)> = Vec::new(); // (vertex index, radius)
            let seg_line = |pts: &[Vector2]| -> (Vector2, Vector2) { (pts[0], *pts.last().unwrap_or(&pts[0])) };
            if let Some(first) = pieces.first().map(|p| p.2[0]) {
                vertices.push(first);
            }
            for j in 0..pieces.len() {
                let (_piece, curvature, pts) = &pieces[j];
                if *curvature != 0.0 {
                    let pi = (|| {
                        let prev = pieces.get(j.checked_sub(1)?)?;
                        let next = pieces.get(j + 1)?;
                        let (p1, p2) = seg_line(&prev.2);
                        let (p3, p4) = seg_line(&next.2);
                        let d1 = p2 - p1;
                        let d2 = p4 - p3;
                        let den = d1.x * d2.y - d1.y * d2.x;
                        if den.abs() < 1e-12 {
                            return None;
                        }
                        let t = ((p3.x - p1.x) * d2.y - (p3.y - p1.y) * d2.x) / den;
                        Some(p1 + d1 * t)
                    })();
                    let Some(pi) = pi else { continue };
                    let vi = vertices.len();
                    vertices.push(pi);
                    // vi is the PI's vertex index; the inner index (what
                    // curve_radii indexes) is vi-1. Recorded verify2 fix:
                    // the walk previously subtracted 1 twice (here and in
                    // the apply loop below), dropping the first curve's
                    // radius and shifting the rest — visible once the site
                    // alignments (#662) made curves round-trip through the
                    // built file's own decode.
                    radii_at.push((vi, 1.0 / curvature.abs()));
                } else {
                    let next_is_arc = pieces.get(j + 1).map(|p| p.1 != 0.0).unwrap_or(false);
                    if next_is_arc {
                        continue; // the arc's PI takes this place
                    }
                    let end = *pts.last().unwrap_or(&pts[0]);
                    if let Some(last) = vertices.last() {
                        if (last.x - end.x).abs() < 1e-12 && (last.y - end.y).abs() < 1e-12 {
                            continue;
                        }
                    }
                    vertices.push(end);
                }
            }
            if vertices.len() < 2 {
                // Nothing walkable — fall back to the stroked polyline.
                vertices = a.alignment_polylines().first().cloned().unwrap_or_default();
            }
            let mut curve_radii = vec![0.0f64; vertices.len().saturating_sub(2)];
            for (vi, r) in &radii_at {
                // curve_radii[i] is the curve at inner vertex i+1.
                if *vi >= 1 && *vi - 1 < curve_radii.len() {
                    curve_radii[*vi - 1] = *r;
                }
            }
            items.push(serde_json::json!({ "key": key, "name": name, "layer": "C-ROAD", "vertices": vertices.iter().map(|v| j2(*v)).collect::<Vec<_>>(), "curve_radii": curve_radii.iter().map(|r| jf(*r)).collect::<Vec<_>>() }));
        }
        families.push(serde_json::json!({ "family": "alignment", "count": alignments.len(), "items": items }));
    }

    // Profiles: PVIs with curve lengths, linked to their alignment by the
    // alignment handle in the record's references.
    let profiles = all_of(doc, "AECC_PROFILE");
    if !profiles.is_empty() {
        let mut items = Vec::new();
        for (i, h) in profiles.iter().enumerate() {
            let a = arch_of(doc, *h).unwrap();
            let name = a.profile_name().unwrap_or_default();
            let mut align_key = a
                .typed_handles()
                .iter()
                .find_map(|(v, _k)| align_keys.iter().find(|(ah, _k)| ah.value() == *v).map(|(_ah, k)| k.clone()))
                .unwrap_or_default();
            if align_key.is_empty() {
                // The record carries no alignment handle: link by sampling
                // over each alignment (exactly one yields elevations).
                let mut hits = align_keys.iter().filter(|(ah, _k)| {
                    matches!(arch_of(doc, *ah), Some(al) if !a.profile_over(&al).is_empty())
                });
                if let Some((ah, k)) = hits.next() {
                    align_key = k.clone();
                    if hits.next().is_some() {
                        align_key = String::new(); // ambiguous — skip
                    }
                }
            }
            let pvis: Vec<Json> = a.profile_pvis().iter().map(|p| serde_json::json!({ "station": jf(p.point.x), "elevation": jf(p.point.y), "curve": jf(p.curve_length) })).collect();
            items.push(serde_json::json!({ "key": format!("PF{i}"), "name": name, "alignment": align_key, "pvis": pvis }));
        }
        families.push(serde_json::json!({ "family": "profile", "count": profiles.len(), "items": items }));
    }

    // Profile views: frame (origin + ranges), linked to the alignment.
    let pviews = all_of(doc, "AECC_PROFILE_VIEW");
    if !pviews.is_empty() {
        let items: Vec<Json> = pviews
            .iter()
            .enumerate()
            .map(|(i, h)| {
                let a = arch_of(doc, *h).unwrap();
                let name = a.decode().strings.get(2).cloned().unwrap_or_default();
                let align_key = a
                    .typed_handles()
                    .iter()
                    .find_map(|(v, _k)| align_keys.iter().find(|(ah, _k)| ah.value() == *v).map(|(_ah, k)| k.clone()))
                    .unwrap_or_default();
                match a.profile_view_frame() {
                    Some(f) => serde_json::json!({ "key": format!("PV{i}"), "name": name, "alignment": align_key, "origin": j2(f.origin), "stations": [jf(f.station_min), jf(f.station_max)], "elevations": [jf(f.elevation_min), jf(f.elevation_max)] }),
                    None => serde_json::json!({ "key": format!("PV{i}"), "name": name, "alignment": align_key, "origin": null }),
                }
            })
            .collect();
        families.push(serde_json::json!({ "family": "profile_view", "count": pviews.len(), "items": items }));
    }

    // Sample line groups: stations + swath widths, linked to the alignment.
    let groups = all_of(doc, "AECC_SAMPLE_LINE_GROUP");
    let mut group_keys: Vec<(Handle, String)> = Vec::new();
    if !groups.is_empty() {
        let mut items = Vec::new();
        for (i, h) in groups.iter().enumerate() {
            let a = arch_of(doc, *h).unwrap();
            let name = a.decode().strings.get(2).cloned().unwrap_or_default();
            let key = if name.is_empty() { format!("SLG{i}") } else { name.clone() };
            group_keys.push((*h, key.clone()));
            let align_key = a
                .typed_handles()
                .iter()
                .find_map(|(v, _k)| align_keys.iter().find(|(ah, _k)| ah.value() == *v).map(|(_ah, k)| k.clone()))
                .unwrap_or_default();
            let sl = a.sample_lines();
            let (stations, left, right) = match sl {
                Some(sl) => (sl.stations.iter().map(|s| jf(*s)).collect::<Vec<_>>(), sl.left, sl.right),
                None => (Vec::new(), 0.0, 0.0),
            };
            items.push(serde_json::json!({ "key": key, "name": name, "alignment": align_key, "left": jf(left), "right": jf(right), "stations": stations }));
        }
        families.push(serde_json::json!({ "family": "sample_line_group", "count": groups.len(), "items": items }));
    }

    // Sample lines: their stations come from the lines' own records (the
    // group's station list decodes empty on this drawing's groups). The
    // swath widths are a parameter gap — the manifest uses a nominal one.
    let slines = all_of(doc, "AECC_SAMPLE_LINE");
    if !slines.is_empty() {
        let mut items = Vec::new();
        for (i, h) in slines.iter().enumerate() {
            let a = arch_of(doc, *h).unwrap();
            let group_key = a
                .typed_handles()
                .iter()
                .find_map(|(v, _k)| group_keys.iter().find(|(gh, _k)| gh.value() == *v).map(|(_gh, k)| k.clone()))
                .unwrap_or_default();
            let station = a.sample_line_station().map(jf).unwrap_or(Json::Null);
            items.push(serde_json::json!({ "key": format!("SL{i}"), "group": group_key, "station": station }));
        }
        families.push(serde_json::json!({ "family": "sample_line", "count": slines.len(), "items": items }));
        gaps.push(gap("sample_line.swath", slines.len(), "parameter: the line's left/right swath widths (records not decoded; nominal 10/10 used)", "yes — read the vertex records the writer itself writes (add_sample_line_through)"));
    }

    // Sections: written per group+surface at build time (add_sections); the
    // manifest records the counts for verification.
    let sections = all_of(doc, "AECC_SECTION");
    let corridor_sections = all_of(doc, "AECC_SECTION_CORRIDOR");
    if !sections.is_empty() {
        families.push(serde_json::json!({ "family": "section", "count": sections.len(), "items": [] }));
    }
    if !corridor_sections.is_empty() {
        gaps.push(gap("AeccDbSectionCorridor", corridor_sections.len(), "writer: corridor sections need the corridor", "yes — after a corridor writer lands"));
    }

    // Section views: origin per view, matched to sample lines by order.
    // When no frame decodes, the family cannot be rebuilt — a gap.
    let sviews = all_of(doc, "AECC_GRAPH_SECTION_VIEW");
    if !sviews.is_empty() {
        let items: Vec<Json> = sviews
            .iter()
            .enumerate()
            .map(|(i, h)| {
                let a = arch_of(doc, *h).unwrap();
                let group_key = a
                    .typed_handles()
                    .iter()
                    .find_map(|(v, _k)| group_keys.iter().find(|(gh, _k)| gh.value() == *v).map(|(_gh, k)| k.clone()))
                    .unwrap_or_default();
                let origin = a.section_view_frame().map(|f| j2(f.origin)).unwrap_or(Json::Null);
                serde_json::json!({ "key": format!("SV{i}"), "group": group_key, "origin": origin })
            })
            .collect();
        if items.iter().any(|i| i["origin"].is_array()) {
            families.push(serde_json::json!({ "family": "section_view", "count": sviews.len(), "items": items }));
        } else {
            gaps.push(gap("AeccDbGraphCrossSection", sviews.len(), "parameter: the view frames (section_view_frame() decodes None on these records; the writer add_section_view needs the origin)", "yes — writer exists; extend the frame grammar to this record form"));
        }
    }

    // Assemblies, corridors, subassemblies and the labeling records: gaps.
    for (dxf, why) in [
        ("AECC_ASSEMBLY", "writer exists (add_assembly) but the assembly's subassembly layout needs PKT package content — pilot skips"),
        ("AECC_CORRIDOR", "writer exists (add_corridor) but needs the assembly; pilot skips with it"),
        ("AECC_SUBASSEMBLY", "needs a PKT package from the tool palette catalog; parameters are decoded but not carried in the manifest yet"),
        ("AECC_SAMPLE_LINE_LABELING", "labeling records are written by the application inside the group's records; no standalone writer"),
        ("AECC_SECTIONALDTABAND_LABELGROUP", "band labeling group; no standalone writer"),
        ("AECC_VALIGNMENT_SAGCURVE_LABEL_GROUP", "label group; no standalone writer in the pilot bin"),
        ("AECC_VALIGNMENT_CRESTCURVE_LABEL_GROUP", "label group; no standalone writer in the pilot bin"),
    ] {
        let n = all_of(doc, dxf).len();
        if n > 0 {
            gaps.push(gap(cpp_class_name(dxf).unwrap_or(dxf), n, missing_of(why), implementable_of(why)));
        }
    }

    // Network part definitions (doc objects): record what the file holds
    // — the packet-1 pipe/structure wiring names a part definition per
    // pipe/structure, but a drawing's own part-def records have no
    // manifest family and no writer here.
    let part_defs: Vec<&acadrust::classes::arch::ArchObject> = doc
        .objects
        .values()
        .filter_map(|o| match o {
            acadrust::objects::ObjectType::Arch(a) if a.dxf_name == "AECC_NETWORK_PART_DEF" => Some(a),
            _ => None,
        })
        .collect();
    if !part_defs.is_empty() {
        let with_strings = part_defs.iter().filter(|a| !a.decode().strings.is_empty()).count();
        gaps.push(serde_json::json!({ "family": "AECC_NETWORK_PART_DEF", "count": part_defs.len(), "missing": format!("writer: no manifest family for a drawing's own part-definition records ({with_strings} of {} decode inline strings; the number-field reader targets the entity record form); the pipe/structure writers rebuild an implicit default catalog", part_defs.len()), "implementable": "uncertain — the object records keep their bodies; a parts-catalog writer is create/network.rs dictionary work" }));
    }

    let c = census(doc);
    serde_json::json!({
        "source": source,
        "codec_census": c,
        "mcp_census": mcp_census,
        "doc_census": doc_census(doc),
        "object_census": object_census(doc),
        "families": families,
        "gaps": gaps,
    })
}

fn missing_of(why: &str) -> &'static str {
    if why.contains("writer exists") { "writer: chained (pilot scope)" } else { "writer" }
}
fn implementable_of(why: &str) -> &'static str {
    if why.contains("PKT") { "uncertain — PKT package content must ship from the catalog" } else { "yes — writers exist, wiring is mechanical" }
}

// ---------------- build ----------------

fn build(manifest: &Json, out: &std::path::Path) -> Result<Vec<String>, String> {
    let mut notes = Vec::new();
    let mut doc = acadrust::CadDocument::new();
    doc.version = acadrust::types::DxfVersion::AC1032;

    // Layers the manifest's entities sit on (a layer the table lacks would
    // normalize every entity back to "0").
    let mut ensure_layer = |doc: &mut acadrust::CadDocument, name: &str| {
        if doc.layers.get(name).is_none() && name != "0" {
            let _ = doc.layers.add(Layer::new(name));
        }
    };
    for fam in manifest["families"].as_array().cloned().unwrap_or_default() {
        for item in fam["items"].as_array().cloned().unwrap_or_default() {
            if let Some(layer) = item["layer"].as_str() {
                ensure_layer(&mut doc, layer);
            }
        }
    }

    let fams = manifest["families"].as_array().cloned().unwrap_or_default();
    let find = |fams: &[Json], name: &str| fams.iter().find(|f| f["family"] == name).cloned();

    // Native entities first.
    for name in ["polyline3d", "lwpolyline", "circle", "arc", "line", "mtext"] {
        if let Some(f) = find(&fams, name) {
            for item in f["items"].as_array().unwrap_or(&vec![]) {
                match name {
                    "lwpolyline" => {
                        let mut p = LwPolyline::new();
                        p.common.layer = item["layer"].as_str().unwrap_or("0").to_string();
                        p.is_closed = item["closed"].as_bool().unwrap_or(false);
                        p.elevation = item["elevation"].as_f64().unwrap_or(0.0);
                        p.vertices = item["vertices"].as_array().unwrap().iter().map(|v| LwVertex {
                            location: Vector2::new(v[0].as_f64().unwrap_or(0.0), v[1].as_f64().unwrap_or(0.0)),
                            bulge: v.get(2).and_then(|b| b.as_f64()).unwrap_or(0.0),
                            start_width: 0.0,
                            end_width: 0.0,
                            vertex_id: 0,
                        }).collect();
                        doc.add_entity(EntityType::LwPolyline(p)).map_err(|e| e.to_string())?;
                    }
                    "arc" => {
                        let mut a = Arc::new();
                        a.common.layer = item["layer"].as_str().unwrap_or("0").to_string();
                        a.center = v3(&item["center"]);
                        a.radius = item["radius"].as_f64().unwrap_or(1.0);
                        a.start_angle = item["start_angle"].as_f64().unwrap_or(0.0);
                        a.end_angle = item["end_angle"].as_f64().unwrap_or(0.0);
                        doc.add_entity(EntityType::Arc(a)).map_err(|e| e.to_string())?;
                    }
                    "polyline3d" => {
                        let mut p = Polyline3D::new();
                        p.common.layer = item["layer"].as_str().unwrap_or("0").to_string();
                        // W4-2 build-side fix (recorded): carry the decoded
                        // closed flag into the typed field — the writer
                        // round-trips it (pinned upstream in #657).
                        p.flags.closed = item["closed"].as_bool().unwrap_or(false);
                        p.vertices = item["vertices"].as_array().unwrap().iter().map(|v| Vertex3DPolyline { handle: Handle::NULL, layer: String::new(), position: v3(v), flags: 0 }).collect();
                        doc.add_entity(EntityType::Polyline3D(p)).map_err(|e| e.to_string())?;
                    }
                    "circle" => {
                        let mut c = Circle::new();
                        c.common.layer = item["layer"].as_str().unwrap_or("0").to_string();
                        c.center = v3(&item["center"]);
                        c.radius = item["radius"].as_f64().unwrap_or(1.0);
                        doc.add_entity(EntityType::Circle(c)).map_err(|e| e.to_string())?;
                    }
                    "line" => {
                        let mut l = Line { common: Default::default(), start: v3(&item["start"]), end: v3(&item["end"]), thickness: 0.0, normal: Vector3::UNIT_Z };
                        l.common.layer = item["layer"].as_str().unwrap_or("0").to_string();
                        doc.add_entity(EntityType::Line(l)).map_err(|e| e.to_string())?;
                    }
                    "mtext" => {
                        let mut m = MText::new();
                        m.common.layer = item["layer"].as_str().unwrap_or("0").to_string();
                        m.value = item["text"].as_str().unwrap_or_default().to_string();
                        m.insertion_point = v3(&item["location"]);
                        m.height = item["height"].as_f64().unwrap_or(1.0);
                        doc.add_entity(EntityType::MText(Box::new(m))).map_err(|e| e.to_string())?;
                    }
                    _ => {}
                }
            }
        }
    }

    // COGO points (before parcels; the number is explicit so a failed name
    // set below does not shift later points).
    if let Some(f) = find(&fams, "cogo_point") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let number = item["number"].as_u64().map(|n| n as u32);
            let position = v3(&item["position"]);
            let description = item["description"].as_str().map(|s| s.to_string());
            let name = item["name"].as_str().map(|s| s.to_string());
            match add_cogo_point(&mut doc, number, position, description.as_deref(), None, None) {
                Ok(h) => {
                    if let Some(n) = &name {
                        if let Err(e) = acadrust::classes::civil::set_cogo_point_name(&mut doc, h, Some(n)) {
                            notes.push(format!("cogo_point {number:?} name {n:?}: {e}"));
                        }
                    }
                }
                Err(e) => notes.push(format!("cogo_point {number:?}: {e}")),
            }
        }
    }

    // Gravity pipe network: one network per file (the oracle's network name
    // and parts list are not carried — logged gaps), parts in manifest order.
    if find(&fams, "structure").is_some() || find(&fams, "pipe").is_some() {
        match add_pipe_network(&mut doc, "NETWORK", None) {
            Ok(network) => {
                if let Some(f) = find(&fams, "structure") {
                    for item in f["items"].as_array().unwrap_or(&vec![]) {
                        let Some(position) = item.get("position").and_then(|v| v.is_array().then(|| v3(v))) else {
                            notes.push(format!("structure {}: no position decoded", item["key"]));
                            continue;
                        };
                        let rotation = item["rotation"].as_f64().unwrap_or(0.0);
                        if let Err(e) = add_structure(&mut doc, network, position, rotation) {
                            notes.push(format!("structure {}: {e}", item["key"]));
                        }
                    }
                }
                if let Some(f) = find(&fams, "pipe") {
                    for item in f["items"].as_array().unwrap_or(&vec![]) {
                        let (Some(start), Some(end)) = (
                            item.get("start").and_then(|v| v.is_array().then(|| v3(v))),
                            item.get("end").and_then(|v| v.is_array().then(|| v3(v))),
                        ) else {
                            notes.push(format!("pipe {}: no ends decoded", item["key"]));
                            continue;
                        };
                        if let Err(e) = add_pipe(&mut doc, network, start, end) {
                            notes.push(format!("pipe {}: {e}", item["key"]));
                        }
                    }
                }
            }
            Err(e) => notes.push(format!("pipe_network: {e}")),
        }
    }

    // Sites + parcels. Sites first (the application holds both in the
    // AECC_PARCEL record form; see analyze), then each parcel joins the
    // site its manifest names — the record the parcel's site reference
    // points at in the oracle.
    let mut site: Option<Handle> = None;
    let mut site_handles: BTreeMap<String, Handle> = BTreeMap::new();
    if let Some(f) = find(&fams, "site") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let name = item["name"].as_str().unwrap_or_default();
            let desc = item["desc"].as_str().unwrap_or_default();
            match add_site(&mut doc, name, desc) {
                Ok(h) => { site_handles.insert(name.to_string(), h); }
                Err(e) => notes.push(format!("site {name}: {e}")),
            }
        }
    }
    if let Some(f) = find(&fams, "parcel") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let s = item["site"].as_str()
                .and_then(|n| site_handles.get(n).copied())
                .or_else(|| { let s = site.get_or_insert_with(|| add_site(&mut doc, "SITE", "").unwrap()); Some(*s) });
            let Some(s) = s else { continue };
            let vertices: Vec<Vector2> = item["vertices"].as_array().map(|a| a.iter().map(|v| v2(v)).collect()).unwrap_or_default();
            match add_parcel(&mut doc, s, &vertices, None) {
                Ok(_) => {}
                Err(e) => notes.push(format!("parcel {}: {}", item["name"].as_str().unwrap_or("?"), e)),
            }
        }
    }

    // Surfaces.
    let mut surface_handles: Vec<Handle> = Vec::new();
    // D017 verification adaptation (recorded): on the fixed tree the
    // empty-shell reader (#656) decodes an unbuilt surface as the four
    // bounding corners at ±f64::MAX with no triangles. Route that item to
    // the empty-shell writer so the built record stays the empty shell the
    // application stores (app reads vertices=0 triangles=0, as the oracle).
    fn is_empty_shell(points: &[Vector3], n_tris: usize) -> bool {
        n_tris == 0
            && points.len() == 4
            && points.iter().all(|p| p.x.abs() == f64::MAX && p.y.abs() == f64::MAX && p.z.abs() == f64::MAX)
    }
    if let Some(f) = find(&fams, "tin_surface") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let points: Vec<Vector3> = item["points"].as_array().map(|a| a.iter().map(|v| v3(v)).collect()).unwrap_or_default();
            let n_tris = item["triangles"].as_array().map(|a| a.len()).unwrap_or(0);
            let name = item["name"].as_str().unwrap_or("SURF");
            let res = if is_empty_shell(&points, n_tris) {
                acadrust::classes::civil::add_empty_tin_surface(&mut doc, name, None)
            } else {
                add_tin_surface(&mut doc, name, &points, None)
            };
            match res {
                Ok(h) => surface_handles.push(h),
                Err(e) => notes.push(format!("tin_surface: {e}")),
            }
        }
        // D017 verification adaptation (recorded): surfaces whose stored
        // triangulation is undecodable (items < count, e.g. W4-3 'EG') now
        // longer drifts. Names come from analyze's "empty" list.
        let count = f["count"].as_u64().unwrap_or(0) as usize;
        let written = f["items"].as_array().map(|a| a.len()).unwrap_or(0);
        let empties: Vec<String> = f["empty"].as_array().map(|a| a.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect()).unwrap_or_default();
        for i in written..count {
            let name = empties.get(i - written).map(|s| s.as_str()).unwrap_or("SURF");
            match acadrust::classes::civil::add_empty_tin_surface(&mut doc, name, None) {
                Ok(h) => surface_handles.push(h),
                Err(e) => notes.push(format!("tin_surface empty {name:?}: {e}")),
            }
        }
    }

    // Alignments, keyed.
    let mut align_map: std::collections::HashMap<String, Handle> = Default::default();
    if let Some(f) = find(&fams, "alignment") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let vertices: Vec<Vector2> = item["vertices"].as_array().map(|a| a.iter().map(|v| v2(v)).collect()).unwrap_or_default();
            let radii: Vec<f64> = item["curve_radii"].as_array().map(|a| a.iter().filter_map(|v| v.as_f64()).collect()).unwrap_or_default();
            let curves: Vec<VertexCurve> = (0..vertices.len().saturating_sub(2)).map(|i| if radii.get(i).copied().unwrap_or(0.0) > 0.0 { VertexCurve::Arc(radii[i]) } else { VertexCurve::None }).collect();
            let key = item["key"].as_str().unwrap_or("AL").to_string();
            let name = item["name"].as_str().unwrap_or(&key).to_string();
            match add_alignment_with_curves(&mut doc, &name, &vertices, &curves, None) {
                Ok(h) => {
                    align_map.insert(key, h);
                }
                Err(e) => notes.push(format!("alignment {key}: {e}")),
            }
        }
    }

    // Profiles.
    let mut profile_handles: Vec<Handle> = Vec::new();
    if let Some(f) = find(&fams, "profile") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let Some(align_key) = item["alignment"].as_str().map(|s| s.to_string()) else { continue };
            let Some(alignment) = align_map.get(&align_key).copied() else {
                notes.push(format!("profile {}: alignment {align_key} missing", item["key"]));
                continue;
            };
            let pvis: Vec<Vector2> = item["pvis"].as_array().map(|a| a.iter().map(|p| Vector2::new(p["station"].as_f64().unwrap_or(0.0), p["elevation"].as_f64().unwrap_or(0.0))).collect()).unwrap_or_default();
            let name = item["name"].as_str().unwrap_or("PF").to_string();
            let curves: Vec<f64> = if pvis.len() >= 3 {
                item["pvis"].as_array().unwrap()[1..pvis.len() - 1].iter().map(|p| p["curve"].as_f64().unwrap_or(0.0)).collect()
            } else {
                Vec::new()
            };
            let built = if pvis.len() >= 2 {
                add_profile(&mut doc, alignment, &name, &pvis, &curves, None)
            } else if let Some(surface) = surface_handles.first().copied() {
                // A profile with no PVIs is a surface profile (EG).
                add_surface_profile(&mut doc, alignment, surface, &name, 0.0, None, None)
            } else {
                Err(acadrust::error::DxfError::Parse("no PVIs and no surface for a surface profile".into()))
            };
            match built {
                Ok(h) => profile_handles.push(h),
                Err(e) => notes.push(format!("profile {}: {e}", item["key"])),
            }
        }
    }

    // Profile views.
    if let Some(f) = find(&fams, "profile_view") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let Some(align_key) = item["alignment"].as_str().map(|s| s.to_string()) else { continue };
            let Some(alignment) = align_map.get(&align_key).copied() else { continue };
            let Some(origin) = item.get("origin").and_then(|v| v.is_array().then(|| v2(v))) else {
                notes.push(format!("profile_view {}: no frame decoded", item["key"]));
                continue;
            };
            let stations = item["stations"].as_array().map(|a| (a[0].as_f64(), a[1].as_f64()));
            let elevations = item["elevations"].as_array().map(|a| (a[0].as_f64(), a[1].as_f64()));
            let name = item["name"].as_str().unwrap_or("PV").to_string();
            match add_profile_view_with_range(&mut doc, alignment, &name, origin, stations.and_then(|(a, b)| Some((a?, b?))), elevations.and_then(|(a, b)| Some((a?, b?))), None) {
                Ok(_) => {}
                Err(e) => notes.push(format!("profile_view {}: {e}", item["key"])),
            }
        }
    }

    // Sample line groups.
    let mut group_handles: Vec<(String, Handle, Vec<Handle>, usize)> = Vec::new();
    if let Some(f) = find(&fams, "sample_line_group") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let Some(align_key) = item["alignment"].as_str().map(|s| s.to_string()) else { continue };
            let Some(alignment) = align_map.get(&align_key).copied() else { continue };
            let name = item["name"].as_str().unwrap_or("SLG").to_string();
            let Ok(group) = add_sample_line_group(&mut doc, alignment, &name, None) else {
                notes.push(format!("sample_line_group {name}: failed"));
                continue;
            };
            group_handles.push((name.clone(), group, Vec::new(), 0usize));
            let _ = item;
        }
    }
    // Sample lines: station per line, nominal swath (a logged gap).
    if let Some(f) = find(&fams, "sample_line") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let gkey = item["group"].as_str().unwrap_or_default().to_string();
            let Some(gi) = group_handles.iter().position(|(n, _g, _l, _c)| *n == gkey) else { continue };
            let Some(station) = item["station"].as_f64() else { continue };
            // The name counter counts attempts, not successes (a failed
            // line must not shift the later names).
            let sname = format!("SL{}", group_handles[gi].3 + 1);
            group_handles[gi].3 += 1;
            match add_sample_line(&mut doc, group_handles[gi].1, &sname, station, 10.0, 10.0, None) {
                Ok(h) => group_handles[gi].2.push(h),
                Err(e) => notes.push(format!("sample line {sname} at {station}: {e}")),
            }
        }
    }
    // Sections sample the first surface.
    if !surface_handles.is_empty() {
        for (_name, group, _lines, _c) in &group_handles {
            if let Err(e) = add_sections(&mut doc, *group, surface_handles[0]) {
                notes.push(format!("sections: {e}"));
            }
        }
    }
    if let Some(f) = find(&fams, "section_view") {
        let items = f["items"].as_array().cloned().unwrap_or_default();
        // Views are matched to sample lines by order within the group.
        let mut per_group: std::collections::HashMap<String, Vec<(usize, &Json)>> = Default::default();
        for (i, item) in items.iter().enumerate() {
            let g = item["group"].as_str().unwrap_or_default().to_string();
            per_group.entry(g).or_default().push((i, item));
        }
        for (gname, views) in per_group {
            let Some((_n, _g, lines, _c)) = group_handles.iter().find(|(n, _g, _l, _c)| *n == gname) else { continue };
            for (j, (_i, item)) in views.iter().enumerate() {
                let Some(line) = lines.get(j).copied() else { continue };
                let Some(origin) = item.get("origin").and_then(|v| v.is_array().then(|| v2(v))) else { continue };
                let sname = format!("SV{}", j + 1);
                if let Err(e) = add_section_view(&mut doc, line, &sname, origin, None) {
                    notes.push(format!("section_view {sname}: {e}"));
                }
            }
        }
    }

    DwgWriter::write_to_file(out, &doc).map_err(|e| e.to_string())?;
    Ok(notes)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("analyze") => {
            let oracle = &args[2];
            let manifest_path = &args[3];
            let doc = DwgReader::from_file(oracle).unwrap().read_with_stats().unwrap().document;
            let mcp = args.get(4).and_then(|p| std::fs::read_to_string(p).ok()).and_then(|s| serde_json::from_str(&s).ok());
            let manifest = analyze(&doc, oracle, mcp);
            std::fs::write(manifest_path, serde_json::to_string_pretty(&manifest).unwrap()).unwrap();
            println!("gaps: {}", manifest["gaps"].as_array().map(|a| a.len()).unwrap_or(0));
            println!("families: {}", manifest["families"].as_array().map(|a| a.len()).unwrap_or(0));
        }
        Some("build") => {
            let manifest: Json = serde_json::from_str(&std::fs::read_to_string(&args[2]).unwrap()).unwrap();
            let out = std::path::Path::new(&args[3]);
            match build(&manifest, out) {
                Ok(notes) => {
                    for n in notes {
                        println!("NOTE: {n}");
                    }
                    println!("wrote {} ({} bytes)", out.display(), std::fs::metadata(out).map(|m| m.len()).unwrap_or(0));
                }
                Err(e) => {
                    eprintln!("build failed: {e}");
                    std::process::exit(1);
                }
            }
        }
        Some("detect") => {
            // Wave-1 classification probe: model-space census (all classes,
            // app-style keys) + per-alignment element-kind histogram + the
            // piece counts the manifest builder can/cannot reproduce. Read
            // only; no manifest is produced.
            let oracle = &args[2];
            let doc = DwgReader::from_file(oracle).unwrap().read_with_stats().unwrap().document;
            let c = census(&doc);
            let mut arc_kinds: BTreeMap<String, usize> = BTreeMap::new();
            let mut raw_elements: Vec<Json> = Vec::new();
            for h in all_of(&doc, "AECC_ALIGNMENT") {
                if let Some(a) = arch_of(&doc, h) {
                    let els = a.alignment_elements().unwrap_or_default();
                    raw_elements.push(serde_json::json!({ "handle": h.value(), "elements": els.len() }));
                    for e in els {
                        let k = match e.kind {
                            acadrust::classes::civil::AlignmentElementKind::FixedArc { .. } => "FixedArc",
                            acadrust::classes::civil::AlignmentElementKind::FreeArc { .. } => "FreeArc",
                            acadrust::classes::civil::AlignmentElementKind::FixedLine { .. } => "FixedLine",
                            acadrust::classes::civil::AlignmentElementKind::FreeLine => "FreeLine",
                            acadrust::classes::civil::AlignmentElementKind::FloatingArc { .. }
                            | acadrust::classes::civil::AlignmentElementKind::FloatingArcToPoint { .. }
                            | acadrust::classes::civil::AlignmentElementKind::FloatingArcFromPoint { .. } => "FloatingArc*",
                            acadrust::classes::civil::AlignmentElementKind::FloatingLine { .. }
                            | acadrust::classes::civil::AlignmentElementKind::FloatingLineFrom { .. } => "FloatingLine*",
                            acadrust::classes::civil::AlignmentElementKind::Circle { .. } => "Circle",
                            acadrust::classes::civil::AlignmentElementKind::Other { .. } => continue,
                            _ => "other",
                        };
                        *arc_kinds.entry(k.to_string()).or_default() += 1;
                    }
                    // Undecoded element types, per alignment (read gap
                    // diagnosis).
                    if let Some(els) = a.alignment_elements() {
                        let mut others: BTreeMap<String, usize> = BTreeMap::new();
                        for e in &els {
                            if let acadrust::classes::civil::AlignmentElementKind::Other { element_type, constraint } = &e.kind {
                                *others.entry(format!("{element_type}/{constraint:?}")).or_default() += 1;
                            }
                        }
                        if !others.is_empty() {
                            raw_elements.last_mut().unwrap().as_object_mut().unwrap().insert("undecoded".into(), serde_json::json!(others));
                        }
                    }
                }
            }
            let out = serde_json::json!({ "source": oracle, "census": c, "alignment_element_kinds": arc_kinds, "alignments": raw_elements });
            println!("{}", serde_json::to_string(&out).unwrap());
        }
        Some("verify") => {
            // Layer (a): decode the BUILT file with the codec and dump the
            // same analysis schema; the comparison against the manifest is
            // done by scripts/compare_verify.py (exact f64 ==).
            let built = &args[2];
            let out_path = &args[3];
            let doc = DwgReader::from_file(built).unwrap().read_with_stats().unwrap().document;
            let analysis = analyze(&doc, built, None);
            std::fs::write(out_path, serde_json::to_string_pretty(&analysis).unwrap()).unwrap();
            println!("built analysis -> {out_path}");
        }
        _ => {
            eprintln!("usage: corpus_roundtrip analyze <oracle.dwg> <manifest.json> [mcp_census.json] | build <manifest.json> <out.dwg> | verify <built.dwg> <analysis.json>");
            std::process::exit(2);
        }
    }
}
