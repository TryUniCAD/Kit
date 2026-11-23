from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent.parent), str(HERE.parent)]

from AuditKeywordModels import MANIFEST, digest, json_bytes, recovered_documents, require
from ProjectPartDimensions import project_dimensions, read_link
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmXmlRoles import KAsmXmlRoles
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmKeyIndex import KeyIndexOrder
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadImpKeyNodes import KImportKeyRoles
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadRows, RequireRecord
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


def native_rows(archive, link):
    dimensions, parameter_ids = project_dimensions(archive)
    roots = tuple(RequireNative(node) for node in link.ResolvedValue.RootsValue)
    root_fields = link.ConfigValue.RootValue.FieldsValue
    cabinet, = tuple(node for node in roots if node.ClassValue.NameValue == "moDetailCabinet_c")
    environment = RequireNative(root_fields["f1e0"], "moEnvFolder_c")
    manager = RequireNative(root_fields["f13f8"], "moPrtExplViewManager_c")
    require(environment in roots and manager not in roots and root_fields.get("f1018") is None,
            "independent cuboid keyword helpers do not have their witnessed owners")
    require(manager.FieldsValue["f18"] is None,
            "saved cuboid exploded helper unexpectedly has a name")
    nodes = (*roots, *ReadChildren(environment), *ReadChildren(cabinet), manager)
    classes = Counter(node.ClassValue.NameValue for node in nodes)
    require(classes["moProfileFeature_c"] == classes["moExtrusion_c"] == 1 and len(dimensions) == 1
            and tuple(parameter_ids.values()) == ((-1,),),
            "recovered cuboid exceeds its one-driver model")
    rows = []
    for node in nodes:
        kind = node.ClassValue.NameValue
        identity = FieldInt(node.FieldsValue, "f08")
        dissectable = None
        if kind == "moProfileFeature_c":
            tag, label, dissectable = "Sketch", None, True
        elif kind == "moExtrusion_c":
            tag, label = "Extrusion", "Boss-Extrude"
        elif kind in KImportKeyRoles:
            tag, label = KImportKeyRoles[kind]
        else:
            tag, label = KAsmXmlRoles[kind]
        title = "" if node is manager else ReadNativeName(node)
        rows.append(KeywordFeature(identity, title, label, tag, dimensions.get(identity, ()), (), dissectable, None))
    return tuple(sorted(rows, key=KeyIndexOrder)), classes


def make_index(archive):
    require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
            "recovered cuboid archive profile changed")
    linked = read_link(archive)
    model = RequireNative(linked.ConfigValue.RootValue, "moPart_c")
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue.FieldsValue
    selected = RequireNative(manager["f360"], "moPartConfiguration_c")
    entry, = ReadRows(RequireRecord(manager["f370"])["items"])
    require(entry["o"] is selected and manager["f368"] is selected and FieldInt(selected.FieldsValue, "f08") == 0,
            "the active cuboid configuration does not match the complete manager list")
    material, = tuple(node for node in linked.ResolvedValue.RootsValue
                      if node is not None and node.ClassValue.NameValue == "moMaterialFolder_c")
    require(material.FieldsValue["f378"] == "", "the recovered cuboid has assigned material")
    config = KeywordConfig(0, ReadNativeName(selected), ReadNativeName(material))
    header = RequireNative(linked.ConfigValue.HeaderValue.FieldsValue["f38"], "moExtObject_c")
    stamp = FieldInt(RequireRecord(header.FieldsValue["shared"]), "f28")
    rows, classes = native_rows(archive, linked)
    data = MakeKeywords(ReadNativeName(model), stamp, (config,), rows, CompactTags=True, NativeRows=True)
    return data, classes


def main():
    parser = ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    documents = {}
    counts = Counter()
    for path, raw in recovered_documents():
        archive = SldprtArchive.from_bytes(raw)
        built, classes = make_index(archive)
        require(built == archive.require(KeywordsStream), "saved cuboid differs from its binary projection")
        documents[path] = {"document_sha256": digest(raw), "keyword_sha256": digest(built), "keyword_bytes": len(built)}
        counts.update(classes)
    require(len(documents) == 111 and sum(counts.values()) == 2886, "recovered cuboid cohort changed")
    report = {"schema": "kit.sw2026.recovered-cuboid-keyword-owners.v1",
              "input_manifest_sha256": MANIFEST, "script_sha256": sha256(HERE.read_bytes()).hexdigest(),
              "documents": documents, "feature_owners": dict(counts),
              "saved_keyword_used_only_for_final_comparison": True,
              "native_processes_started": 0, "heldout_inputs_read": 0}
    raw = json_bytes(report)
    with args.output.open("xb") as output:
        output.write(raw)
    print(json.dumps({"sha256": digest(raw), "keywords_exact": len(documents), "feature_owners": sum(counts.values())}))


if __name__ == "__main__":
    main()
