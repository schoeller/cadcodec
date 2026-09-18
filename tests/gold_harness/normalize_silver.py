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
            # c_prop33 (edge color): gold's dwg.spec default is 0 (ByBlock);
            # silver stores Color::ByLayer (256). Gold emits 0 on every
            # corpus row, so map silver's ByLayer -> 0 here.
            if name == "c_prop33" and v == 256:
                v = 0
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
        gold_type = OBJECT_TYPE_MAP.get(silver_type, silver_type.upper())
        payload = obj[silver_type]
        if not isinstance(payload, dict):
            continue
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
        if silver_type == "Scale":
            # Gold stores a raw `flag` BS (bit 0x01 = temporary) and does NOT
            # emit the derived `is_temporary` bool; silver stores only the
            # derived bool. Project `flag`; pop is_temporary so the generic
            # payload loop cannot re-emit it (extra_in_silver on every SCALE).
            is_temp = bool(payload.pop("is_temporary", False))
            fields.setdefault("flag", 1 if is_temp else 0)
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
                # LAYER (dwg.spec 3298): silver stores a `flags` bit-struct and
                # color as {Index: n}; gold emits flag0 (the raw RC bitmask) and
                # color as a plain index int, plus plotstyle (handle).
                fl = rec.get("flags")
                if isinstance(fl, dict):
                    bits = fl.get("unknown_bits", 0) & ~0x7F
                    for name, bit in (("frozen", 0), ("off", 1), ("frozen_in_new", 2),
                                      ("locked", 3), ("xref", 4), ("xref_dep", 4),
                                      ("xref_resolved", 5), ("xref_ref", 6),
                                      ("frozen_in_new_vp", 2)):
                        if fl.get(name):
                            bits |= (1 << bit)
                    fields["flag0"] = bits
                    rec.pop("flags", None)
                col = rec.get("color")
                if isinstance(col, dict) and "Index" in col:
                    fields["color"] = col["Index"]
                    rec.pop("color", None)
                # plotstyle: silver stores plotstyle_handle; gold plotstyle.
                if "plotstyle_handle" in rec:
                    fields["plotstyle"] = normalize_handle_value(rec["plotstyle_handle"])
                    rec.pop("plotstyle_handle", None)
                # ltype: silver stores line_type as a NAME string and drops the
                # handle (linetype_handle is null). Gold emits the handle dict.
                # This is a silver READER gap — the normalizer can't recover the
                # handle from a name without a lookup. Leave it missing so the
                # differ reports the real gap.
                if "line_type" in rec:
                    rec.pop("line_type", None)
                # drop silver-only
                for kk in ("plotstyle", "ltype", "plot_style", "book_name", "color_name",
                           "description", "is_plottable", "transparency",
                           "xref_block_record_handle", "material", "material_handle"):
                    rec.pop(kk, None)
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
                    # DIMFIT/DIMUNIT are R13-R14 only. DIMCLRD/E/RT: silver
                    # stores index 0 where gold emits a CMC true-color hash
                    # (R2004+) or index 0 (R2000); skip index 0 on R2004+.
                    if ku in ("DIMFIT", "DIMUNIT"):
                        continue
                    if ku in ("DIMCLRD", "DIMCLRE", "DIMCLRT") and v == 0 and r2004_plus:
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
