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
    "Associative": "UNKNOWN",
    "ClassObject": "UNKNOWN",
    "DataObject": "UNKNOWN",
    "Field": "FIELD",
    "FieldList": "FIELDLIST",
    "RegisteredClass": "UNKNOWN",
    "DgnLineStyle": "UNKNOWN",
    "ProxyObject": "UNKNOWN",
    "Unknown": "UNKNOWN",
}

# Per-silver-type field-name overrides to match gold vocabulary.
FIELD_NAME_MAP: Dict[str, Dict[str, str]] = {
    "Line": {"normal": "extrusion", "start": "start", "end": "end", "thickness": "thickness"},
    "Circle": {"normal": "extrusion", "center": "center", "radius": "radius", "thickness": "thickness"},
    "Arc": {"normal": "extrusion", "center": "center", "radius": "radius", "start_angle": "start_angle", "end_angle": "end_angle", "thickness": "thickness"},
    "Ellipse": {"normal": "extrusion", "center": "center", "major_axis": "major_axis", "minor_to_major_ratio": "axis_ratio", "start_parameter": "start_param", "end_parameter": "end_param"},
    "Point": {"location": "point"},
    "Text": {"normal": "extrusion", "insertion_point": "insertion_pt", "alignment_point": "alignment_pt", "value": "text_value"},
    "MText": {"normal": "extrusion", "insertion_point": "insertion_pt", "value": "text_value"},
    "LwPolyline": {"normal": "extrusion"},
    "Polyline2D": {"normal": "extrusion"},
    "Polyline3D": {"normal": "extrusion"},
    "Spline": {"normal": "extrusion"},
    "Hatch": {"normal": "extrusion"},
    "Insert": {"normal": "extrusion", "insertion_point": "insertion_pt", "block_name": "name"},
    "Block": {"base_point": "base_pt", "name": "name"},
    "BlockEnd": {},
    "Seqend": {},
    "Ray": {"normal": "extrusion", "start_point": "start_pt", "unit_direction": "direction"},
    "XLine": {"normal": "extrusion", "start_point": "start_pt", "unit_direction": "direction"},
    "Leader": {"normal": "extrusion"},
    "MLine": {"normal": "extrusion"},
    "Helix": {"normal": "extrusion"},
    "Solid": {"normal": "extrusion"},
    "Face3D": {"normal": "extrusion"},
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
    """Turn a silver handle int/None into a gold-style handle dict."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return {"code": 0, "size": 0, "value": value, "absref": value}
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
                for sk, sv in sub.items():
                    if sk == "texture":
                        continue
                    gk = _MATERIAL_MAP_FIELD.get(sk, sk)
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
            fields[name] = _vs_property_value(ext[i])
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

    # DWG/DXF version string, e.g. "AC1015". AC1018 (R2004) introduced the
    # `is_xdic_missing` bit and AC1027 (R2013) the `has_ds_data` bit on every
    # object handle stream (common_object_handle_data.spec SINCE R_2004a /
    # SINCE R_2013). Both are emitted for objects and table records alike.
    version = data.get("version", "")
    r2004_plus = isinstance(version, str) and version >= "AC1018"
    r2007_plus = isinstance(version, str) and version >= "AC1021"
    r2010_plus = isinstance(version, str) and version >= "AC1024"
    r2013_plus = isinstance(version, str) and version >= "AC1027"

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

        field_map = FIELD_NAME_MAP.get(silver_type, {})
        for k, v in payload.items():
            if k == "common":
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
        gold_type = OBJECT_TYPE_MAP.get(silver_type, silver_type.upper())
        payload = obj[silver_type]
        if not isinstance(payload, dict):
            continue
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
        if silver_type == "Scale":
            # Gold stores a raw `flag` BS (bit 0x01 = temporary); silver stores
            # the derived is_temporary bool. Project `flag` and emit
            # is_temporary as gold's int (0/1).
            is_temp = bool(payload.get("is_temporary"))
            fields.setdefault("flag", 1 if is_temp else 0)
            fields["is_temporary"] = 1 if is_temp else 0
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
        # Silver-only top-level VisualStyle fields that gold stores inside the
        # property bag or under a different name; skip so they don't appear as
        # extra_in_silver. The pre-R2010 top-level face_*/edge_* fields ARE
        # gold fields (read into the struct, not the bag), so keep them.
        vs_skip = {
            "properties", "internal_use_only", "extended_lighting_model",
        } if silver_type == "VisualStyle" else set()
        mat_consumed = _map_material(payload, fields, r2007_plus, r2010_plus) if silver_type == "Material" else set()
        for k, v in payload.items():
            if k in ("handle", "owner", "owner_handle", "reactors", "xdictionary_handle"):
                continue
            if k in vs_skip or k in mat_consumed:
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
            for k, v in rec.items():
                if k in ("handle", "owner", "owner_handle", "reactors", "xdictionary_handle"):
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
                    # DIMFIT/DIMUNIT are R13-R14 only. DIMCLRD/E/RT: silver
                    # stores index 0 where gold emits a CMC true-color hash
                    # (R2004+) or index 0 (R2000); skip index 0 on R2004+.
                    if ku in ("DIMFIT", "DIMUNIT"):
                        continue
                    if ku in ("DIMCLRD", "DIMCLRE", "DIMCLRT") and v == 0 and r2004_plus:
                        continue
                    fields[ku] = normalize_value(v)
                    continue
                # Drop silver's xref bookkeeping duplicates (already emitted
                # as is_xref_* above) and the text-style name duplicate.
                if record_gold_type == "DIMSTYLE" and k in ("xref_reference", "xref_resolved", "xref_dependent", "xref_handle", "annotative"):
                    continue
                # LAYER.linewt: gold stores the raw lweights[] index; silver
                # stores the enum string. Map it.
                if k == "line_weight":
                    fields["linewt"] = _lineweight_to_gold(v)
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
