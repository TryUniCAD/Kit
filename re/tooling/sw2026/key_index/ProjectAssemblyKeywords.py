from pathlib import PureWindowsPath

from AuditKeywordCorpus import require
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmXmlRoles import KAsmXmlRoles
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmKeyIndex import EmitAsmKeyIndex, MakeAsmKeyRef
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadRows, RequireNode, RequireRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def feature_owners(model, resolved):
    environment = RequireNode(model.FieldsValue.get("f1e0"), "moEnvFolder_c")
    require(sum(node is environment for node in resolved) == 1, "resolved environment alias differs")
    cabinets = tuple(node for node in resolved if node.ClassValue.NameValue == "moDetailCabinet_c")
    require(len(cabinets) == 1, "resolved annotation cabinet is ambiguous")
    lights = ReadChildren(environment)
    notes = ReadChildren(cabinets[0])
    require(all(node.ClassValue.NameValue in {"moAmbientLight_c", "moDirectionLight_c"} for node in lights)
            and all(node.ClassValue.NameValue == "moNotesAreaFtrFolder_c" for node in notes),
            "saved presentation folder has an unclassified child")
    exploded = RequireNode(model.FieldsValue.get("f1590"), "moExplViewManager_c")
    require(exploded not in resolved, "exploded manager duplicates a resolved root")
    require(model.FieldsValue.get("f1598") == 0 and all(exploded.FieldsValue.get(key) == value
            for key, value in (("f358", None), ("f360", None), ("f368", {"n": 0, "items": []}),
                               ("f398", 0.0), ("f3a0", -1), ("f3a4", -1))) and not ReadChildren(exploded),
            "saved exploded manager has unclassified placement records")
    owners = (*resolved, *lights, *notes, exploded)
    require(all(node.ClassValue.NameValue in KAsmXmlRoles for node in owners),
            "saved hierarchy contains an unclassified keyword owner")
    return owners


def occurrence_rows(model):
    owner = model.FieldsValue.get("f68")
    present = FieldInt(model.FieldsValue, "has_list68")
    if present == 0:
        require(owner is None, "inactive occurrence table has entries")
        return ()
    require(present == 1, "unsupported occurrence table presence flag")
    listed = RequireRecord(RequireRecord(owner)["list"])
    rows = []
    for entry in ReadRows(listed["items"]):
        occurrence = RequireNode(entry["o"], "moReference_c")
        target = RequireNode(occurrence.FieldsValue["f3b0"], "moExtObject_c")
        logical, _, kind, _ = ReadFileKey(target)
        path = PureWindowsPath(logical)
        require(kind == 2 and path.name == logical and path.suffix.casefold() in {"", ".sldprt"},
                "saved occurrence does not target a named part")
        rows.append(MakeAsmKeyRef(occurrence, logical))
    require(FieldInt(listed, "n") == len(rows), "saved occurrence count differs")
    return tuple(rows)


def project_index(model, resolved, header, manager):
    model = RequireNode(model, "moAssembly_c")
    active_config = RequireNode(manager.FieldsValue["f360"], "moConfiguration_c")
    require(FieldInt(active_config.FieldsValue, "f08") == FieldInt(model.FieldsValue, "f08"),
            "assembly and selected configuration identities differ")
    owners = feature_owners(model, resolved)
    references = occurrence_rows(model)
    return EmitAsmKeyIndex(model, header, active_config, owners, references), len(owners), len(references)


def read_index_graph(archive):
    linked = ReadNativeLink(archive, 0)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    return linked.ConfigValue.RootValue, linked.ResolvedValue.RootsValue, linked.ConfigValue.HeaderValue, manager
