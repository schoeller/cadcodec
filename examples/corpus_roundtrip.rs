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

use acadrust::classes::civil::{add_alignment_with_curves, add_parcel, add_profile, add_profile_view_with_range, add_sample_line, add_sample_line_group, add_section_view, add_sections, add_site, add_surface_profile, add_tin_surface, cpp_class_name, VertexCurve};
use acadrust::entities::{Circle, EntityType, Line, MText, Polyline3D, Vertex3DPolyline};
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
        EntityType::Polyline3D(_) => "AcDb3dPolyline",
        EntityType::MText(_) => "AcDbMText",
        EntityType::Text(_) => "AcDbText",
        EntityType::Insert(_) => "AcDbBlockReference",
        _ => return None,
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
    let mut circles = Vec::new();
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
            EntityType::Circle(c) => circles.push(c),
            EntityType::Line(l) => lines.push(l),
            EntityType::MText(m) => mtexts.push(m),
            EntityType::Extended(_) => {}
            other => {
                let key = native_key(other).unwrap_or("AcDbUnknown");
                *native_gaps.entry(key.to_string()).or_default() += 1;
            }
        }
    }
    if !plines.is_empty() {
        families.push(serde_json::json!({ "family": "polyline3d", "count": plines.len(), "items": plines.iter().map(|p| serde_json::json!({
            "layer": p.common.layer,
            "closed": p.flags.closed,
            "vertices": p.vertices.iter().map(|v| j3(v.position)).collect::<Vec<_>>(),
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
    // TIN surfaces: points and triangle list (the points writer rebuilds the
    // TIN; the stored triangulation itself is a parameter gap).
    let surfaces = all_of(doc, "AECC_TIN_SURFACE");
    if !surfaces.is_empty() {
        let mut items = Vec::new();
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
            }
        }
        families.push(serde_json::json!({ "family": "tin_surface", "count": surfaces.len(), "items": items }));
        // Triangulation note: the points writer retriangulates; triangle
        // identity is compared in verify and expected to differ.
        gaps.push(gap("tin_surface.triangulation", surfaces.len(), "parameter: the stored triangle list (the points writer retriangulates)", "uncertain — check whether TinOperation has a faces op"));
    }

    // Parcels: name + outline from the proxy-graphics profile (a closing
    // point repeated as the first is dropped).
    let parcels = all_of(doc, "AECC_PARCEL");
    if !parcels.is_empty() {
        let items: Vec<Json> = parcels.iter().map(|h| {
            let a = arch_of(doc, *h).unwrap();
            let (name, _alt) = a.face_name().unwrap_or_default();
            let mut outline = a.profiles.first().cloned().unwrap_or_default();
            if outline.len() > 1 && outline.first() == outline.last() {
                outline.pop();
            }
            serde_json::json!({ "name": name, "site": "", "vertices": outline.iter().map(|p| j2(Vector2::new(p.x, p.y))).collect::<Vec<_>>() })
        }).collect();
        families.push(serde_json::json!({ "family": "parcel", "count": parcels.len(), "items": items }));
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
                    // curve_radii[i] is the curve at inner vertex i+1.
                    radii_at.push(((vi - 1), 1.0 / curvature.abs()));
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

    let c = census(doc);
    serde_json::json!({
        "source": source,
        "codec_census": c,
        "mcp_census": mcp_census,
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
    for name in ["polyline3d", "circle", "line", "mtext"] {
        if let Some(f) = find(&fams, name) {
            for item in f["items"].as_array().unwrap_or(&vec![]) {
                match name {
                    "polyline3d" => {
                        let mut p = Polyline3D::new();
                        p.common.layer = item["layer"].as_str().unwrap_or("0").to_string();
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

    // Sites + parcels.
    let mut site: Option<Handle> = None;
    if let Some(f) = find(&fams, "parcel") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let s = *site.get_or_insert_with(|| add_site(&mut doc, "SITE", "").unwrap());
            let vertices: Vec<Vector2> = item["vertices"].as_array().map(|a| a.iter().map(|v| v2(v)).collect()).unwrap_or_default();
            match add_parcel(&mut doc, s, &vertices, None) {
                Ok(_) => {}
                Err(e) => notes.push(format!("parcel {}: {}", item["name"].as_str().unwrap_or("?"), e)),
            }
        }
    }

    // Surfaces.
    let mut surface_handles: Vec<Handle> = Vec::new();
    if let Some(f) = find(&fams, "tin_surface") {
        for item in f["items"].as_array().unwrap_or(&vec![]) {
            let points: Vec<Vector3> = item["points"].as_array().map(|a| a.iter().map(|v| v3(v)).collect()).unwrap_or_default();
            match add_tin_surface(&mut doc, item["name"].as_str().unwrap_or("SURF"), &points, None) {
                Ok(h) => surface_handles.push(h),
                Err(e) => notes.push(format!("tin_surface: {e}")),
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
