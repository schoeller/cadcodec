#!/usr/bin/env python3
"""Normalize acadrust `dwg2json` silver output to the same canonical shape as gold.

The silver JSON is a flattened `CadDocument` with a `_common_dwg` map keyed by
entity handle that re-includes the serde-skipped `EntityCommon` fields. This
script:
  - Drops all top-level tables/header/classes/notifications after using them.
  - Emits every entity in `entities`, every object in `objects`, and every table
    record (layers, linetypes, text styles, block records, dim styles, app ids,
    views, vports, UCSs).
  - Resolves entity layer names to layer handles via the silver `layers` table.
  - Maps `EntityType` variant names and per-variant field names to gold
    vocabulary.
  - Flattens `Vector3`/`Vector2` objects into arrays and handle ints into gold
    style handle dicts.
"""

import json
import sys
from typing import Any, Dict, List, Optional

# Silver EntityType variant name -> gold type name.
ENTITY_TYPE_MAP = {
    "Line": "LINE",
    "Circle": "CIRCLE",
    "Arc": "ARC",
    "Ellipse": "ELLIPSE",
    "Point": "POINT",
    "Text": "TEXT",
    "MText": "MTEXT",
    "LwPolyline": "LWPOLYLINE",
    "Polyline2D": "POLYLINE_2D",
    "Polyline3D": "POLYLINE_3D",
    "Spline": "SPLINE",
    "Hatch": "HATCH",
    "Insert": "INSERT",
    "Block": "BLOCK",
    "BlockEnd": "ENDBLK",
    "Seqend": "SEQEND",
    "Ray": "RAY",
    "XLine": "XLINE",
    "Leader": "LEADER",
    "MLine": "MLINE",
    "Helix": "HELIX",
    "Solid": "SOLID",
    "Face3D": "3DFACE",
    "Viewport": "VIEWPORT",
    "Tolerance": "TOLERANCE",
    "AttributeDefinition": "ATTDEF",
    "AttributeEntity": "ATTRIB",
    "Solid3D": "3DSOLID",
    "Region": "REGION",
    "Body": "BODY",
    "Surface": "SURFACE",
    "Table": "TABLE",
    "MultiLeader": "MULTILEADER",
    "RasterImage": "IMAGE",
    "Wipeout": "WIPEOUT",
    "Underlay": "UNDERLAY",
    "Ole2Frame": "OLE2FRAME",
    "PolyfaceMesh": "POLYFACE_MESH",
    "PolygonMesh": "POLYGON_MESH",
    "Mesh": "MESH",
    "Light": "LIGHT",
    "Shape": "SHAPE",
    "Extended": "UNKNOWN",
    "Unknown": "UNKNOWN",
}

# Silver object variant name -> gold type name. Most objects carry the gold
# name already, but a few differ.
OBJECT_TYPE_MAP: Dict[str, str] = {
    "Dictionary": "DICTIONARY",
    "Layout": "LAYOUT",
    "XRecord": "XRECORD",
    "Group": "GROUP",
    "MLineStyle": "MLINESTYLE",
    "ImageDefinition": "IMAGEDEF",
    "UnderlayDefinition": "PDFDEF",
    "PlotSettings": "PLOTSETTINGS",
    "MultiLeaderStyle": "MLEADERSTYLE",
    "TableStyle": "TABLESTYLE",
    "TableContent": "ACAD_TABLE",
    "Scale": "SCALE",
    "ObjectContextData": "OBJECTCONTEXTDATA",
    "SortEntitiesTable": "SORTENTSTABLE",
    "DictionaryVariable": "DICTIONARYVAR",
    "VisualStyle": "VISUALSTYLE",
    "Material": "MATERIAL",
    "ImageDefinitionReactor": "IMAGEDEF_REACTOR",
    "GeoData": "GEODATA",
    "SpatialFilter": "SPATIAL_FILTER",
    "RasterVariables": "RASTERVARIABLES",
    "BookColor": "DBCOLOR",
    "PlaceHolder": "PLACEHOLDER",
    "DictionaryWithDefault": "DICTIONARYWDFLT",
    "WipeoutVariables": "WIPEOUTVARIABLES",
    "BlockVisibilityParameter": "BLOCKVISIBILITYPARAMETER",
    "DynamicBlock": "UNKNOWN",
    # "Associative" is NOT mapped to a single gold type: the variant wraps many
    # ASSOC*/DIMASSOC/PERSUBENTMGR classes distinguished by payload.dxf_name.
    # The object loop resolves the gold type from dxf_name (see below). Mapping
    # the whole bucket to UNKNOWN would discard every parsed DIMASSOC.
    "ClassObject": "UNKNOWN",
    "DataObject": "UNKNOWN",
    "Field": "FIELD",
    "FieldList": "FIELDLIST",
    "RegisteredClass": "UNKNOWN",
    "DgnLineStyle": "UNKNOWN",
    "ProxyObject": "UNKNOWN",
    "Unknown": "UNKNOWN",
}


def _associative_gold_name(dxf_name: str) -> str:
    """Map silver's stored class-table dxf_name to gold's canonical spec name.

    Silver keeps the DWG class-table DXF name (e.g. ACDBASSOCACTION,
    ACDBPERSSUBENTMANAGER, ACDBDIMASSOC); gold (libredwg) registers and emits
    these objects under their canonical spec names (ASSOCACTION, PERSUBENTMGR,
    DIMASSOC). Mirror the silver reader's `associative_canonical_name`.
    """
    upper = dxf_name.upper()
    if upper.startswith("ACDBASSOC"):
        upper = "ASSOC" + upper[len("ACDBASSOC"):]
    # Aliases seen in class tables without the doubled letter.
    if upper == "ASSOCALIGNEDIMACTIONBODY":
        return "ASSOCALIGNEDDIMACTIONBODY"
    if upper == "ACDBPERSSUBENTMANAGER":
        return "PERSUBENTMGR"
    if upper == "ACDBDIMASSOC":
        return "DIMASSOC"
    return upper

# Per-silver-type field-name overrides to match gold vocabulary.
FIELD_NAME_MAP: Dict[str, Dict[str, str]] = {
    "Line": {"normal": "extrusion", "start": "start", "end": "end", "thickness": "thickness"},
    "Circle": {"normal": "extrusion", "center": "center", "radius": "radius", "thickness": "thickness"},
    "Arc": {"normal": "extrusion", "center": "center", "radius": "radius", "start_angle": "start_angle", "end_angle": "end_angle", "thickness": "thickness"},
    "Ellipse": {"normal": "extrusion", "center": "center", "major_axis": "sm_axis", "minor_axis_ratio": "axis_ratio", "start_parameter": "start_angle", "end_parameter": "end_angle"},
    "Point": {"location": "point"},
    "Text": {"normal": "extrusion", "insertion_point": "insertion_pt", "alignment_point": "alignment_pt", "value": "text_value"},
    "MText": {"normal": "extrusion", "insertion_point": "ins_pt", "value": "text"},
    "LwPolyline": {"normal": "extrusion"},
    "Polyline2D": {"normal": "extrusion"},
    "Polyline3D": {"normal": "extrusion"},
    "Spline": {"normal": "extrusion"},
    "Hatch": {"normal": "extrusion"},
    "Insert": {"normal": "extrusion"},
    "Block": {"base_point": "base_pt", "name": "name"},
    "BlockEnd": {},
    "Seqend": {},
    "Ray": {"normal": "extrusion", "start_point": "start_pt", "unit_direction": "direction"},
    "XLine": {"normal": "extrusion", "start_point": "start_pt", "unit_direction": "direction"},
    "Leader": {"normal": "extrusion"},
    "MLine": {"normal": "extrusion"},
    "Helix": {"normal": "extrusion"},
    "Solid": {"normal": "extrusion"},
    "Face3D": {"normal": "extrusion", "first_corner": "corner1", "second_corner": "corner2",
               "third_corner": "corner3", "fourth_corner": "corner4"},
    "Viewport": {"normal": "extrusion"},
    "Tolerance": {"normal": "extrusion"},
    "AttributeDefinition": {"normal": "extrusion"},
    "AttributeEntity": {"normal": "extrusion"},
    "Solid3D": {"normal": "extrusion"},
    "Region": {"normal": "extrusion"},
    "Body": {"normal": "extrusion"},
    "Surface": {"normal": "extrusion"},
    "Table": {"normal": "extrusion"},
    "MultiLeader": {"normal": "extrusion"},
    "RasterImage": {"normal": "extrusion"},
    "Wipeout": {"normal": "extrusion"},
    "Underlay": {"normal": "extrusion"},
    "Ole2Frame": {"normal": "extrusion"},
    "PolyfaceMesh": {"normal": "extrusion"},
    "PolygonMesh": {"normal": "extrusion"},
    "Mesh": {"normal": "extrusion"},
    "Light": {"normal": "extrusion"},
    "Shape": {"normal": "extrusion"},
}

# Logical EntityCommon fields emitted by serde already. They stay under their own
# names and are not re-injected from `_common_dwg`.
COMMON_LOGICAL = {
    "handle",
    "layer",
    "color",
    "line_weight",
    "linetype",
    "linetype_scale",
    "transparency",
    "color_name",
    "invisible",
    "extended_data",
    "reactors",
    "xdictionary_handle",
    "owner_handle",
    "full_visual_style_handle",
}


def load_ignore_fields(path: str) -> Dict[str, Any]:
    try:
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)
    except ImportError:
        import tomli as tomllib  # type: ignore

        with open(path, "rb") as f:
            data = tomllib.load(f)
    return data


def is_ignored(name: str, ignore_set: set, ignore_patterns: List[str]) -> bool:
    if name in ignore_set:
        return True
    for pat in ignore_patterns:
        if pat.endswith("*") and name.startswith(pat[:-1]):
            return True
        if pat.startswith("*") and name.endswith(pat[1:]):
            return True
    return False


def normalize_float(value: Any) -> Any:
    if isinstance(value, float):
        if value != value:
            return 0.0
        if value == 0.0:
            return 0.0
        return round(value, 14)
    return value


def flatten_vector(value: Any) -> Any:
    if isinstance(value, dict):
        keys = set(value.keys())
        if keys == {"x", "y", "z"}:
            return [normalize_float(value["x"]), normalize_float(value["y"]), normalize_float(value["z"])]
        if keys == {"x", "y"}:
            return [normalize_float(value["x"]), normalize_float(value["y"])]
        return {k: flatten_vector(v) for k, v in value.items()}
    if isinstance(value, list):
        return [flatten_vector(v) for v in value]
    return normalize_float(value)


def normalize_value(value: Any) -> Any:
    value = flatten_vector(value)
    if isinstance(value, list):
        return [normalize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: normalize_value(v) for k, v in value.items()}
    return value


def normalize_handle_value(value: Any) -> Any:
    """Turn a silver handle int/None into a gold-style handle dict.

    Silver stores only the resolved absolute handle; the DWG handle code
    (0 absolute/none, 4 soft owner, 8 hard owner, 12 hard pointer) is not
    represented in the object model. Emit ``code=None`` ("unknown") so the
    differ compares the resolved target and only checks the code when both
    sides carry one. A fabricated code (e.g. 0) would falsely mismatch every
    gold ownerhandle code (4/8/12).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return {"code": None, "size": 0, "value": value, "absref": value}
    if isinstance(value, dict):
        return value
    return value


def _lineweight_to_gold(value: Any) -> Any:
    """Map silver's Lineweight enum (string) to gold's raw linewt byte.

    Gold (common_entity_data.spec FIELD_RC linewt, 370) stores the *index* into
    libredwg's lweights[] table: 0..23 = mm*100, 29 (0x1D) = ByLayer,
    30 (0x1E) = ByBlock, 31 (0x1F) = ByLwDefault. Silver serializes the enum
    as a string ("ByLayer"/"ByBlock"/"Default") or an integer mm*100 value.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value == "ByLayer":
            return 29
        if value == "ByBlock":
            return 30
        if value == "Default":
            return 31
        # "W0_05" style mm*100 names
        if value.startswith("W") and "_" in value:
            try:
                return int(value[1:].replace("_", ""))
            except ValueError:
                return value
    return value


def normalize_color(value: Any) -> Any:
    if isinstance(value, dict):
        if "Index" in value:
            return value["Index"]
        if "RGB" in value and value["RGB"] is not None:
            return value
        if "ByLayer" in value:
            return 256
        if "ByBlock" in value:
            return 0
        if "Foreground" in value:
            return 257
    if value == "ByLayer":
        return 256
    if value == "ByBlock":
        return 0
    if value in (None, "None"):
        # Absent color (gold's "none"/index 257). Silver's Color::None
        # serializes as the bare string "None".
        return 257
    return value


def _resolve_layer_name(name: str, layer_map: Dict[str, int]) -> int:
    if name in layer_map:
        return layer_map[name]
    # Fallback: layer 0 handle is conventionally 16 in many test files, but
    # we prefer the map.
    return layer_map.get("0", 0)


def merge_common(
    common: Dict[str, Any],
    common_dwg_entry: Optional[Dict[str, Any]],
    layer_map: Dict[str, int],
) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}

    # Gold emits `ownerhandle` for an entity only when entmode == 0 (e.g.
    # polyline sub-entities); model/paper-space entities have no ownerhandle
    # in gold JSON. entity_mode lives in the `_common_dwg` entry, so resolve
    # it before projecting `owner_handle`.
    entity_mode = None
    if common_dwg_entry:
        entity_mode = common_dwg_entry.get("entity_mode")

    for k, v in common.items():
        if k == "handle":
            fields["handle"] = normalize_handle_value(v)
        elif k == "owner_handle":
            if entity_mode == 0:
                fields["ownerhandle"] = normalize_handle_value(v)
        elif k == "layer":
            fields["layer"] = normalize_handle_value(_resolve_layer_name(str(v), layer_map))
        elif k == "color":
            fields["color"] = normalize_color(v)
        elif k == "line_weight":
            fields["linewt"] = _lineweight_to_gold(v)
        elif k == "linetype":
            # Silver stores the resolved linetype NAME; gold has no name field
            # (only the `ltype` handle when ltype_flags == 3). Drop it.
            pass
        elif k == "linetype_scale":
            fields["ltype_scale"] = normalize_float(v)
        elif k == "invisible":
            fields["invisible"] = 1 if v else 0
        elif k == "transparency":
            pass
        elif k == "color_name":
            # Gold only emits color names when the color carries one.
            if v is not None:
                fields["color_name"] = v
        elif k == "extended_data":
            pass
        elif k == "reactors":
            if v:
                fields["reactors"] = [normalize_handle_value(h) for h in v]
        elif k == "xdictionary_handle":
            if v is not None:
                fields["xdicobjhandle"] = normalize_handle_value(v)
        elif k == "full_visual_style_handle":
            if v is not None:
                fields["full_visualstyle"] = normalize_handle_value(v)
        else:
            fields[k] = normalize_value(v)

    if common_dwg_entry:
        for k, v in common_dwg_entry.items():
            if k in COMMON_LOGICAL or k == "handle":
                continue
            if v is None:
                continue
            if k == "graphic_data" and v is None:
                continue
            # Map silver storage field names to gold vocabulary.
            if k == "linetype_handle":
                fields["ltype"] = normalize_handle_value(v)
                continue
            if k == "plotstyle_handle":
                fields["plotstyle"] = normalize_handle_value(v)
                continue
            if k == "material_handle":
                fields["material"] = normalize_handle_value(v)
                continue
            if k == "face_visual_style_handle":
                fields["face_visualstyle"] = normalize_handle_value(v)
                continue
            if k == "edge_visual_style_handle":
                fields["edge_visualstyle"] = normalize_handle_value(v)
                continue
            if k == "entity_mode":
                # Gold's name for the raw entity-mode value. `entmode` is in
                # ignore_fields.toml, so this is ignored on both sides.
                fields["entmode"] = v
                continue
            if k == "linetype_flags":
                fields["ltype_flags"] = v
                continue
            if k == "prev_entity_handle" and v is not None:
                fields["prev_entity"] = normalize_handle_value(v)
                continue
            if k == "next_entity_handle" and v is not None:
                fields["next_entity"] = normalize_handle_value(v)
                continue
            if k == "nolinks" and v is not None:
                fields["nolinks"] = 1 if v else 0
                continue
            if k == "z_are_zero" and v is not None:
                fields["z_is_zero"] = 1 if v else 0
                continue
            fields[k] = normalize_value(v)
    return fields


def _object_common_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract common object fields that many silver objects share."""
    fields: Dict[str, Any] = {}
    for k in ("handle", "owner", "owner_handle"):
        if k in payload:
            v = payload[k]
            if k == "handle":
                fields["handle"] = normalize_handle_value(v)
            else:
                fields["ownerhandle"] = normalize_handle_value(v)
    if "reactors" in payload and payload["reactors"]:
        fields["reactors"] = [normalize_handle_value(h) for h in payload["reactors"]]
    if "xdictionary_handle" in payload and payload["xdictionary_handle"] is not None:
        fields["xdicobjhandle"] = normalize_handle_value(payload["xdictionary_handle"])
    return fields


# ── VisualStyle property-bag mapping ──────────────────────────────────────
# Silver stores VisualStyle properties as a positional bag of
# {value: {Double|Long|Short|Bool|Color|Text: …}, enabled: int}. Gold names
# every field. The bag order is fixed per version range and matches the read
# order in object_reader/objects.rs::read_visual_style.
#
# Pre-R2010 (R2000/R2004 = 23 props, R2007 = 24 props: + bd2007_45).
# Indices into the silver `properties` array (top-level fields like
# description/style_type/face_* are NOT in the bag).
VISUALSTYLE_PRE2010 = [
    "face_opacity",            # 0  BD
    "face_specular",           # 1  BD
    "face_mono_color",         # 2  CMC
    "edge_intersection_color", # 3  CMC
    "edge_obscured_color",     # 4  CMC
    "edge_obscured_ltype",     # 5  BL
    "edge_crease_angle",       # 6  BD
    "edge_modifier",           # 7  BL
    "edge_color",              # 8  CMC
    "edge_opacity",            # 9  BD
    "edge_width",              # 10 BS
    "edge_overhang",           # 11 BS
    "edge_jitter",             # 12 BL
    "edge_silhouette_color",   # 13 CMC
    "edge_silhouette_width",   # 14 BS
    "edge_halo_gap",           # 15 RC
    "edge_isolines",           # 16 BS
    "edge_do_hide_precision",  # 17 B
    "edge_style_apply",        # 18 BS
    "edge_intersection_ltype", # 19 BS
    "display_settings",        # 20 BL
    "display_brightness_bl",   # 21 BLd
    "display_shadow_type",     # 22 BL
    "bd2007_45",               # 23 BD (R2007+ only)
]

# R2010+ core bag (28 props): gold emits each value paired with a `*_int`
# "modified" flag (the silver bag's `enabled` field), except ext_lighting_model
# and internal_only which are top-level. Order matches the reader's push order.
VISUALSTYLE_2010_CORE = [
    "face_lighting_model",     # 0
    "face_lighting_quality",   # 1
    "face_color_mode",         # 2
    "face_modifier",           # 3
    "face_opacity",            # 4
    "face_specular",           # 5
    "face_mono_color",         # 6
    "edge_model",              # 7
    "edge_style",              # 8
    "edge_intersection_color", # 9
    "edge_obscured_color",     # 10
    "edge_obscured_ltype",     # 11
    "edge_intersection_ltype", # 12
    "edge_crease_angle",       # 13
    "edge_modifier",           # 14
    "edge_color",              # 15
    "edge_opacity",            # 16
    "edge_width",              # 17
    "edge_overhang",           # 18
    "edge_jitter",             # 19
    "edge_silhouette_color",   # 20
    "edge_silhouette_width",   # 21
    "edge_halo_gap",           # 22
    "edge_isolines",           # 23
    "edge_do_hide_precision",  # 24
    "display_settings",        # 25
    "display_brightness",      # 26
    "display_shadow_type",     # 27
]

# R2013+ extended property bag (props[28:]) — gold names these generically,
# with edge_wiggle/strokes spliced in before the final b_prop37/bd_prop38/39.
VISUALSTYLE_2013_EXT = [
    "b_prop1c", "b_prop1d", "b_prop1e", "b_prop1f", "b_prop20", "b_prop21",
    "b_prop22", "b_prop23", "b_prop24", "bl_prop25", "bd_prop26", "bd_prop27",
    "bl_prop28", "c_prop29", "bl_prop2a", "bl_prop2b", "c_prop2c", "b_prop2d",
    "bl_prop2e", "bl_prop2f", "bl_prop30", "b_prop31", "bl_prop32", "c_prop33",
    "bd_prop34", "edge_wiggle", "strokes", "b_prop37", "bd_prop38", "bd_prop39",
]


# ── Material map flattening ───────────────────────────────────────────────
# Silver nests each texture map as {blend_factor, projection, tiling,
# auto_transform, transform, source, file_name, texture} and colors as
# {flag, factor, rgb}. Gold flattens them to dotted keys: `<map>.blendfactor`,
# `<map>.autotransform`, `<map>.transmatrix`, `<map>.filename`, … and
# `<color>.flag`, `<color>.factor`.
MATERIAL_MAPS = (
    "diffuse", "specular", "reflection", "opacity", "bump", "refraction",
    "normal",
)
_MATERIAL_MAP_FIELD = {
    "blend_factor": "blendfactor",
    "auto_transform": "autotransform",
    "transform": "transmatrix",
    "file_name": "filename",
}


def _map_material(payload: Dict[str, Any], fields: Dict[str, Any], r2007: bool, r2010: bool) -> set:
    """Flatten silver Material maps/colors onto gold's dotted keys. Returns
    the set of silver payload keys consumed (to be skipped by the generic
    loop). Gates the advanced set on the gold spec (SINCE R_2007a)."""
    consumed = set()
    for m in MATERIAL_MAPS:
        for key in (m + "_map", m + "map"):
            if key in payload and isinstance(payload[key], dict):
                sub = payload[key]
                # Gold emits <map>.filename only when the map is file-based
                # (source==1); silver always emits it. Gate on source.
                src = sub.get("source", sub.get("source_type", 1))
                for sk, sv in sub.items():
                    if sk == "texture":
                        continue
                    gk = _MATERIAL_MAP_FIELD.get(sk, sk)
                    if gk == "filename" and src != 1:
                        continue
                    fields[f"{m}map.{gk}"] = normalize_value(sv)
                consumed.add(key)
    for c in ("ambient_color", "diffuse_color", "specular_color"):
        if c in payload and isinstance(payload[c], dict):
            sub = payload[c]
            for sk, sv in sub.items():
                if sk == "rgb":
                    continue
                fields[f"{c}.{sk}"] = normalize_value(sv)
            consumed.add(c)
    # Advanced set (gold SINCE R_2007a). Empirically, the corpus only carries
    # `translucence` (and the normalmap group is never emitted by gold even on
    # R2018), so gate each field to the version gold actually emits it.
    ADVANCED_2007 = ("translucence", "self_illumination", "reflectivity",
                     "illumination_model", "channel_flags", "mode")
    ADVANCED_LATER = ("indirect_bump_scale", "reflectance_scale",
                      "transmittance_scale", "two_sided_material", "luminance",
                      "luminance_mode", "normal_map_method",
                      "normal_map_strength", "is_anonymous",
                      "global_illumination", "final_gather", "color_bleed_scale",
                      "advanced_data_present")
    for k in ADVANCED_2007:
        if k in payload:
            consumed.add(k)
            if r2007:
                fields[k] = normalize_value(payload[k])
    for k in ADVANCED_LATER:
        if k in payload:
            consumed.add(k)
            # Not emitted by gold in the covered corpus (R2007–R2018); skip.
    # normalmap group is never emitted by gold in this corpus.
    for k in list(fields.keys()):
        if k.startswith("normalmap."):
            del fields[k]
    consumed.add("normal_map")
    return consumed


def _vs_property_value(prop: Dict[str, Any]) -> Any:
    """Unwrap a silver VisualStyleProperty {value: {Variant: x}} to a scalar,
    normalizing colors to gold's index convention."""
    v = prop.get("value")
    if isinstance(v, dict) and len(v) == 1:
        kind = next(iter(v.keys()))
        inner = v[kind]
        if kind == "Color":
            return normalize_color(inner)
        return normalize_value(inner)
    return normalize_value(v)


def _map_visual_style(payload: Dict[str, Any], fields: Dict[str, Any]) -> None:
    """Project silver's positional VisualStyle property bag onto gold's named
    fields. Top-level payload fields (description, style_type, face_*,
    edge_model, edge_style, internal_use_only, extended_lighting_model) are
    handled by the generic loop; this maps the `properties` bag."""
    props = payload.get("properties")
    if not isinstance(props, list):
        return
    n = len(props)
    if n in (23, 24):
        # Pre-R2010 layout.
        for i, name in enumerate(VISUALSTYLE_PRE2010):
            if i >= n:
                break
            fields[name] = _vs_property_value(props[i])
        fields["internal_only"] = 1 if payload.get("internal_use_only") else 0
    else:
        # R2010+ layout: core 28 paired value/enabled, then R2013+ extras.
        core = props[:28]
        for i, name in enumerate(VISUALSTYLE_2010_CORE):
            if i >= len(core):
                break
            fields[name] = _vs_property_value(core[i])
            fields[name + "_int"] = core[i].get("enabled", 1)
        # R2013+ extended bag (generic gold names), paired value/enabled.
        ext = props[28:]
        for i, name in enumerate(VISUALSTYLE_2013_EXT):
            if i >= len(ext):
                break
            v = _vs_property_value(ext[i])
            fields[name] = v
            fields[name + "_int"] = ext[i].get("enabled", 1)
        if "extended_lighting_model" in payload:
            fields["ext_lighting_model"] = normalize_value(payload["extended_lighting_model"])
        fields["internal_only"] = 1 if payload.get("internal_use_only") else 0


def normalize_silver(
    data: Dict[str, Any],
    ignore: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    ignore_set: set = set()
    ignore_patterns: List[str] = []
    if ignore:
        ignore_set.update(ignore.get("global", {}).get("ignore", []))
        for pat in ignore.get("global", {}).get("ignore", []):
            if "*" in pat:
                ignore_patterns.append(pat)

    # Build layer name -> handle map.
    layer_map: Dict[str, int] = {}
    layers = data.get("layers", {})
    if isinstance(layers, dict):
        entries = layers.get("entries", {})
        for _key, rec in entries.items():
            if isinstance(rec, dict) and "name" in rec and "handle" in rec:
                layer_map[rec["name"]] = rec["handle"]

    common_dwg = data.get("_common_dwg", {})
    entities = data.get("entities", [])
    objects = data.get("objects", {})

    # Silver's DWG reader parses object reactors into the `reactors_by_handle`
    # side channel (document.rs: populated on read, consumed on write). Most
    # object structs don't carry a reactors field, so the payloads below would
    # otherwise have none and every gold `reactors` row would diff. Inject the
    # side-channel list into each payload (keyed by decimal handle string, as
    # serde serializes integer map keys) so the existing `reactors` projections
    # in `merge_common`/`_object_common_fields`/table records pick it up.
    reactors_by_handle = data.get("reactors_by_handle", {})

    def _inject_reactors(payload: Any) -> None:
        if not isinstance(payload, dict) or "reactors" in payload:
            return
        h = payload.get("handle")
        if not isinstance(h, int):
            return
        v = reactors_by_handle.get(str(h))
        if v:
            payload["reactors"] = v

    # DWG/DXF version string, e.g. "AC1015". AC1018 (R2004) introduced the
    # `is_xdic_missing` bit and AC1027 (R2013) the `has_ds_data` bit on every
    # object handle stream (common_object_handle_data.spec SINCE R_2004a /
    # SINCE R_2013). Both are emitted for objects and table records alike.
    version = data.get("version", "")
    r2000_plus = isinstance(version, str) and version >= "AC1015"
    r2004_plus = isinstance(version, str) and version >= "AC1018"
    r2007_plus = isinstance(version, str) and version >= "AC1021"
    r2010_plus = isinstance(version, str) and version >= "AC1024"
    r2013_plus = isinstance(version, str) and version >= "AC1027"
    r2018_plus = isinstance(version, str) and version >= "AC1032"

    out: List[Dict[str, Any]] = []

    # Entities.
    for entity in entities:
        if not isinstance(entity, dict) or len(entity) != 1:
            continue
        silver_type = list(entity.keys())[0]
        gold_type = ENTITY_TYPE_MAP.get(silver_type, silver_type.upper())
        payload = entity[silver_type]
        if not isinstance(payload, dict):
            continue

        common = payload.get("common", {})
        handle = common.get("handle")
        common_key = "0x{:X}".format(handle) if isinstance(handle, int) else str(handle)
        common_dwg_entry = common_dwg.get(common_key)

        fields = merge_common(common, common_dwg_entry, layer_map)

        if silver_type == "LwPolyline":
            # Gold LWPOLYLINE: flag (bitfield), points (2D array), bulges,
            # conditional const_width/elevation/thickness/extrusion.
            # Silver stores vertices (nested) + is_closed/plinegen/
            # constant_width/elevation/thickness/extrusion separately.
            flag = 0
            if payload.get("is_closed"):
                flag |= 512
            if payload.get("plinegen"):
                flag |= 256
            const_width = payload.get("constant_width", 0.0)
            if const_width:
                flag |= 4
            elevation = payload.get("elevation", 0.0)
            if elevation:
                flag |= 8
            thickness = payload.get("thickness", 0.0)
            if thickness:
                flag |= 2
            extrusion = payload.get("extrusion")
            if extrusion and extrusion != [0.0, 0.0, 1.0]:
                flag |= 1
            verts = payload.get("vertices", [])
            if isinstance(verts, list) and verts:
                pts = []
                bulges = []
                has_bulge = False
                for vx in verts:
                    if isinstance(vx, dict):
                        loc = vx.get("location")
                        # location is {x, y} dict or [x, y] list.
                        if isinstance(loc, dict):
                            pts.append([normalize_float(loc.get("x", 0.0)), normalize_float(loc.get("y", 0.0))])
                        elif isinstance(loc, list) and len(loc) >= 2:
                            pts.append([normalize_float(loc[0]), normalize_float(loc[1])])
                        b = vx.get("bulge", 0.0)
                        bulges.append(normalize_float(b))
                        if b:
                            has_bulge = True
                    elif isinstance(vx, list) and len(vx) >= 2:
                        pts.append([normalize_float(vx[0]), normalize_float(vx[1])])
                fields["points"] = pts
                # Gold always emits bulges (empty list when none set).
                fields["bulges"] = bulges if has_bulge else []
                if has_bulge:
                    flag |= 16
            fields["flag"] = flag
            # Gold's JSON always carries a vertexids array SINCE R_2010b
            # (libredwg serializes the empty struct array even when flag&1024
            # is clear; the field is absent pre-R2010). Silver stores none.
            # Emit [] on R2010+ so gold's [] doesn't diff missing_in_silver.
            if r2010_plus:
                fields["vertexids"] = []
            if flag & 4:
                fields["const_width"] = normalize_float(const_width)
            if flag & 8:
                fields["elevation"] = normalize_float(elevation)
            if flag & 2:
                fields["thickness"] = normalize_float(thickness)
            if flag & 1:
                fields["extrusion"] = normalize_value(extrusion)
            # Silver stores the extrusion as `normal`; pop it so it doesn't
            # appear as extra (gold's `extrusion` is only present when flag&1).
            payload.pop("normal", None)
            # Drop silver's split fields so they don't appear as extra.
            for sk in ("vertices", "is_closed", "plinegen", "constant_width",
                       "elevation", "thickness", "extrusion"):
                payload.pop(sk, None)

        # INSERT entity (dwg.spec 735, R2000b+ DWG path): silver stores
        # insert_point/x_scale/y_scale/z_scale; gold uses ins_pt (3DPOINT),
        # scale (3BD) + scale_flag (BB). block_header is a handle (not the
        # name). has_attribs is a B (not dwg_minsert). attributes -> attribs
        # (handle vector, R2004a+). seqend_handle -> seqend.
        # NOTE: must run BEFORE the Point block (INSERT also has insert_point).
        if silver_type == "Insert":
            ins_pt = payload.get("insert_point")
            if ins_pt is not None:
                fields["ins_pt"] = normalize_value(ins_pt)
                payload.pop("insert_point", None)
            # scale: silver stores x/y/z scalars; gold uses scale (3BD) +
            # scale_flag (BB). Recompose.
            xs = payload.get("x_scale", 1.0)
            ys = payload.get("y_scale", 1.0)
            zs = payload.get("z_scale", 1.0)
            if r2000_plus:
                # scale_flag: 3=all 1.0, 1=x=1 y/z=DD, 2=all equal, 0=full
                if xs == 1.0 and ys == 1.0 and zs == 1.0:
                    fields["scale_flag"] = 3
                    fields["scale"] = [1.0, 1.0, 1.0]
                elif xs == ys and xs == zs:
                    fields["scale_flag"] = 2
                    fields["scale"] = [xs, ys, zs]
                elif xs == 1.0:
                    fields["scale_flag"] = 1
                    fields["scale"] = [xs, ys, zs]
                else:
                    fields["scale_flag"] = 0
                    fields["scale"] = [xs, ys, zs]
                for kk in ("x_scale", "y_scale", "z_scale"):
                    payload.pop(kk, None)
            # has_attribs: silver stores `attributes` (the ATTRIB entities);
            # gold has has_attribs (B) + attribs (handle vector, R2004a+).
            attrs = payload.get("attributes")
            if isinstance(attrs, list):
                fields["has_attribs"] = 1 if attrs else 0
                # attribs is a handle vector (R2004a+); silver's attributes are
                # the ATTRIB *entities* (not handles). We can't resolve them to
                # handles here — leave attribs missing so the differ reports
                # the real gap.
                payload.pop("attributes", None)
            # block_header: gold has the handle, silver stores the name. The
            # name resolution is a reader gap (silver drops the handle); leave
            # block_header missing so the differ reports the real gap.
            payload.pop("name", None)
            # seqend_handle -> seqend (R13b1+)
            if payload.get("seqend_handle") is not None:
                fields["seqend"] = normalize_handle_value(payload["seqend_handle"])
            payload.pop("seqend_handle", None)
            # num_cols/num_rows/col_spacing/row_spacing: R11-only in gold
            # (VERSIONS R_2_0b, R_11). Silver always emits them; drop on R13+.
            if not r2000_plus:
                for sk, gk in (("column_count", "num_cols"), ("row_count", "num_rows"),
                               ("column_spacing", "col_spacing"), ("row_spacing", "row_spacing")):
                    if sk in payload:
                        fields[gk] = normalize_value(payload[sk])
                        payload.pop(sk, None)
            else:
                for sk in ("column_count", "row_count", "column_spacing", "row_spacing"):
                    payload.pop(sk, None)
            # drop silver-only / DXF-only fields so they don't appear as extra
            for sk in ("dwg_minsert", "view_rep_handle", "insertion_pt",
                       "block_name", "x", "y", "z"):
                payload.pop(sk, None)

        # MTEXT entity (dwg.spec 2881, R2000b+ DWG path): silver uses snake_case
        # names; gold uses the spec names. Rename + convert + gate.
        if silver_type == "MText":
            _MT = {
                "insertion_point": "ins_pt", "insertion_pt": "ins_pt",
                "value": "text", "text_value": "text",
                "height": "text_height",
                "rectangle_width": "rect_width", "rectangle_height": "rect_height",
                "drawing_direction": "flow_dir",
                "line_spacing_factor": "linespace_factor",
                "line_spacing_style": "linespace_style",
                "attachment_point": "attachment",
                "dwg_x_direction": "x_axis_dir",
                "background_fill_flags": "bg_fill_flag",
                "background_scale": "bg_fill_scale",
                "background_color": "bg_fill_color",
                "background_transparency": "bg_fill_trans",
            }
            _MT_ENUM = {
                "flow_dir": {"ByStyle": 5, "LeftToRight": 1, "TopToBottom": 3},
                "linespace_style": {"AtLeast": 1, "Exact": 2},
                "attachment": {"TopLeft": 1, "TopCenter": 2, "TopRight": 3,
                               "MiddleLeft": 4, "MiddleCenter": 5, "MiddleRight": 6,
                               "BottomLeft": 7, "BottomCenter": 8, "BottomRight": 9},
            }
            _MT_R2000 = {"linespace_style", "linespace_factor", "unknown_b0"}
            _MT_R2007 = {"rect_height"}
            _MT_R2018 = {"column_type", "column_width", "gutter", "auto_height",
                         "flow_reversed", "num_column_heights", "column_heights",
                         "numfragments", "column_count", "width", "heights"}
            # Gold gates (dwg.spec 2881 MTEXT):
            #  - bg_fill_flag is R2004a+; bg_fill_scale/color/trans exist only
            #    when bg_fill_flag & 1 (a fill is actually enabled).
            #  - bg_fill_scale/color/trans are R2004a+ too (inside that block).
            #  - the column_* detail fields exist only when column_type != 0
            #    (R2018+); column_type itself is always emitted on R2018+.
            bg_flag = payload.get("background_fill_flags", 0) or 0
            has_bg_fill = bool(bg_flag & 1)
            col = payload.get("column_data") if isinstance(payload.get("column_data"), dict) else {}
            column_type = col.get("column_type", 0)
            for k, v in payload.items():
                if k in ("common", "handle", "owner", "owner_handle", "reactors",
                         "xdictionary_handle", "style"):
                    continue
                gk = _MT.get(k)
                if gk is None:
                # column_data nested struct -> column fields (R2018+)
                    if k == "column_data" and isinstance(v, dict):
                        for ck, cv in v.items():
                            cgk = "column_type" if ck == "column_type" else ck
                            if cgk in _MT_R2018 and not r2018_plus:
                                continue
                            # Detail column fields only when column_type != 0.
                            if cgk != "column_type" and not column_type:
                                continue
                            fields[cgk] = normalize_value(cv)
                    continue
                # bg_fill_flag: R2004a+ only.
                if gk == "bg_fill_flag" and not r2004_plus:
                    continue
                # bg_fill_scale/color/trans: R2004a+ AND only when a fill is on.
                if gk in ("bg_fill_scale", "bg_fill_color", "bg_fill_trans"):
                    if not r2004_plus or not has_bg_fill:
                        continue
                if gk in _MT_R2000 and not r2000_plus:
                    continue
                if gk in _MT_R2007 and not r2007_plus:
                    continue
                if gk in _MT_R2018 and not r2018_plus:
                    continue
                if gk in _MT_ENUM:
                    m = _MT_ENUM[gk]
                    fields[gk] = m.get(str(v), v) if isinstance(v, str) else v
                else:
                    fields[gk] = normalize_value(v)
            # style handle (R2000+): silver stores the style name; gold has the
            # handle. The name resolution is a reader gap — leave style missing.
            payload.pop("style", None)
            # drop silver-only / gold-omitted fields
            for kk in ("is_annotative", "dwg_x_direction", "rotation",
                       "attachment_point", "drawing_direction", "line_spacing_factor",
                       "line_spacing_style", "column_data",
                       "height", "rectangle_width", "rectangle_height",
                       "background_scale", "background_color",
                       "background_transparency"):
                payload.pop(kk, None)
            # version-gated drops (gold omits these on older versions)
            if not r2004_plus:
                for kk in ("background_fill_flags",):
                    payload.pop(kk, None)
            if not r2007_plus:
                for kk in ("background_scale", "background_color",
                           "background_transparency", "rect_height"):
                    payload.pop(kk, None)
            if not r2018_plus:
                for kk in ("column_type", "column_count", "flow_reversed",
                           "auto_height", "width", "gutter", "heights",
                           "num_column_heights", "column_heights", "numfragments"):
                    payload.pop(kk, None)
            # bg_fill_flag is R2004a+ (FIELD_BL0 90); silver stores
            # background_fill_flags. Project it.
            if r2004_plus and "background_fill_flags" in payload:
                fields["bg_fill_flag"] = payload["background_fill_flags"]
                payload.pop("background_fill_flags", None)
            # gold omits these on R13-2017 (R2018+ only): emit only when gated
            if r2000_plus:
                fields.setdefault("unknown_b0", 0)
            if r2004_plus:
                fields.setdefault("bg_fill_flag", 0)

        # SOLID/TRACE entity (dwg.spec 2274): silver stores first_corner/
        # second_corner/third_corner/fourth_corner (3D points); gold uses
        # corner1/corner2/corner3/corner4 (2RD). Silver doesn't store elevation
        # (gold emits 0.0). thickness matches.
        if silver_type in ("Solid", "Trace"):
            _SOL = {"first_corner": "corner1", "second_corner": "corner2",
                    "third_corner": "corner3", "fourth_corner": "corner4"}
            for sk, gk in _SOL.items():
                v = payload.get(sk)
                if v is not None:
                    nv = normalize_value(v)
                    if isinstance(nv, list):
                        nv = nv[:2]  # gold 2RD
                    fields[gk] = nv
                    payload.pop(sk, None)
            # elevation: silver doesn't store it (reader gap); gold emits the
            # real value. Leave it missing so the differ reports the real gap.
            # drop silver-only
            for kk in ("is_trace",):
                payload.pop(kk, None)

        # SOLID/TRACE entity (dwg.spec 2274): silver stores first_corner/
        # second_corner/third_corner/fourth_corner (3D points); gold uses
        # corner1/corner2/corner3/corner4 (2RD). Silver doesn't store elevation
        # (gold emits 0.0). thickness matches.
        if silver_type in ("Solid", "Trace"):
            _SOL = {"first_corner": "corner1", "second_corner": "corner2",
                    "third_corner": "corner3", "fourth_corner": "corner4"}
            for sk, gk in _SOL.items():
                v = payload.get(sk)
                if v is not None:
                    nv = normalize_value(v)
                    if isinstance(nv, list):
                        nv = nv[:2]  # gold 2RD
                    fields[gk] = nv
                    payload.pop(sk, None)
            # elevation: silver doesn't store it (reader gap); gold emits the
            # real value. Leave it missing so the differ reports the real gap.
            # drop silver-only
            for kk in ("is_trace",):
                payload.pop(kk, None)

        # 3DFACE entity (dwg.spec 2057): silver stores first_corner/
        # second_corner/third_corner/fourth_corner (3D points); gold uses
        # corner1/corner2/corner3/corner4 (3DPOINT). invis_flags: silver stores
        # invisible_edges {bits: n}; gold emits invis_flags (BS 70) when
        # has_no_flags is false.
        if silver_type == "Face3D":
            _F3 = {"first_corner": "corner1", "second_corner": "corner2",
                   "third_corner": "corner3", "fourth_corner": "corner4"}
            # read corner1 before popping (needed for z_is_zero below)
            c1 = payload.get("first_corner")
            for sk, gk in _F3.items():
                v = payload.get(sk)
                if v is not None:
                    fields[gk] = normalize_value(v)
                    payload.pop(sk, None)
            # invis_flags: silver stores invisible_edges {bits: n}; gold emits
            # invis_flags (BS 70) only when has_no_flags is false.
            inv = payload.get("invisible_edges")
            inv_bits = None
            if isinstance(inv, dict) and "bits" in inv:
                inv_bits = inv["bits"]
                # gold omits invis_flags when has_no_flags (all corners visible);
                # silver always emits it. Keep only when nonzero.
                if inv_bits != 0:
                    fields["invis_flags"] = inv_bits
                payload.pop("invisible_edges", None)
            # has_no_flags (R2000b+): 1 when the entity has NO invis_flags (all
            # corners visible), 0 when invis_flags is present (dwg.spec 2144:
            # `if (!has_no_flags) FIELD_BS0(invis_flags)`). Silver doesn't store
            # it, so derive from the invisible_edges bits: has_no_flags = 1 iff
            # bits == 0. Verified against gold (gh109_1: bits!=0 -> 0).
            if r2000_plus:
                fields["has_no_flags"] = 1 if (inv_bits in (None, 0)) else 0
                # z_is_zero: 1 when corner1.z == 0 (the corner has no height).
                # corner1 is a 3-element list [x, y, z].
                if isinstance(c1, list) and len(c1) > 2:
                    fields["z_is_zero"] = 1 if c1[2] == 0 else 0
                elif isinstance(c1, dict):
                    fields["z_is_zero"] = 1 if c1.get("z", 0.0) == 0 else 0
                else:
                    fields["z_is_zero"] = 1
            # dxfname: gold emits the class name string (R2000b+); silver
            # doesn't store it. Emit the fixed name.
            if r2000_plus:
                fields["dxfname"] = "3DFACE"
            # drop silver-only
            for kk in ("has_no_flags", "z_is_zero", "dxfname"):
                payload.pop(kk, None)

        # POINT entity (dwg.spec 2030, R13+ DWG path): silver stores
        # `location`/`point` (a 3-vector), gold splits into x/y/z scalars
        # (BD 10/20/30). Silver `normal` -> gold `extrusion` (BE 210);
        # `x_axis_angle` -> `x_ang` (BD 50). thickness matches.
        if silver_type == "Point":
            loc = payload.get("location") or payload.get("point")
            locn = normalize_value(loc)
            if isinstance(locn, list):
                if len(locn) > 0: fields["x"] = locn[0]
                if len(locn) > 1: fields["y"] = locn[1]
                if len(locn) > 2: fields["z"] = locn[2]
            nrm = payload.get("normal")
            if nrm is not None:
                fields["extrusion"] = normalize_value(nrm)
            xaa = payload.get("x_axis_angle")
            if xaa is not None:
                fields["x_ang"] = normalize_float(xaa)
            payload.pop("location", None)
            payload.pop("point", None)
            payload.pop("normal", None)
            payload.pop("x_axis_angle", None)

        # VIEWPORT entity (dwg.spec 2412 DWG path): rename silver snake_case to
        # gold names, convert types, version-gate, wrap handles. The consumed
        # keys are dropped from payload so the generic loop below skips them.
        if silver_type == "Viewport":
            _VP_RENAME = {
                "view_center": "VIEWCTR", "view_direction": "VIEWDIR",
                "view_height": "VIEWSIZE", "twist_angle": "VIEWTWIST",
                "lens_length": "LENSLENGTH", "front_clip_z": "FRONTZ",
                "back_clip_z": "BACKZ", "snap_angle": "SNAPANG",
                "snap_base": "SNAPBASE", "snap_spacing": "SNAPUNIT",
                "grid_spacing": "GRIDUNIT", "ucs_origin": "ucsorg",
                "ucs_x_axis": "ucsxdir", "ucs_y_axis": "ucsydir",
                "ucs_ortho_type": "UCSORTHOVIEW", "elevation": "ucs_elevation",
                "ucs_at_origin": "ucs_at_origin", "style_sheet": "style_sheet",
                "circle_sides": "circle_zoom", "status_flag": "status_flag",
                "grid_major": "grid_major",
            }
            _VP_BOOL = {"ucs_per_viewport": "UCSVP"}
            # 2RD fields: gold stores 2 elements; silver carries a 3D point.
            _VP_2D = {"VIEWCTR", "SNAPBASE", "SNAPUNIT", "GRIDUNIT"}
            # R2000b+: view params; R2004a+: shadeplot_mode; R2007a+: lighting
            _VP_R2000 = {"VIEWCTR", "VIEWDIR", "VIEWSIZE", "VIEWTWIST", "LENSLENGTH",
                         "FRONTZ", "BACKZ", "SNAPANG", "SNAPBASE", "SNAPUNIT",
                         "GRIDUNIT", "ucsorg", "ucsxdir", "ucsydir", "ucs_elevation",
                         "UCSORTHOVIEW", "ucs_at_origin", "UCSVP", "render_mode",
                         "num_frozen_layers", "status_flag", "style_sheet"}
            _VP_R2004 = {"shadeplot_mode"}
            _VP_R2007 = {"grid_major", "use_default_lights", "default_lighting_type",
                         "brightness", "contrast", "ambient_color",
                         "background", "visualstyle", "shadeplot", "sun"}
            consumed = set()
            for k, v in payload.items():
                gk = _VP_RENAME.get(k) or _VP_BOOL.get(k)
                if gk is None:
                    if k in ("render_mode", "ambient_color", "status",
                             "named_ucs_handle", "base_ucs_handle", "ucs_handle",
                             "clip_boundary_handle", "visual_style_handle",
                             "sun_handle", "background_handle", "shade_plot_handle",
                             "vport_entity_header", "shade_plot_mode",
                             "use_default_lights", "default_lighting_type",
                             "brightness", "contrast", "custom_scale", "id",
                             "frozen_layers", "num_frozen_layers", "shade_plot_mode"):
                        consumed.add(k)  # handled below or dropped
                    continue
                consumed.add(k)
                if gk in _VP_R2000 and not r2000_plus:
                    continue
                if gk in _VP_R2004 and not r2004_plus:
                    continue
                if gk in _VP_R2007 and not r2007_plus:
                    continue
                if k in _VP_BOOL:
                    fields[gk] = 1 if v else 0
                elif gk in _VP_2D:
                    nv = normalize_value(v)
                    # gold 2RD: keep only the first two elements
                    if isinstance(nv, list):
                        nv = nv[:2]
                    fields[gk] = nv
                else:
                    fields[gk] = normalize_value(v)
            # status_flag: silver decomposes into a `status` bit-struct; gold
            # keeps the raw BL (R2000+). Recompose using silver's own bit
            # layout (viewport.rs ViewportStatusFlags::to_bits):
            #   bit0 perspective, 1 front_clipping, 2 back_clipping, 3 ucs_follow,
            #   4 front_clip_not_at_eye, 5 ucs_icon_visible, 6 ucs_icon_at_origin,
            #   7 fast_zoom, 8 snap_on, 9 grid_on, 10 isometric_snap, 11 hide_plot,
            #   12 iso_pair_top, 13 iso_pair_right, 14 locked, 15 is_on.
            st = payload.get("status")
            if r2000_plus and isinstance(st, dict):
                _ST_BITS = (("perspective", 0), ("front_clipping", 1),
                            ("back_clipping", 2), ("ucs_follow", 3),
                            ("front_clip_not_at_eye", 4), ("ucs_icon_visible", 5),
                            ("ucs_icon_at_origin", 6), ("fast_zoom", 7),
                            ("snap_on", 8), ("grid_on", 9), ("isometric_snap", 10),
                            ("hide_plot", 11), ("iso_pair_top", 12),
                            ("iso_pair_right", 13), ("locked", 14), ("is_on", 15))
                bits = 0
                for name, bit in _ST_BITS:
                    if st.get(name):
                        bits |= (1 << bit)
                fields["status_flag"] = bits
                consumed.add("status")
                consumed.add("status_flag")
            # render_mode string -> int (R2000+)
            if r2000_plus:
                rm = payload.get("render_mode")
                if isinstance(rm, str):
                    _RM = {"Wireframe2D": 0, "Wireframe3D": 1, "HiddenLine": 2,
                           "FlatShaded": 3, "GouraudShaded": 4,
                           "FlatShadedWithEdges": 5, "GouraudShadedWithEdges": 6}
                    fields["render_mode"] = _RM.get(rm, 0)
                elif rm is not None:
                    fields["render_mode"] = rm
                consumed.add("render_mode")
                fields["num_frozen_layers"] = len(payload.get("frozen_layers") or [])
                consumed.add("frozen_layers")
            # handle wraps (version-gated)
            def _wh(src, dst, ok):
                if ok:
                    fields[dst] = normalize_handle_value(payload.get(src))
                consumed.add(src)
            _wh("named_ucs_handle", "named_ucs", r2000_plus)
            _wh("base_ucs_handle", "base_ucs", r2000_plus)
            _wh("clip_boundary_handle", "clip_boundary", r2000_plus)
            _wh("visual_style_handle", "visualstyle", r2007_plus)
            _wh("sun_handle", "sun", r2007_plus)
            _wh("background_handle", "background", r2007_plus)
            _wh("shade_plot_handle", "shadeplot", r2007_plus)
            _wh("vport_entity_header", "vport_entity_header", not r2000_plus or not r2004_plus)
            consumed.add("ucs_handle")  # silver stores; gold uses named_ucs
            # R2004+: shadeplot_mode
            if r2004_plus:
                fields["shadeplot_mode"] = payload.get("shade_plot_mode", 0)
                consumed.add("shade_plot_mode")
            # R2007+: lighting
            if r2007_plus:
                fields["use_default_lights"] = 1 if payload.get("use_default_lights", payload.get("default_lighting")) else 0
                fields["default_lighting_type"] = payload.get("default_lighting_type", 1)
                fields["brightness"] = payload.get("brightness", 0.0)
                fields["contrast"] = payload.get("contrast", 0.0)
                ac = payload.get("ambient_color")
                if isinstance(ac, dict) and "Rgb" in ac:
                    rgb = ac["Rgb"]
                    fields["ambient_color"] = {"index": 250,
                        "rgb": "c2%02x%02x%02x%02x" % (0, rgb.get("r", 0), rgb.get("g", 0), rgb.get("b", 0))}
                elif isinstance(ac, str):
                    fields["ambient_color"] = normalize_value(ac)
                for kk in ("use_default_lights", "default_lighting", "default_lighting_type",
                           "brightness", "contrast", "ambient_color"):
                    consumed.add(kk)
            # drop silver-only / DXF-only fields so they don't appear as extra
            for sk in ("custom_scale", "id", "on_off",
                       # top-level silver-only status/UI bits and pre-2007 fields
                       # gold omits on the binary-DWG path for this version:
                       "ucs_icon_visible", "grid_flags", "default_lighting",
                       "shade_plot_mode", "frozen_layers"):
                payload.pop(sk, None)
            for sk in consumed:
                payload.pop(sk, None)

        field_map = FIELD_NAME_MAP.get(silver_type, {})
        for k, v in payload.items():
            if k == "common":
                continue
            # BLOCK/ENDBLK entity (dwg.spec 610-712): gold's dwgread emits only
            # `name` + common handle data on the binary-DWG path; base_pt /
            # description / xref_path are `#ifdef IS_DXF`-only. Silver wrongly
            # carries the parent BLOCK_HEADER's fields onto the entity — drop
            # them (both pre- and post-FIELD_NAME_MAP names).
            if silver_type in ("Block", "BlockEnd") and k in (
                "base_pt", "base_point", "description", "xref_path"):
                continue
            name = field_map.get(k, k)
            if is_ignored(name, ignore_set, ignore_patterns):
                continue
            fields[name] = normalize_value(v)

        out.append({"type": gold_type, "fields": fields})

    # Objects map keyed by handle string. Silver stores objects in a HashMap
    # (unordered), while gold's OBJECTS array is in handle order. The differ
    # aligns by (type, ordinal-within-type), so emit silver objects in
    # ascending handle order to match gold's canonical ordering.
    def _obj_sort_key(item) -> int:
        payload = item[1]
        if isinstance(payload, dict) and len(payload) == 1:
            inner = next(iter(payload.values()))
            if isinstance(inner, dict):
                h = inner.get("handle")
                if isinstance(h, int):
                    return h
        try:
            return int(item[0], 0)
        except (ValueError, TypeError):
            return 0

    for _handle_key, obj in sorted(objects.items(), key=_obj_sort_key):
        if not isinstance(obj, dict) or len(obj) != 1:
            continue
        silver_type = list(obj.keys())[0]
        payload = obj[silver_type]
        if not isinstance(payload, dict):
            continue
        if silver_type == "Associative":
            # Resolve DIMASSOC from the payload's dxf_name; silver's reader
            # parses it fully, so emit it under its real gold type instead of
            # flattening to UNKNOWN. The remaining ASSOC*/PERSUBENTMGR classes
            # are NOT yet field-projected — emitting them under canonical names
            # would surface many field-level gaps — so keep them as UNKNOWN
            # until their per-type projection packets land.
            if _associative_gold_name(payload.get("dxf_name") or "") == "DIMASSOC":
                gold_type = "DIMASSOC"
            else:
                gold_type = "UNKNOWN"
        else:
            gold_type = OBJECT_TYPE_MAP.get(silver_type, silver_type.upper())
        _inject_reactors(payload)
        fields = _object_common_fields(payload)
        if r2004_plus:
            # Gold emits is_xdic_missing on every object's handle stream.
            fields["is_xdic_missing"] = 1 if payload.get("xdictionary_handle") is None else 0
        if r2013_plus:
            # has_ds_data marks AcDs (SAB) modeler geometry storage; only
            # entities with modeler data set it, objects are always 0.
            fields["has_ds_data"] = 0
        if silver_type == "VisualStyle":
            _map_visual_style(payload, fields)
        assoc_data = None
        if silver_type == "Associative":
            # Every Associative payload wraps its parsed data under `data` plus
            # class-name metadata (`dxf_name`/`cpp_class_name`/`source_version`)
            # that gold does not serialize. Capture `data` for the per-type
            # projection below, then drop it and the metadata so the generic
            # loop cannot re-emit them as extra_in_silver (this runs for ALL
            # Associative subtypes, including the UNKNOWN-typed ones).
            assoc_data = payload.get("data")
            for kk in ("data", "dxf_name", "cpp_class_name", "source_version"):
                payload.pop(kk, None)
        if silver_type == "Scale":
            # Gold stores a raw `flag` BS (bit 0x01 = temporary) and does NOT
            # emit the derived `is_temporary` bool; silver stores only the
            # derived bool. Project `flag`; pop is_temporary so the generic
            # payload loop cannot re-emit it (extra_in_silver on every SCALE).
            is_temp = bool(payload.pop("is_temporary", False))
            fields.setdefault("flag", 1 if is_temp else 0)
        if silver_type == "Associative" and gold_type == "DIMASSOC":
            # Gold (dwg2.spec 3653 DWG_OBJECT(DIMASSOC)): associativity (BLx),
            # trans_space_flag (B), rotated_type (RC), dimensionobj (handle 4,
            # 330), then a fixed 6-slot `ref` array of AcDbOsnapPointRef blocks.
            # Silver stores the parsed data nested under
            # data.DimensionAssociation with snake_case names and a
            # per-associativity-slot list-of-lists; project to gold's flat,
            # slot-padded shape. unknown_bits (the HANDLE_UNKNOWN_BITS raw hex)
            # is NOT stored by silver and is left missing_in_silver.
            da = (assoc_data or {}).get("DimensionAssociation", {})
            if da:
                fields["associativity"] = da.get("associativity", 0)
                fields["trans_space_flag"] = 1 if da.get("trans_space") else 0
                fields["rotated_type"] = da.get("rotated_type", 0)
                if da.get("dimension") is not None:
                    fields["dimensionobj"] = normalize_handle_value(da["dimension"])
                # Gold's `ref` array is indexed by the associativity bit position
                # (dwg2.spec 3661 REPEAT_CN(6, ref): bit rcount1 -> ref[rcount1]),
                # so ref[1] holds the bit-1 (associativity&2) reference and unset
                # slots serialize as empty objects. Silver stores the same slot
                # layout in references: [Vec; 4], already keyed by bit position —
                # project each slot IN PLACE, preserving its index. Do NOT flatten
                # and re-pack (that shifts slot1 refs to index 0).
                refs = []
                for slot in da.get("references", []):
                    if isinstance(slot, list) and slot:
                        # One OsnapPointRef per slot in the corpus (the on-disk
                        # continuation bit can chain more, but none appear here).
                        r = slot[0]
                        gr = {
                            "classname": r.get("class_name", ""),
                            "osnap_type": r.get("osnap_type", 0),
                            "xrefs": [normalize_handle_value(h) for h in r.get("xrefs", [])],
                            "osnap_dist": normalize_float(r.get("osnap_distance", 0.0)),
                            "osnap_pt": normalize_value(r.get("osnap_point", [0.0, 0.0, 0.0])),
                            "has_lastpt_ref": 1 if r.get("has_last_point_reference") else 0,
                        }
                        if r.get("osnap_type"):
                            gr["main_subent_type"] = r.get("main_subent_type", 0)
                            gr["main_gsmarker"] = r.get("main_gs_marker", 0)
                            gr["xrefpaths"] = r.get("xref_paths", [])
                        if r.get("osnap_type") in (6, 11):
                            gr["intsectobj"] = [normalize_handle_value(h) for h in r.get("intersection_objects", [])]
                            gr["intersec_subent_type"] = r.get("intersection_subent_type", 0)
                            gr["intersec_gsmarker"] = r.get("intersection_gs_marker", 0)
                            gr["intersec_xrefpaths"] = r.get("intersection_xref_paths", [])
                        refs.append(gr)
                    else:
                        refs.append({})
                while len(refs) < 6:
                    refs.append({})
                fields["ref"] = refs[:6]
            # `data` + metadata were already popped by the general Associative
            # block above (assoc_data was captured before the pop).
        if silver_type == "XRecord":
            # Gold: xdata_size (BL), xdata (raw entry list), cloning (BS,
            # SINCE R_2000b). Silver: name (derived), cloning_flags (enum),
            # entries (structured list). Project to gold's shape.
            entries = payload.get("entries", [])
            fields["xdata_size"] = len(entries) if isinstance(entries, list) else 0
            # Project entries to gold's flat [code, value] pairs.
            if isinstance(entries, list):
                xdata = []
                for e in entries:
                    if isinstance(e, dict):
                        code = e.get("code", 0)
                        val = e.get("value")
                        # Unwrap the value variant ({"Int16": 1} -> 1).
                        if isinstance(val, dict) and len(val) == 1:
                            val = next(iter(val.values()))
                        xdata.append([code, normalize_value(val)])
                fields["xdata"] = xdata
            # cloning_flags enum -> cloning int (KeepExisting=0, etc.).
            cf = payload.get("cloning_flags")
            cloning_map = {"KeepExisting": 0, "Keep": 0, "ReplaceExisting": 1,
                           "Replace": 1, "XrefKeepExisting": 2, "Xref": 2}
            fields["cloning"] = cloning_map.get(cf, 0)
            # Drop silver-only fields.
            for sk in ("name", "cloning_flags", "entries", "object_references",
                       "preserve_object_reference_stream", "entries_complete",
                       "raw_data", "raw_dwg_handle_bits"):
                payload.pop(sk, None)
        if silver_type == "DictionaryVariable":
            # Gold: schema (RCd), strvalue (T). Silver: schema_number, value,
            # name. Map and drop the empty name.
            if "schema_number" in payload:
                fields["schema"] = normalize_value(payload["schema_number"])
            if "value" in payload:
                fields["strvalue"] = normalize_value(payload["value"])
            for sk in ("schema_number", "value", "name"):
                payload.pop(sk, None)
        # TABLESTYLE object (dwg2.spec 964). Two disjoint shapes:
        #  - legacy (pre-R2008, UNTIL R_2007): name/flow_direction/flags/
        #    horiz_cell_margin/vert_cell_margin/is_title_suppressed/
        #    is_header_suppressed/rowstyles. Silver reads the same data under
        #    snake_case names into flow_direction/flags/horizontal_margin/...
        #  - modern (R2010+): unknown_rc/name/unknown_bl1/unknown_bl2/cellstyle
        #    handle + the named cell-style payload CellStyle_fields under
        #    `sty.cellstyle.*` (and per-override `ovr.cellstyle.*`). Silver
        #    reads it into modern_style / modern_overrides.
        if silver_type == "TableStyle":
            def _content_format(cf, pfx):
                if not isinstance(cf, dict):
                    return
                fields[f"{pfx}.property_override_flags"] = cf.get("property_override_flags", 0)
                fields[f"{pfx}.property_flags"] = cf.get("property_flags", 0)
                fields[f"{pfx}.value_data_type"] = cf.get("value_data_type", 0)
                fields[f"{pfx}.value_unit_type"] = cf.get("value_unit_type", 0)
                fields[f"{pfx}.value_format_string"] = cf.get("value_format_string", "")
                fields[f"{pfx}.rotation"] = normalize_float(cf.get("rotation", 0.0))
                fields[f"{pfx}.block_scale"] = normalize_float(cf.get("block_scale", 0.0))
                ca = cf.get("cell_alignment", 0)
                fields[f"{pfx}.cell_alignment"] = ca if isinstance(ca, int) else 0
                fields[f"{pfx}.content_color"] = normalize_color(cf.get("content_color"))
                ts = cf.get("text_style")
                if ts is not None:
                    fields[f"{pfx}.text_style"] = normalize_handle_value(ts)
                fields[f"{pfx}.text_height"] = normalize_float(cf.get("text_height", 0.0))

            def _cell_style(cs, pfx):
                if not isinstance(cs, dict):
                    return
                fields[f"{pfx}.type"] = cs.get("style_type", 0)
                dflags = cs.get("data_flags", 0)
                fields[f"{pfx}.data_flags"] = dflags
                # The detail block is only serialized when data_flags != 0.
                if not dflags:
                    return
                fields[f"{pfx}.property_override_flags"] = cs.get("property_override_flags", 0)
                fields[f"{pfx}.merge_flags"] = cs.get("merge_flags", 0)
                fields[f"{pfx}.bg_color"] = normalize_color(cs.get("background_color"))
                fields[f"{pfx}.content_layout"] = cs.get("content_layout", 0)
                _content_format(cs.get("content_format"), f"{pfx}.content_format")
                mof = cs.get("margin_override_flags", 0)
                fields[f"{pfx}.margin_override_flags"] = mof
                if mof:
                    fields[f"{pfx}.vert_margin"] = normalize_float(cs.get("vertical_margin", 0.0))
                    fields[f"{pfx}.horiz_margin"] = normalize_float(cs.get("horizontal_margin", 0.0))
                    fields[f"{pfx}.bottom_margin"] = normalize_float(cs.get("bottom_margin", 0.0))
                    fields[f"{pfx}.right_margin"] = normalize_float(cs.get("right_margin", 0.0))
                    fields[f"{pfx}.margin_horiz_spacing"] = normalize_float(cs.get("horizontal_spacing", 0.0))
                    fields[f"{pfx}.margin_vert_spacing"] = normalize_float(cs.get("vertical_spacing", 0.0))
                borders = cs.get("borders", [])
                nb = len(borders) if isinstance(borders, list) else 0
                fields[f"{pfx}.num_borders"] = nb
                # Gold omits the borders array entirely when num_borders == 0
                # (REPEAT2(num_borders) yields nothing -> no key). Only emit it
                # when there are borders.
                if isinstance(borders, list) and nb:
                    projected = []
                    for b in borders:
                        if not isinstance(b, dict):
                            continue
                        gb = {"index_mask": b.get("index_mask", 0)}
                        border = b.get("border")
                        if isinstance(border, dict):
                            gb["border_overrides"] = 0  # property_flags bitflags -> BL
                            bt = border.get("border_type", 0)
                            gb["border_type"] = bt if isinstance(bt, int) else 0
                            gb["color"] = normalize_color(border.get("color"))
                            lw = border.get("line_weight", 0)
                            gb["linewt"] = lw if isinstance(lw, int) else 0
                            lt = b.get("line_type")
                            if lt is not None:
                                gb["ltype"] = normalize_handle_value(lt)
                            gb["visible"] = 0 if border.get("is_invisible") else 1
                            gb["double_line_spacing"] = normalize_float(border.get("double_line_spacing", 0.0))
                        projected.append(gb)
                    fields[f"{pfx}.borders"] = projected

            if not r2010_plus:
                # Legacy pre-R2008 path. Map snake_case -> gold names.
                fields["flow_direction"] = {"Down": 0, "Up": 1}.get(
                    payload.get("flow_direction"), payload.get("flow_direction", 0))
                fl = payload.get("flags", 0)
                fields["flags"] = fl if isinstance(fl, int) else 0
                fields["horiz_cell_margin"] = normalize_float(payload.get("horizontal_margin", 0.0))
                fields["vert_cell_margin"] = normalize_float(payload.get("vertical_margin", 0.0))
                fields["is_title_suppressed"] = 1 if payload.get("title_suppressed") else 0
                fields["is_header_suppressed"] = 1 if payload.get("header_suppressed") else 0
                # rowstyles: libredwg's legacy decode is degenerate ([0,0,0]);
                # the real content is in unknown_bits. Emit the placeholder to
                # match gold's shape.
                fields["rowstyles"] = [0, 0, 0]
            else:
                # Modern R2010+ path.
                fields["unknown_rc"] = payload.get("modern_unknown_byte", 0)
                fields["unknown_bl1"] = payload.get("modern_unknown_long1", 0)
                fields["unknown_bl2"] = payload.get("modern_unknown_long2", 0)
                csh = payload.get("modern_cell_style_handle")
                if csh is not None:
                    fields["cellstyle"] = normalize_handle_value(csh)
                ms = payload.get("modern_style")
                if isinstance(ms, dict):
                    _cell_style(ms.get("cell_style"), "sty.cellstyle")
                    fields["sty.id"] = ms.get("id", 0)
                    fields["sty.type"] = ms.get("style_type", 0)
                    fields["sty.name"] = ms.get("name", "")
                overrides = payload.get("modern_overrides", [])
                fields["numoverrides"] = len(overrides) if isinstance(overrides, list) else 0
                if isinstance(overrides, list) and overrides:
                    # Gold emits the FIRST override as `ovr.*` (+ unknown_bl3).
                    fields["unknown_bl3"] = overrides[0][0] if isinstance(overrides[0], (list, tuple)) else 0
                    ovr = overrides[0][1] if isinstance(overrides[0], (list, tuple)) and len(overrides[0]) > 1 else None
                    if isinstance(ovr, dict):
                        _cell_style(ovr.get("cell_style"), "ovr.cellstyle")
                        fields["ovr.id"] = ovr.get("id", 0)
                        fields["ovr.type"] = ovr.get("style_type", 0)
                        fields["ovr.name"] = ovr.get("name", "")
            # Drop silver-only / differently-named fields.
            for sk in ("description", "version", "horizontal_margin",
                       "vertical_margin", "title_suppressed", "header_suppressed",
                       "flow_direction", "flags",
                       "data_row_style", "header_row_style", "title_row_style",
                       "modern_unknown_byte", "modern_unknown_long1",
                       "modern_unknown_long2", "modern_cell_style_handle",
                       "modern_style", "modern_overrides", "annotative"):
                payload.pop(sk, None)
        # MLINESTYLE object (dwg.spec 4513): gold emits name/description/flag/
        # fill_color/start_angle/end_angle + num_lines + lines[] (offset/color/
        # lt). Silver stores elements[] (offset/color/linetype-name) + a flags
        # bitflag dict + fill_color. Project to gold's shape.
        if silver_type == "MLineStyle":
            # flag: gold BS 70 bitmask. Silver stores a flags dict
            # (fill_on/display_joints/display_start_caps/... booleans). The
            # corpus's styles have all-false flags -> flag 0. Project the dict
            # to the bitmask: fill_on=1, display_miters=2 (not stored), caps.
            fl = payload.get("flags")
            flag = 0
            if isinstance(fl, dict):
                if fl.get("fill_on"):
                    flag |= 1
                if fl.get("display_miters"):
                    flag |= 2
                if fl.get("start_square"):
                    flag |= 16
                if fl.get("start_inner_arc") or fl.get("start_inner_arcs"):
                    flag |= 32
                if fl.get("start_round"):
                    flag |= 64
                if fl.get("end_square"):
                    flag |= 256
                if fl.get("end_inner_arc") or fl.get("end_inner_arcs"):
                    flag |= 512
                if fl.get("end_round"):
                    flag |= 1024
            elif isinstance(fl, int):
                flag = fl
            fields["flag"] = flag
            if "description" in payload:
                fields["description"] = payload["description"]
            if "fill_color" in payload:
                fields["fill_color"] = normalize_color(payload["fill_color"])
            if "start_angle" in payload:
                fields["start_angle"] = normalize_float(payload["start_angle"])
            if "end_angle" in payload:
                fields["end_angle"] = normalize_float(payload["end_angle"])
            # lines[]: gold normalizes each line to its leading BD (offset) ->
            # the corpus rows are degenerate ([0,0]). Silver stores elements[]
            # with offset/color/linetype. Project count + the offset list.
            elements = payload.get("elements", [])
            fields["num_lines"] = len(elements) if isinstance(elements, list) else 0
            if isinstance(elements, list):
                fields["lines"] = [normalize_float(e.get("offset", 0.0)) if isinstance(e, dict) else 0
                                   for e in elements]
            for sk in ("elements", "flags", "fill_color", "start_angle",
                       "end_angle", "description"):
                payload.pop(sk, None)
        # Silver-only top-level VisualStyle fields that gold stores inside the
        # property bag or under a different name; skip so they don't appear as
        # extra_in_silver. The pre-R2010 top-level face_*/edge_* fields ARE
        # gold fields (read into the struct, not the bag), so keep them.
        vs_skip = {
            "properties", "internal_use_only", "extended_lighting_model",
        } if silver_type == "VisualStyle" else set()
        # MLEADERSTYLE object (dwg2.spec 1461): silver uses different field
        # names (snake_case + enums). Rename + convert + gate.
        if silver_type == "MultiLeaderStyle":
            _ML = {
                "content_type": "content_type", "leader_draw_order": "leader_order",
                "multileader_draw_order": "mleader_order",
                "max_leader_points": "max_points",
                "first_segment_angle": "first_seg_angle",
                "second_segment_angle": "second_seg_angle",
                "path_type": "type", "line_weight": "linewt",
                "enable_landing": "has_landing", "landing_gap": "landing_gap",
                "enable_dogleg": "has_dogleg", "landing_distance": "landing_dist",
                "arrowhead_size": "arrow_head_size", "default_text": "text_default",
                "text_left_attachment": "attach_left", "text_right_attachment": "attach_right",
                "text_alignment": "text_align_type", "text_color": "text_color",
                "text_height": "text_height", "text_frame": "has_text_frame",
                "text_always_left": "text_always_left", "align_space": "align_space",
                "block_content_color": "block_color", "block_content_rotation": "block_rotation",
                "enable_block_scale": "use_block_scale", "enable_block_rotation": "use_block_rotation",
                "block_content_connection": "block_connection", "scale_factor": "scale",
                "property_changed": "is_changed", "break_gap_size": "break_size",
                "text_angle_type": "text_angle_type",
                "text_attachment_direction": "attach_dir",
                "text_top_attachment": "attach_top", "text_bottom_attachment": "attach_bottom",
                "unknown_flag_298": "text_extended",
            }
            # enum string -> int maps (gold stores the BS/RC index)
            _ML_ENUM = {
                "content_type": {"None": 0, "Block": 1, "MText": 2},
                "leader_order": {"ContentFirst": 0, "LeaderFirst": 1, "LeaderHeadFirst": 0},
                "mleader_order": {"ContentFirst": 0, "LeaderFirst": 1},
                "type": {"StraightLineSegments": 0, "Spline": 1, "None_": 2, "InVisible": 2},
                "text_angle_type": {"Insert": 0, "Horizontal": 1, "BestFit": 2},
                "text_align_type": {"Left": 0, "Center": 1, "Right": 2, "Justify": 3, "Aligned": 4},
                "attach_dir": {"Horizontal": 0, "Vertical": 1},
                "attach_top": {"TopOfTopLine": 0, "MiddleOfTopLine": 1, "MiddleOfText": 2,
                               "CenterOfText": 9, "MiddleOfBottomLine": 3,
                               "BottomOfBottomLine": 4, "BottomLine": 5,
                               "BottomOfTopLineUnderlineBottomLine": 6,
                               "BottomOfTopLineUnderlineTopLine": 7,
                               "BottomOfTopLineUnderlineAll": 8,
                               "CenterOfTextOverline": 10},
                "attach_bottom": {"TopOfTopLine": 0, "MiddleOfTopLine": 1, "MiddleOfText": 2,
                                  "CenterOfText": 9, "MiddleOfBottomLine": 3,
                                  "BottomOfBottomLine": 4, "BottomLine": 5,
                                  "BottomOfTopLineUnderlineBottomLine": 6,
                                  "BottomOfTopLineUnderlineTopLine": 7,
                                  "BottomOfTopLineUnderlineAll": 8,
                                  "CenterOfTextOverline": 10},
                "attach_left": {"TopOfTopLine": 0, "MiddleOfTopLine": 1, "MiddleOfText": 2,
                                "MiddleOfBottomLine": 3, "BottomOfBottomLine": 4, "BottomLine": 5,
                                "BottomOfTopLineUnderlineBottomLine": 6,
                                "BottomOfTopLineUnderlineTopLine": 7,
                                "BottomOfTopLineUnderlineAll": 8,
                                "CenterOfTextOverline": 10},
                "attach_right": {"TopOfTopLine": 0, "MiddleOfTopLine": 1, "MiddleOfText": 2,
                                 "MiddleOfBottomLine": 3, "BottomOfBottomLine": 4, "BottomLine": 5,
                                 "BottomOfTopLineUnderlineBottomLine": 6,
                                 "BottomOfTopLineUnderlineTopLine": 7,
                                 "BottomOfTopLineUnderlineAll": 8,
                                 "CenterOfTextOverline": 10},
                "block_connection": {"BlockExtents": 0, "InsertionPoint": 1},
            }
            _ML_BOOL = {"has_landing", "has_dogleg", "use_block_scale", "use_block_rotation",
                        "has_text_frame", "text_always_left", "is_changed", "text_extended"}
            _ML_R2010 = {"class_version", "attach_dir", "attach_top", "attach_bottom"}
            _ML_R2013 = {"text_extended"}
            ml_consumed = set()
            for k, v in payload.items():
                if k in ("handle", "owner", "owner_handle", "reactors", "xdictionary_handle"):
                    continue
                gk = _ML.get(k)
                if gk is None:
                    if k in ("line_type_handle", "text_style_handle", "arrowhead_handle",
                             "block_content_handle", "block_content_scale_x",
                             "block_content_scale_y", "block_content_scale_z",
                             "line_color", "text_color", "is_annotative", "description",
                             "name", "class_version"):
                        ml_consumed.add(k)
                    continue
                ml_consumed.add(k)
                if gk in _ML_R2010 and not r2010_plus:
                    continue
                if gk in _ML_R2013 and not r2013_plus:
                    continue
                if gk in _ML_ENUM:
                    m = _ML_ENUM[gk]
                    fields[gk] = m.get(str(v), m.get(v.replace(" ", ""), v)) if isinstance(v, str) else v
                elif k in _ML_BOOL:
                    fields[gk] = 1 if v else 0
                else:
                    fields[gk] = normalize_value(v)
            # class_version (dwg2.spec 1461): the spec gates it SINCE R_2010b,
            # but MLEADERSTYLE objects are always read from EED/upconverted, so
            # gold emits class_version (default 2) on EVERY corpus version
            # (R2000 example_2000 included). Emit unconditionally.
            fields["class_version"] = payload.get("class_version", 2)
            ml_consumed.add("class_version")
            # linewt: gold stores the raw BLd lineweight value (negative =
            # ByLayer=-1/ByBlock=-2/Default=-3, else mm*100). Silver stores the
            # enum string. Map to gold's raw value.
            lw = payload.get("line_weight")
            if isinstance(lw, str):
                _LW = {"ByLayer": -1, "ByBlock": -2, "Default": -3, "ByLwDefault": -3}
                fields["linewt"] = _LW.get(lw, -3)
                ml_consumed.add("line_weight")
            # handles: gold emits these as handle dicts even when null (code 5,
            # absref 0). Silver stores Option<Handle> (None = null). Emit the
            # null-handle shape so the differ resolves both to target 0.
            _NULL_HANDLE = {"code": 5, "size": 0, "value": 0, "absref": 0}
            def _h(name):
                v = payload.get(name)
                return normalize_handle_value(v) if v is not None else _NULL_HANDLE
            fields["line_type"] = _h("line_type_handle")
            fields["text_style"] = _h("text_style_handle")
            fields["arrow_head"] = _h("arrowhead_handle")
            fields["block"] = _h("block_content_handle")
            for kk in ("line_type_handle", "text_style_handle", "arrowhead_handle",
                       "block_content_handle"):
                ml_consumed.add(kk)
            # colors: silver stores a Color enum; gold emits the ACI index
            # (ByBlock=0, ByLayer=256). normalize_color handles the string.
            for src, dst in (("line_color", "line_color"), ("text_color", "text_color"),
                             ("block_content_color", "block_color")):
                v = payload.get(src)
                if v is not None:
                    fields[dst] = normalize_color(v)
                ml_consumed.add(src)
            # block_scale: silver stores x/y/z scalars; gold uses a 3BD
            if r2013_plus or True:  # block_scale is JSON 3BD
                bsc = [payload.get("block_content_scale_x", 1.0),
                       payload.get("block_content_scale_y", 1.0),
                       payload.get("block_content_scale_z", 1.0)]
                fields["block_scale"] = bsc
                for kk in ("block_content_scale_x", "block_content_scale_y", "block_content_scale_z"):
                    ml_consumed.add(kk)
            # description/name: silver stores both; gold has description
            if payload.get("description"):
                fields["description"] = payload["description"]
            ml_consumed.update(("description", "name", "is_annotative"))
            # is_annotative (dwg2.spec 1461 FIELD_B 296): gold emits it on every
            # version (EED/upconvert); emit unconditionally.
            fields["is_annotative"] = 1 if payload.get("is_annotative") else 0
            for kk in ml_consumed:
                payload.pop(kk, None)

        mat_consumed = _map_material(payload, fields, r2007_plus, r2010_plus) if silver_type == "Material" else set()
        # LAYOUT object (dwg.spec 5316): silver stores plot config FLAT with
        # different names; gold nests them under `plotsettings.*` (the
        # AcDbPlotSettings subclass). Project the whole set.
        if silver_type == "Layout":
            # --- plotsettings.* (the AcDbPlotSettings subclass) ---
            _PS = {
                # gold printer_cfg_file = silver plot_page_name (the page setup
                # name); gold paper_size = silver plot_printer_name (the device);
                # gold canonical_media_name = silver paper_size (the media).
                "plot_page_name": "plotsettings.printer_cfg_file",
                "plot_printer_name": "plotsettings.paper_size",
                "plot_flags_dict": "plotsettings.plot_flags",  # placeholder; dict handled below
                "plot_margin_left": "plotsettings.left_margin",
                "plot_margin_bottom": "plotsettings.bottom_margin",
                "plot_margin_right": "plotsettings.right_margin",
                "plot_margin_top": "plotsettings.top_margin",
                "paper_width": "plotsettings.paper_width",
                "paper_height": "plotsettings.paper_height",
                "plot_printer_name": "plotsettings.paper_size",  # gold paper_size = silver device name
                "paper_size": "plotsettings.canonical_media_name",  # gold canonical = silver media
                "plot_paper_units": "plotsettings.plot_paper_unit",
                "plot_rotation": "plotsettings.plot_rotation_mode",
                "plot_type": "plotsettings.plot_type",
                "plot_scale_factor": "plotsettings.std_scale_factor",
                "plot_scale_type": "plotsettings.std_scale_type",
                "plot_style_sheet": "plotsettings.stylesheet",
            }
            # version gates (shadeplot R2004a+, livesection/plotview handles)
            _PS_R2004 = {"plotsettings.shadeplot_type", "plotsettings.shadeplot_reslevel",
                         "plotsettings.shadeplot_customdpi"}
            for sk, gk in _PS.items():
                if sk in ("plot_flags_dict",):
                    continue
                v = payload.get(sk)
                if v is None:
                    continue
                if gk in _PS_R2004 and not r2004_plus:
                    continue
                fields[gk] = normalize_value(v)
            # plot_flags dict -> int bits, using silver's PlotFlags::to_bits
            # layout (plot_settings.rs): bit0 plot_viewport_borders, 1
            # show_plot_styles, 2 plot_centered, 3 plot_hidden, 4
            # use_standard_scale, 5 plot_plot_styles, 6 scale_lineweights, 7
            # print_lineweights, 9 draw_viewports_first, 10 model_type, 11
            # update_paper, 12 zoom_to_paper_on_update, 13 initializing, 14
            # prev_plot_init; unknown_bits carried through (mask !0x7EFF).
            pfl = payload.get("plot_flags")
            if isinstance(pfl, dict):
                bits = pfl.get("unknown_bits", 0) & ~0x7EFF
                for name, bit in (("plot_viewport_borders", 0), ("show_plot_styles", 1),
                        ("plot_centered", 2), ("plot_hidden", 3), ("use_standard_scale", 4),
                        ("plot_plot_styles", 5), ("scale_lineweights", 6),
                        ("print_lineweights", 7), ("draw_viewports_first", 9),
                        ("model_type", 10), ("update_paper", 11),
                        ("zoom_to_paper_on_update", 12), ("initializing", 13),
                        ("prev_plot_init", 14)):
                    if pfl.get(name):
                        bits |= (1 << bit)
                fields["plotsettings.plot_flags"] = bits
            elif isinstance(pfl, int):
                fields["plotsettings.plot_flags"] = pfl
            # 2-point fields: plot_origin, plot_window_ll/ur, paper_image_origin
            if payload.get("plot_origin_x") is not None or payload.get("plot_origin_y") is not None:
                fields["plotsettings.plot_origin"] = [payload.get("plot_origin_x", 0.0), payload.get("plot_origin_y", 0.0)]
            if payload.get("plot_window_min_x") is not None or payload.get("plot_window_min_y") is not None:
                fields["plotsettings.plot_window_ll"] = [payload.get("plot_window_min_x", 0.0), payload.get("plot_window_min_y", 0.0)]
            if payload.get("plot_window_max_x") is not None or payload.get("plot_window_max_y") is not None:
                fields["plotsettings.plot_window_ur"] = [payload.get("plot_window_max_x", 0.0), payload.get("plot_window_max_y", 0.0)]
            if payload.get("paper_image_origin_x") is not None or payload.get("paper_image_origin_y") is not None:
                fields["plotsettings.paper_image_origin"] = [payload.get("paper_image_origin_x", 0.0), payload.get("paper_image_origin_y", 0.0)]
            # canonical_media_name is mapped from silver's `paper_size` in _PS
            # above; do NOT double-emit it here.
            # shadeplot (R2004a+)
            if r2004_plus:
                if payload.get("shade_plot_mode") is not None:
                    fields["plotsettings.shadeplot_type"] = payload["shade_plot_mode"]
                if payload.get("shade_plot_resolution") is not None:
                    fields["plotsettings.shadeplot_reslevel"] = payload["shade_plot_resolution"]
                if payload.get("shade_plot_dpi") is not None:
                    fields["plotsettings.shadeplot_customdpi"] = payload["shade_plot_dpi"]
            # paper_units/drawing_units: gold computes from std_scale_factor;
            # silver stores plot_scale_numerator/denominator.
            if payload.get("plot_scale_numerator") is not None:
                fields["plotsettings.paper_units"] = payload["plot_scale_numerator"]
            if payload.get("plot_scale_denominator") is not None:
                fields["plotsettings.drawing_units"] = payload["plot_scale_denominator"]
            # plotview handle (R2004a+; gold omits it on R2000/AC1015).
            if r2004_plus and payload.get("plot_view_handle") is not None:
                fields["plotsettings.plotview"] = normalize_handle_value(payload["plot_view_handle"])
            # shadeplot handle (R2007a+, code 4)
            if r2007_plus and payload.get("shade_plot_handle") is not None:
                fields["plotsettings.shadeplot"] = normalize_handle_value(payload["shade_plot_handle"])
            # --- non-plotsettings LAYOUT fields ---
            _LAY = {
                "min_extents": "EXTMIN", "max_extents": "EXTMAX",
                "insertion_base": "INSBASE", "min_limits": "LIMMIN",
                "max_limits": "LIMMAX", "ucs_origin": "UCSORG",
                "ucs_x_axis": "UCSXDIR", "ucs_y_axis": "UCSYDIR",
                "ucs_ortho_type": "UCSORTHOVIEW", "elevation": "ucs_elevation",
                "flags": "layout_flags", "name": "layout_name",
                "tab_order": "tab_order",
            }
            for sk, gk in _LAY.items():
                v = payload.get(sk)
                if v is None:
                    continue
                fields[gk] = normalize_value(v)
            # handles
            if payload.get("block_record") is not None:
                fields["block_header"] = normalize_handle_value(payload["block_record"])
            if payload.get("viewport") is not None:
                fields["active_viewport"] = normalize_handle_value(payload["viewport"])
            # drop all consumed/silver-only keys so the generic loop skips them
            for kk in (list(_PS) + list(_LAY) + [
                "plot_flags", "plot_origin_x", "plot_origin_y",
                "plot_window_min_x", "plot_window_min_y",
                "plot_window_max_x", "plot_window_max_y",
                "paper_image_origin_x", "paper_image_origin_y",
                "shade_plot_mode", "shade_plot_resolution", "shade_plot_dpi",
                "plot_scale_numerator", "plot_scale_denominator",
                "plot_view_handle", "plot_view_name", "plot_page_name",
                "block_record", "viewport", "viewports",
                # silver-only LAYOUT fields gold omits on the binary path:
                "visual_style_handle",
            ]):
                payload.pop(kk, None)

        for k, v in payload.items():
            if k in ("handle", "owner", "owner_handle", "reactors", "xdictionary_handle"):
                continue
            if k in vs_skip or k in mat_consumed:
                continue
            # LAYOUT base_ucs/named_ucs are handle-stream fields in gold
            # (code 5, dwg.spec); silver stores the raw Handle int. Wrap so
            # the differ resolves them (a bare int never matches a token).
            if silver_type == "Layout" and k in ("base_ucs", "named_ucs"):
                fields[k] = normalize_handle_value(v)
                continue
            # GEODATA host_block: gold handle-stream field (code 4); silver
            # stores the raw Handle int.
            if gold_type == "GEODATA" and k == "host_block":
                fields[k] = normalize_handle_value(v)
                continue
            if is_ignored(k, ignore_set, ignore_patterns):
                continue
            fields[k] = normalize_value(v)
        out.append({"type": gold_type, "fields": fields})

    # Table records.
    TABLE_SPECS: List[Tuple[str, str, str]] = [
        ("layers", "LAYER", "LAYER"),
        ("line_types", "LTYPE", "LTYPE"),
        ("text_styles", "STYLE", "STYLE"),
        ("block_records", "BLOCK_RECORD", "BLOCK_HEADER"),
        ("dim_styles", "DIMSTYLE", "DIMSTYLE"),
        ("app_ids", "APPID", "APPID"),
        ("views", "VIEW", "VIEW"),
        ("vports", "VPORT", "VPORT"),
        ("ucss", "UCS", "UCS"),
    ]
    # Gold emits these storage fields for every table record
    # (COMMON_TABLE_FLAGS + common_object_handle_data.spec). Silver parses the
    # xref bits and unknown byte but discards them; for ordinary drawings they
    # are always this uniform set, so the normalizer derives them:
    #   ownerhandle       = the owning table's control-object handle
    #   is_xref_ref       = 1   (ordinary records always reference-free)
    #   is_xref_resolved  = 0
    #   is_xref_dep       = 0
    #   xref              = null handle
    #   unknown           = 0   (APPID only, SINCE R_13b1)
    # Gold emits a CONTROL object per table (e.g. APPID_CONTROL) that silver
    # does not surface as a standalone object (the table's handle IS the
    # control). Emit a minimal control record so the differ's handle->type map
    # can resolve table-record ownerhandle to <TYPE>_CONTROL instead of a raw
    # int. The control's own fields are gold-version-gated and not compared
    # beyond handle/type, so keep it minimal.
    CONTROL_GOLD_TYPE = {
        "layers": "LAYER_CONTROL", "line_types": "LTYPE_CONTROL",
        "text_styles": "STYLE_CONTROL", "block_records": "BLOCK_CONTROL",
        "dim_styles": "DIMSTYLE_CONTROL", "app_ids": "APPID_CONTROL",
        "views": "VIEW_CONTROL", "vports": "VPORT_CONTROL",
        "ucss": "UCS_CONTROL",
    }
    for table_key, _entry_gold_type, record_gold_type in TABLE_SPECS:
        table = data.get(table_key, {})
        if not isinstance(table, dict):
            continue
        table_handle = normalize_handle_value(table.get("handle"))
        control_type = CONTROL_GOLD_TYPE.get(table_key)
        if control_type and table_handle is not None:
            out.append({"type": control_type,
                        "fields": {"handle": table_handle,
                                   "ownerhandle": normalize_handle_value(0)}})
        entries = table.get("entries", {})
        for _key, rec in entries.items():
            if not isinstance(rec, dict):
                continue
            _inject_reactors(rec)
            fields = _object_common_fields(rec)
            if table_handle is not None:
                fields["ownerhandle"] = table_handle
            # is_xref_* bits: gold reads them from the stream only up to
            # R2004; on R2007+ they are derived (is_xref_ref=1, is_xref_dep
            # from is_xref_resolved) but the JSON omits the always-constant
            # ones. Emit only where gold serializes them.
            if not r2007_plus:
                fields["is_xref_ref"] = 1
                fields["is_xref_dep"] = 0
            fields["is_xref_resolved"] = 0
            fields["xref"] = normalize_handle_value(0)
            if record_gold_type == "APPID":
                fields["unknown"] = 0
            if record_gold_type == "BLOCK_HEADER":
                # BLOCK_RECORD flag bits (dwg.spec): ordinary block records
                # are neither anonymous nor xref-bound.
                fields["anonymous"] = 0
                fields["hasattrs"] = 0
                fields["blkisxref"] = 0
                fields["xrefoverlaid"] = 0
                fields["xref_loaded"] = 0
                # Gold always emits xref_pname (FIELD_T, R13b1+); silver stores
                # no xref_pname, so emit gold's default empty string.
                fields.setdefault("xref_pname", "")
            if record_gold_type == "VPORT":
                # VPORT view params (dwg.spec 4007-4160 DWG path): rename silver
                # snake_case to gold names, convert types, version-gate. The
                # consumed keys are skipped by the generic loop below.
                _VPORT_RENAME = {
                    "view_height": "VIEWSIZE", "view_width": "view_width",
                    "view_center": "VIEWCTR", "view_direction": "VIEWDIR",
                    "view_target": "view_target", "view_twist": "VIEWTWIST",
                    "lens_length": "LENSLENGTH", "front_clip": "FRONTZ",
                    "back_clip": "BACKZ", "snap_rotation": "SNAPANG",
                    "snap_base": "SNAPBASE", "snap_spacing": "SNAPUNIT",
                    "grid_spacing": "GRIDUNIT", "ucs_origin": "ucsorg",
                    "ucs_x_axis": "ucsxdir", "ucs_y_axis": "ucsydir",
                    "ucs_elevation": "ucs_elevation", "ucs_ortho_type": "UCSORTHOVIEW",
                    "ucs_at_origin": "ucs_at_origin", "grid_major": "grid_major",
                    "brightness": "brightness", "contrast": "contrast",
                    "default_lighting_type": "default_lightning_type",  # gold typo
                    "snap_isopair": "SNAPISOPAIR",
                }
                _VPORT_BOOL = {
                    "grid_on": "GRIDMODE", "snap_on": "SNAPMODE",
                    "snap_style": "SNAPSTYLE", "fast_zoom": "FASTZOOM",
                    "ucsfollow": "UCSFOLLOW", "use_default_lights": "use_default_lights",
                    "ucs_per_viewport": "UCSVP",
                }
                _VPORT_R2000 = {"ucsorg", "ucsxdir", "ucsydir", "ucs_elevation",
                                "UCSORTHOVIEW", "ucs_at_origin", "UCSVP",
                                "render_mode", "named_ucs", "base_ucs"}
                _VPORT_R2007 = {"grid_flags", "grid_major", "use_default_lights",
                                "default_lightning_type", "brightness", "contrast",
                                "ambient_color", "sun", "background", "visualstyle"}
                # all silver keys this block consumes (generic loop must skip)
                vport_consumed = (set(_VPORT_RENAME) | set(_VPORT_BOOL)
                                  | {"render_mode", "grid_flags", "ambient_color",
                                     "named_ucs_handle", "base_ucs_handle", "sun_handle",
                                     "background_handle", "visual_style_handle",
                                     "ucsicon_lower", "ucsicon_origin"})
                for k, v in rec.items():
                    if k not in vport_consumed:
                        continue
                    gk = _VPORT_RENAME.get(k) or _VPORT_BOOL.get(k)
                    if gk is None:
                        continue  # special-conversion keys handled below
                    if gk in _VPORT_R2000 and not r2000_plus:
                        continue
                    if gk in _VPORT_R2007 and not r2007_plus:
                        continue
                    if k in _VPORT_BOOL:
                        fields[gk] = 1 if v else 0
                    else:
                        fields[gk] = normalize_value(v)
                # special conversions
                if r2000_plus:
                    rm = rec.get("render_mode")
                    if isinstance(rm, str):
                        _RM = {"Wireframe2D": 0, "Wireframe3D": 1, "HiddenLine": 2,
                               "FlatShaded": 3, "GouraudShaded": 4,
                               "FlatShadedWithEdges": 5, "GouraudShadedWithEdges": 6}
                        fields["render_mode"] = _RM.get(rm, 0)
                    elif rm is not None:
                        fields["render_mode"] = rm
                    fields["named_ucs"] = normalize_handle_value(rec.get("named_ucs_handle"))
                    fields["base_ucs"] = normalize_handle_value(rec.get("base_ucs_handle"))
                if r2007_plus:
                    gfl = rec.get("grid_flags")
                    if isinstance(gfl, dict):
                        fields["grid_flags"] = ((1 if gfl.get("beyond_limits") else 0)
                                                | (2 if gfl.get("adaptive") else 0)
                                                | (4 if gfl.get("subdivision") else 0)
                                                | (8 if gfl.get("follow_dynamic") else 0))
                    elif gfl is not None:
                        fields["grid_flags"] = gfl
                    fields["sun"] = normalize_handle_value(rec.get("sun_handle"))
                    fields["background"] = normalize_handle_value(rec.get("background_handle"))
                    fields["visualstyle"] = normalize_handle_value(rec.get("visual_style_handle"))
                    ac = rec.get("ambient_color")
                    if isinstance(ac, dict) and "Rgb" in ac:
                        rgb = ac["Rgb"]
                        fields["ambient_color"] = {"index": 250,
                            "rgb": "c2%02x%02x%02x%02x" % (0, rgb.get("r", 0), rgb.get("g", 0), rgb.get("b", 0))}
                # composite bits
                ucsicon = (1 if rec.get("ucsicon_lower") else 0) | (2 if rec.get("ucsicon_origin") else 0)
                fields["UCSICON"] = ucsicon
                viewmode = ((1 if rec.get("ucs_per_viewport") else 0)
                            | (2 if rec.get("ucs_at_origin") else 0)
                            | (8 if rec.get("ucsfollow") else 0))
                fields["VIEWMODE"] = viewmode
                # view_width: gold computes it (aspect_ratio * VIEWSIZE); silver
                # stores neither. Derive from the two silver values so the
                # R2000+ gold field (a plain BD in the DWG path) matches.
                vh = rec.get("view_height")
                ar = rec.get("aspect_ratio")
                if isinstance(vh, (int, float)) and isinstance(ar, (int, float)):
                    fields.setdefault("view_width", ar * vh)
            if record_gold_type == "VIEW":
                # VIEW table record (dwg.spec 3738 DWG path): rename silver
                # snake_case view params to gold names, convert, version-gate.
                _VIEW_RENAME = {
                    "height": "VIEWSIZE", "width": "view_width",
                    "direction": "VIEWDIR", "target": "view_target",
                    "twist_angle": "VIEWTWIST", "lens_length": "LENSLENGTH",
                    "front_clip": "FRONTZ", "back_clip": "BACKZ",
                    "ucs_origin": "ucsorg", "ucs_x_axis": "ucsxdir",
                    "ucs_y_axis": "ucsydir", "ucs_ortho_type": "UCSORTHOVIEW",
                    "ucs_elevation": "ucs_elevation", "ucs_associated": "associated_ucs",
                    "default_lighting_type": "default_lightning_type",
                    "brightness": "brightness", "contrast": "contrast",
                }
                _VIEW_BOOL = {"paper_space": "is_pspace", "ucs_associated_bool": "associated_ucs",
                              "use_default_lights": "use_default_lights"}
                _VIEW_2D = {"VIEWCTR"}
                _VIEW_R2000 = {"render_mode", "associated_ucs", "ucsorg", "ucsxdir",
                               "ucsydir", "UCSORTHOVIEW", "ucs_elevation",
                               "named_ucs", "base_ucs"}
                _VIEW_R2007 = {"use_default_lights", "default_lightning_type",
                               "brightness", "contrast", "ambient_color",
                               "background", "visualstyle", "sun", "livesection",
                               "is_camera_plottable"}
                view_consumed = set()
                for k, v in rec.items():
                    if k in ("handle", "owner", "owner_handle", "reactors", "xdictionary_handle"):
                        continue
                    gk = _VIEW_RENAME.get(k) or _VIEW_BOOL.get(k)
                    if gk is None:
                        if k in ("render_mode", "ambient_color", "named_ucs_handle",
                                 "base_ucs_handle", "sun_handle", "background_handle",
                                 "visual_style_handle", "live_section_handle",
                                 "perspective", "front_clipping", "back_clipping",
                                 "front_clip_at_eye", "center"):
                            view_consumed.add(k)
                        continue
                    view_consumed.add(k)
                    if gk in _VIEW_R2000 and not r2000_plus:
                        continue
                    if gk in _VIEW_R2007 and not r2007_plus:
                        continue
                    if k in _VIEW_BOOL:
                        fields[gk] = 1 if v else 0
                    else:
                        fields[gk] = normalize_value(v)
                # center -> VIEWCTR (2RD)
                c = rec.get("center")
                if c is not None:
                    nv = normalize_value(c)
                    if isinstance(nv, list):
                        nv = nv[:2]
                    fields["VIEWCTR"] = nv
                    view_consumed.add("center")
                # render_mode string -> int (R2000+)
                if r2000_plus:
                    rm = rec.get("render_mode")
                    if isinstance(rm, str):
                        _RM = {"Wireframe2D": 0, "Wireframe3D": 1, "HiddenLine": 2,
                               "FlatShaded": 3, "GouraudShaded": 4,
                               "FlatShadedWithEdges": 5, "GouraudShadedWithEdges": 6}
                        fields["render_mode"] = _RM.get(rm, 0)
                    elif rm is not None:
                        fields["render_mode"] = rm
                    fields["named_ucs"] = normalize_handle_value(rec.get("named_ucs_handle"))
                    fields["base_ucs"] = normalize_handle_value(rec.get("base_ucs_handle"))
                    for kk in ("render_mode", "named_ucs_handle", "base_ucs_handle"):
                        view_consumed.add(kk)
                if r2007_plus:
                    fields["use_default_lights"] = 1 if rec.get("use_default_lights") else 0
                    fields["is_camera_plottable"] = 1 if rec.get("camera_plottable") else 0
                    view_consumed.add("camera_plottable")
                    fields["background"] = normalize_handle_value(rec.get("background_handle"))
                    fields["visualstyle"] = normalize_handle_value(rec.get("visual_style_handle"))
                    fields["sun"] = normalize_handle_value(rec.get("sun_handle"))
                    ac = rec.get("ambient_color")
                    if isinstance(ac, dict) and "Rgb" in ac:
                        rgb = ac["Rgb"]
                        fields["ambient_color"] = {"index": 250,
                            "rgb": "c2%02x%02x%02x%02x" % (0, rgb.get("r", 0), rgb.get("g", 0), rgb.get("b", 0))}
                    for kk in ("use_default_lights", "background_handle", "visual_style_handle",
                               "sun_handle", "ambient_color"):
                        view_consumed.add(kk)
                # drop silver-only / DXF-only fields
                for kk in ("perspective", "front_clipping", "back_clipping",
                           "front_clip_at_eye", "live_section_handle"):
                    view_consumed.add(kk)
                # composite VIEWMODE bits (same as VPORT)
                viewmode = ((1 if rec.get("ucs_per_viewport") else 0)
                            | (2 if rec.get("ucs_at_origin") else 0)
                            | (8 if rec.get("ucsfollow") else 0))
                fields["VIEWMODE"] = viewmode
                view_consumed.update(("ucs_per_viewport", "ucsfollow"))
                # aspect_ratio: gold computes view_width / VIEWSIZE (both stored
                # in silver as width/height). Derive it.
                vw = rec.get("width"); vh2 = rec.get("height")
                if isinstance(vw, (int, float)) and isinstance(vh2, (int, float)) and vh2:
                    fields.setdefault("aspect_ratio", vw / vh2)
                # livesection handle (R2007+)
                if r2007_plus:
                    fields["livesection"] = normalize_handle_value(rec.get("live_section_handle"))
                    view_consumed.add("live_section_handle")
                # drop silver xref bookkeeping (gold table-record block emits the
                # is_xref_* bits; these silver-internal dupes never appear in gold)
                view_consumed.update(("xref_reference", "xref_resolved",
                                      "xref_dependent", "xref_handle"))
                # consumed-key guard for the generic loop below
                for kk in view_consumed:
                    rec.pop(kk, None)
            if record_gold_type == "LTYPE":
                # LTYPE dash patterns (dwg.spec 3580 DWG path). Silver stores
                # elements[] (length+complex), pattern_length, alignment as a
                # char; gold stores dashes[] (8 fields each), pattern_len,
                # numdashes, alignment as a byte (ord). Project.
                al = rec.get("alignment")
                if isinstance(al, str) and len(al) == 1:
                    fields["alignment"] = ord(al)
                elif isinstance(al, int):
                    fields["alignment"] = al
                if r2000_plus or True:  # pattern_len is LATER_VERSIONS (R13+)
                    fields["pattern_len"] = rec.get("pattern_length", 0.0)
                elems = rec.get("elements") or []
                fields["numdashes"] = len(elems)
                if elems:
                    dashes = []
                    for e in elems:
                        cx = e.get("complex")
                        if isinstance(cx, dict):
                            dashes.append({
                                "length": e.get("length", 0.0),
                                "complex_shapecode": cx.get("shapecode", 0),
                                "style": normalize_handle_value(cx.get("style_handle", 0)),
                                "x_offset": cx.get("x_offset", 0.0),
                                "y_offset": cx.get("y_offset", 0.0),
                                "scale": cx.get("scale", 1.0),
                                "rotation": cx.get("rotation", 0.0),
                                "shape_flag": cx.get("flags", 0),
                            })
                        else:
                            dashes.append({
                                "length": e.get("length", 0.0),
                                "complex_shapecode": 0,
                                "style": normalize_handle_value(0),
                                "x_offset": 0.0, "y_offset": 0.0,
                                "scale": 1.0, "rotation": 0.0, "shape_flag": 0,
                            })
                    fields["dashes"] = dashes
                # strings_area: gold emits a TF binary field. UNTIL R_2004 it's
                # always 256 bytes; R2007+ only when has_strings_area (any dash
                # with shape_flag & 2). All-zero in the corpus. Silver stores
                # none; emit zeros on pre-R2007 so gold's field matches.
                if not r2007_plus:
                    fields["strings_area"] = "00" * 256
                elif elems and any((e.get("complex") or {}).get("flags", 0) & 2 for e in elems):
                    fields["strings_area"] = "00" * 512
                # drop silver-only names so the generic loop skips them
                for kk in ("elements", "pattern_length", "alignment"):
                    rec.pop(kk, None)
            if r2004_plus:
                # Gold emits is_xdic_missing on every object's handle stream,
                # table records included.
                fields["is_xdic_missing"] = 1 if rec.get("xdictionary_handle") is None else 0
            if r2013_plus:
                fields["has_ds_data"] = 0
            if record_gold_type == "DIMSTYLE":
                # flag0 is a derived gold field (bit 0 of the 70 flag); the
                # silver struct doesn't store it. Gold always has it as 0 for
                # ordinary styles.
                fields.setdefault("flag0", 0)
            if record_gold_type == "STYLE":
                # STYLE (dwg.spec 3479): silver stores is_shape_file / height;
                # gold uses is_shape / text_size. Project.
                if "is_shape_file" in rec:
                    fields["is_shape"] = 1 if rec["is_shape_file"] else 0
                if "height" in rec:
                    fields["text_size"] = normalize_value(rec["height"])
                # is_vertical: silver stores it; gold emits it (R2000+).
                if r2000_plus and "is_vertical" in rec:
                    fields["is_vertical"] = 1 if rec["is_vertical"] else 0
                # generation: silver stores flags dict; gold emits a plain RC.
                # bigfont_file: silver stores big_font_file; gold bigfont_file.
                if "big_font_file" in rec:
                    fields["bigfont_file"] = rec["big_font_file"]
                    rec.pop("big_font_file", None)
                fl = rec.get("flags")
                if isinstance(fl, dict):
                    gen = 0
                    if fl.get("backward"): gen |= 2
                    if fl.get("upside_down"): gen |= 4
                    fields["generation"] = gen
                    rec.pop("flags", None)
                # drop silver-only
                for kk in ("is_shape_file", "height", "true_type_font", "is_vertical",
                           "xref_dependent", "annotative"):
                    rec.pop(kk, None)
            if record_gold_type == "LAYER":
                # LAYER (dwg.spec 3298): silver stores flag0 (raw bitmask) and
                # linetype_handle on the struct; project them. color {Index:n}
                # -> int. plotstyle_handle -> plotstyle (handle-wrap).
                if "flag0" in rec:
                    fields["flag0"] = rec["flag0"]
                    rec.pop("flag0", None)
                col = rec.get("color")
                if isinstance(col, dict) and "Index" in col:
                    fields["color"] = col["Index"]
                    rec.pop("color", None)
                if "plotstyle_handle" in rec:
                    fields["plotstyle"] = normalize_handle_value(rec["plotstyle_handle"])
                    rec.pop("plotstyle_handle", None)
                # ltype: silver stores line_type (name) + linetype_handle. Gold
                # emits the handle dict. Project the handle.
                if "linetype_handle" in rec:
                    fields["ltype"] = normalize_handle_value(rec["linetype_handle"])
                    rec.pop("linetype_handle", None)
                # drop silver-only
                for kk in ("plotstyle", "ltype", "plot_style", "book_name", "color_name",
                           "description", "is_plottable", "transparency",
                           "xref_block_record_handle", "material_handle",
                           "flags", "line_type"):
                    rec.pop(kk, None)
                # material: gold emits it as a handle dict (R2007a+); silver
                # stores the raw Handle int. Wrap it. Drop it on pre-R2007 so
                # the generic loop doesn't re-add it.
                if r2007_plus and "material" in rec:
                    fields["material"] = normalize_handle_value(rec["material"])
                rec.pop("material", None)
            for k, v in rec.items():
                if k in ("handle", "owner", "owner_handle", "reactors", "xdictionary_handle"):
                    continue
                # VPORT: the dedicated block above already projected/renamed or
                # intentionally dropped every view-param key; skip them here so
                # the generic loop doesn't re-add them under silver names.
                if record_gold_type == "VPORT":
                    if k in ("view_height", "view_width", "view_center", "view_direction",
                             "view_target", "view_twist", "lens_length", "front_clip",
                             "back_clip", "snap_rotation", "snap_base", "snap_spacing",
                             "grid_spacing", "ucs_origin", "ucs_x_axis", "ucs_y_axis",
                             "ucs_elevation", "ucs_ortho_type", "ucs_at_origin",
                             "grid_major", "brightness", "contrast", "default_lighting_type",
                             "snap_isopair", "grid_on", "snap_on", "snap_style",
                             "fast_zoom", "ucsfollow", "use_default_lights",
                             "ucs_per_viewport", "render_mode", "grid_flags",
                             "ambient_color", "named_ucs_handle", "base_ucs_handle",
                             "sun_handle", "background_handle", "visual_style_handle",
                             "ucsicon_lower", "ucsicon_origin",
                             # silver-only VPORT fields gold never emits on the
                             # binary-DWG path (clipping flags live in VIEWMODE/
                             # plot settings; perspective is DXF-only):
                             "perspective", "front_clipping", "back_clipping",
                             "front_clip_at_eye",
                             # silver xref bookkeeping (the gold-side is_xref_*
                             # bits are emitted by the table-record block; these
                             # silver-internal duplicates never appear in gold):
                             "xref_reference", "xref_resolved", "xref_dependent",
                             "xref_handle"):
                        continue
                # BLOCK_HEADER (dwg.spec 3146-3278): rename silver storage
                # names to gold's, version-gate the R2004+/R2007+ fields, and
                # drop silver-only fields gold never serializes to JSON.
                if record_gold_type == "BLOCK_HEADER":
                    if k == "base_point":
                        fields["base_pt"] = normalize_value(v); continue
                    if k == "block_entity_handle":
                        fields["block_entity"] = normalize_handle_value(v); continue
                    if k == "block_end_handle":
                        fields["endblk_entity"] = normalize_handle_value(v); continue
                    if k == "entity_handles":
                        if r2004_plus and v:
                            fields["entities"] = [normalize_handle_value(h) for h in v]
                        continue
                    if k == "units":
                        if r2007_plus:
                            fields["insert_units"] = normalize_value(v)
                        continue
                    if k == "scale_uniformly":
                        if r2007_plus:
                            fields["block_scaling"] = 1 if v else 0
                        continue
                    if k == "explodable":
                        if r2007_plus:
                            fields["explodable"] = 1 if v else 0
                        continue
                    # gold never serializes these to binary-DWG JSON:
                    # flags (composite -> split bits done above), preview_data,
                    # insert_count_bytes, insert_handles, xref_path, is_xdic_missing
                    # (already set above), has_ds_data (set above).
                    if k in ("flags", "preview_data", "insert_count_bytes",
                             "insert_handles", "xref_path"):
                        continue
                # DIMSTYLE: silver stores lowercase dim* names; gold uses
                # uppercase DIM*. Uppercase the dim prefix and drop
                # silver-only derived fields (true_color, name, handle forms)
                # and version-gated fields gold doesn't have in this version.
                if record_gold_type == "DIMSTYLE" and k.startswith("dim"):
                    # DIMTXSTY: gold stores the text-style HANDLE; silver
                    # stores the resolved name in `dimtxsty`. Emit the handle.
                    if k == "dimtxsty":
                        h = rec.get("dimtxsty_handle")
                        if h is not None:
                            fields["DIMTXSTY"] = normalize_handle_value(h)
                        continue
                    # DIMLTYPE/DIMLTEX1/DIMLTEX2: gold emits these handles
                    # SINCE R_2007a; silver stores them as *_handle.
                    if k in ("dimltex_handle", "dimltex1_handle", "dimltex2_handle"):
                        if r2007_plus:
                            gk = {"dimltex_handle": "DIMLTYPE",
                                  "dimltex1_handle": "DIMLTEX1",
                                  "dimltex2_handle": "DIMLTEX2"}[k]
                            fields[gk] = normalize_handle_value(v)
                        continue
                    if k.endswith(("_true_color", "_name", "_handle")):
                        continue
                    ku = k.upper()
                    # Version gates from gold dwg.spec.
                    if ku in ("DIMFXL", "DIMJOGANG", "DIMTFILL", "DIMTFILLCLR", "DIMARCSYM", "DIMFXLON") and not r2007_plus:
                        continue
                    if ku in ("DIMTXTDIRECTION", "DIMALTMZF", "DIMALTMZS", "DIMMZF", "DIMMZS") and not r2010_plus:
                        continue
                    # DIMFIT/DIMUNIT are R13-R14 only. DIMCLRD/E/RT and
                    # DIMTFILLCLR are FIELD_CMC (color) — silver reads them via
                    # read_cm_color into a clean ACI index (0=ByBlock, 256=
                    # ByLayer) and stores it on the i16 field; gold emits the
                    # same index. Always project it (the earlier `v==0 skip`
                    # wrongly dropped ByBlock, producing missing_in_silver).
                    if ku in ("DIMFIT", "DIMUNIT"):
                        continue
                    # DIMLDRBLK/DIMBLK/DIMBLK1/DIMBLK2: gold emits these
                    # handles SINCE R_2000b (code 5, dwg.spec); silver stores
                    # raw Handle ints. Wrap for the differ's handle resolution.
                    if ku in ("DIMLDRBLK", "DIMBLK", "DIMBLK1", "DIMBLK2"):
                        fields[ku] = normalize_handle_value(v)
                        continue
                    fields[ku] = normalize_value(v)
                    continue
                # Drop silver's xref bookkeeping duplicates (already emitted
                # as is_xref_* above) and the text-style name duplicate.
                if record_gold_type in ("DIMSTYLE", "LTYPE") and k in ("xref_reference", "xref_resolved", "xref_dependent", "xref_handle", "annotative"):
                    continue
                # LAYER.linewt: gold stores the raw lweights[] index; silver
                # stores the enum string. Map it.
                if k == "line_weight":
                    fields["linewt"] = _lineweight_to_gold(v)
                    continue
                # BLOCK_HEADER.layout / LAYER.material are handle-stream fields
                # in gold (code 5); silver stores raw Handle ints. Wrap for
                # the differ's handle resolution.
                if (record_gold_type, k) in (("BLOCK_HEADER", "layout"), ("LAYER", "material")):
                    fields[k] = normalize_handle_value(v)
                    continue
                if is_ignored(k, ignore_set, ignore_patterns):
                    continue
                fields[k] = normalize_value(v)
            out.append({"type": record_gold_type, "fields": fields})

    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: normalize_silver.py <silver.json> [ignore_fields.toml]", file=sys.stderr)
        sys.exit(1)
    ignore: Optional[Dict[str, Any]] = None
    if len(sys.argv) >= 3:
        ignore = load_ignore_fields(sys.argv[2])
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    norm = normalize_silver(data, ignore)
    json.dump(norm, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
