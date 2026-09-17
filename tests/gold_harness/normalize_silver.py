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
            fields["linewt"] = v if isinstance(v, int) else 29
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

    # Objects map keyed by handle string.
    for _handle_key, obj in objects.items():
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
        for k, v in payload.items():
            if k in ("handle", "owner", "owner_handle", "reactors", "xdictionary_handle"):
                continue
            if is_ignored(k, ignore_set, ignore_patterns):
                continue
            fields[k] = normalize_value(v)
        out.append({"type": gold_type, "fields": fields})

    # Table records.
    TABLE_SPECS: List[Tuple[str, str, str]] = [
        ("layers", "LAYER", "LAYER"),
        ("line_types", "LTYPE", "LTYPE"),
        ("text_styles", "STYLE", "TEXTSTYLE"),
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
    for table_key, _entry_gold_type, record_gold_type in TABLE_SPECS:
        table = data.get(table_key, {})
        if not isinstance(table, dict):
            continue
        table_handle = normalize_handle_value(table.get("handle"))
        entries = table.get("entries", {})
        for _key, rec in entries.items():
            if not isinstance(rec, dict):
                continue
            fields = _object_common_fields(rec)
            if table_handle is not None:
                fields["ownerhandle"] = table_handle
            fields["is_xref_ref"] = 1
            fields["is_xref_resolved"] = 0
            fields["is_xref_dep"] = 0
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
            for k, v in rec.items():
                if k in ("handle", "owner", "owner_handle", "reactors", "xdictionary_handle"):
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
