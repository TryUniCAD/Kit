import dataclasses
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from DecodeControls import NAMES
from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.formats.Fusion.DocumentCodec.Records.MakeDesignProf import MakeDesignProf
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

CONTROLS = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Controls"
SOURCES = ("Fillet", "Chamfer", "Shell", "ExtrudeCut", "RectPattern", "MirrorBody", "MultiFeature")
TARGET = REPO / "src/convert/formats/Fusion/DocumentCodec/PartFeatures/Vocabulary"
ROOT = "98542EB9-A4F2-4137-A808-DBB5B3CD6159"
AUTHORED = {"ASMRecipe", "BrepProgenitor", "BrepRef", "DcChamferData", "DcChamferFeature", "DcFilletEdgeData", "DcFilletEdgeFeature", "DcShellFeature", "ETCachedCurve3d"}


def known_guids():
    result = set()
    for vocab in (REPO / "src/convert/formats/Fusion/DocumentCodec").rglob("*Classes.json"):
        if "PartFeatures" in vocab.parts:
            continue
        for entry in json.loads(vocab.read_text()):
            result.add(entry["ClassGuid"].upper())
    return result


def wire_json(shape):
    result = {"KindValue": shape.KindValue}
    if shape.Arguments:
        result["Arguments"] = [wire_json(a) for a in shape.Arguments]
    if shape.Members:
        result["Members"] = [field_json(m) for m in shape.Members]
    if shape.ClassGuid:
        result["ClassGuid"] = shape.ClassGuid
    if shape.FixedCount:
        result["FixedCount"] = shape.FixedCount
    if shape.AllowedInts:
        result["AllowedInts"] = list(shape.AllowedInts)
    if shape.HasMatrixRows:
        result["HasMatrixRows"] = True
    return result


def field_json(member):
    return {"FieldName": member.FieldName, "ValueType": wire_json(member.ValueType), "IsSaved": member.IsSaved}


def class_name(guid, is_value):
    name = NAMES[guid.upper()]
    if is_value and name.endswith("MetaType"):
        name = name[: -len("MetaType")]
    return name


def author_value(value, shape, catalog_names):
    kind = type(value).__name__
    if value is None:
        return None
    if kind in ("LocalRef", "SegmentRef"):
        return None
    if kind == "OptionalValue":
        inner = author_value(value.Value, shape.Arguments[0], catalog_names)
        return inner
    if kind == "ValueSeries":
        if shape.Arguments and shape.Arguments[0].KindValue == "ref":
            return []
        return [author_value(v, shape.Arguments[0], catalog_names) for v in value.Items]
    if kind == "ValueMap":
        if any(a.KindValue == "ref" for a in shape.Arguments):
            return []
        return [{"key": author_value(p.First, shape.Arguments[0], catalog_names), "value": author_value(p.Second, shape.Arguments[1], catalog_names)} for p in value.Entries]
    if kind == "ValuePair":
        return {"first": author_value(value.First, shape.Arguments[0], catalog_names), "second": author_value(value.Second, shape.Arguments[1], catalog_names)}
    if kind == "ValueStruct":
        members = {m.FieldName: m for m in shape.Members}
        if shape.KindValue == "sketch-tag":
            return {f.FieldName: f.Value for f in value.Fields}
        return {f.FieldName: author_value(f.Value, members[f.FieldName].ValueType, catalog_names) for f in value.Fields}
    if kind == "ValueObject":
        groups = []
        for group in value.Groups:
            schema = catalog_names[group.ClassGuid.upper()]
            members = {m.FieldName: m for m in schema.Members}
            groups.append({"identifier": group.ClassGuid, "fields": {f.FieldName: author_value(f.Value, members[f.FieldName].ValueType, catalog_names) for f in group.Fields}})
        return groups
    if kind == "MatrixValue":
        if value.Entries is None:
            return {"identity": True}
        raise ValueError("non-identity matrix default")
    if kind == "RecipeValue":
        return None
    if dataclasses.is_dataclass(value):
        raise ValueError("unhandled " + kind)
    if isinstance(value, float) and value != value:
        raise ValueError("nan default")
    return value


def main():
    known = known_guids()
    catalog = DocumentCatalog(ReadDocSchemas())
    selected = {}
    spaces = {}
    defaults = {}
    for source in SOURCES:
        with OpenFusionZip((CONTROLS / (source + ".f3d")).read_bytes()) as archive:
            members = [m.Name for m in archive.Members]
            meta_name = next(n for n in members if n.endswith("MetaStream.dat") and "FusionDesignSegmentType" in n)
            bulk_name = meta_name.replace("MetaStream.dat", "BulkStream.dat")
            meta_bytes = archive.ReadMember(meta_name, 1 << 26)
            bulk = archive.ReadMember(bulk_name, 1 << 26)
            others = [ReadMetaWire(archive.ReadMember(n, 1 << 26)) for n in members if n.endswith("MetaStream.dat") and n != meta_name]
        metadata = ReadMetaWire(meta_bytes)
        targets = tuple(ExternalTarget(s.Header.SegmentId, oid, e.ClassGuid) for s in others for e in s.Classes for oid in e.OwnerIds)
        records = tuple(BulkRecord(s.TypeCode, s.ObjectId, s.IsPrimary, bulk[s.PayloadOffset:s.EndOffset]) for s in ReadBulkSpans(bulk, meta_bytes))
        versions = {c.ClassGuid.upper(): c for c in metadata.Classes}
        for guid, row in versions.items():
            if guid in known or guid in selected:
                continue
            schema = next(s for s in catalog.Classes[guid] if s.SchemaVersion == row.SchemaVersion)
            selected[guid] = schema
            spaces[guid] = row.ClassSpace
        by_guid = {}
        for guid, row in versions.items():
            by_guid[guid] = next(s for s in catalog.Classes[guid] if s.SchemaVersion == row.SchemaVersion)
        profile = MakeDesignProf(ReadDocSchemas(), metadata.Classes, targets)
        for entity in DecodeEntities(records, metadata.Classes, profile):
            for group in entity.Groups:
                guid = group.ClassGuid.upper()
                if guid not in selected:
                    continue
                name = class_name(guid, selected[guid].IsValue)
                if name in defaults:
                    continue
                members = {m.FieldName: m for m in by_guid[guid].Members}
                defaults[name] = {f.FieldName: author_value(f.Value, members[f.FieldName].ValueType, by_guid) for f in group.Fields}
    missing = [g for g, s in selected.items() if s.BaseGuid.upper() not in known and s.BaseGuid.upper() not in selected and s.BaseGuid.upper() != ROOT and s.BaseGuid]
    if missing:
        raise ValueError("lineage gap " + repr(missing))
    vocabulary = []
    for guid in sorted(selected):
        schema = selected[guid]
        name = class_name(guid, schema.IsValue)
        vocabulary.append({"ClassGuid": schema.ClassGuid, "BaseGuid": schema.BaseGuid, "SchemaVersion": schema.SchemaVersion, "Members": [field_json(m) for m in schema.Members], "IsValue": schema.IsValue, "NameValue": name, "ClassSpace": spaces[guid]})
        if any(m.IsSaved for m in schema.Members) and name not in defaults:
            if schema.IsValue:
                continue
            raise ValueError("no native default for " + name)
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "FeatureClasses.json").write_text(json.dumps(vocabulary, indent=2) + "\n")
    ordered = {name: defaults[name] for name in sorted(defaults) if name in AUTHORED}
    (TARGET / "FeatureDefaults.json").write_text(json.dumps(ordered, indent=2, sort_keys=True) + "\n")
    print(len(vocabulary), "classes", len(ordered), "defaults")
    print(sorted(e["NameValue"] for e in vocabulary))


if __name__ == "__main__":
    main()
