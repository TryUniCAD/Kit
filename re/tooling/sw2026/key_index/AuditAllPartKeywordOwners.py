from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from itertools import chain
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent.parent), str(HERE.parent)]
from AuditKeywordModels import (
    SOURCE,
    MANIFEST,
    digest,
    json_bytes,
    require,
    KEYWORDS,
    ReadKeyIndex,
    SldprtArchive,
    pinned_documents,
    recovered_documents,
)
from ProjectPartDimensions import project_dimensions, read_link
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmKeyIndex import (
    KeyIndexOrder,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireRecord,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmXmlRoles import (
    KAsmXmlRoles,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadImpKeyNodes import (
    KImportKeyRoles,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatText import (
    ReadMatText,
)


def material_label(selected, visible, native_profile):
    visual = selected.FieldsValue.get("f78")
    if visual is None:
        return None if native_profile else ""
    raw = ReadMatText(visual.FieldsValue["f20"]["f20"])
    if not raw:
        return None
    if raw == "Steel":
        if visible.FieldsValue["f378"] != "":
            raise ValueError("legacy unassigned material has an assigned folder")
        return ReadNativeName(visible)
    pieces = raw.split("|")
    if len(pieces) not in (2, 3) or not pieces[0] or not pieces[1]:
        raise ValueError("unclassified material identity")
    if len(pieces) == 3:
        _ = int(pieces[2])
    return pieces[1]


def build(a, link):
    root = RequireNative(link.ConfigValue.RootValue, "moPart_c")
    drivers, parameter_ids = project_dimensions(a)
    require(
        all(identity == -1 for values in parameter_ids.values() for identity in values),
        "registered display parameter needs its own index order",
    )
    manager = link.ManagerValue
    if manager is None:
        c = a.require("Contents/CMgr")
        try:
            manager = ReadCmgrMut(c, 19000)
        except ValueError:
            manager = ReadCmgrMut(c, 19000, ReadMaterial=True)
    fields = manager.RootValue.FieldsValue
    active = RequireNative(fields["f360"], "moPartConfiguration_c")
    (selected,) = ReadRows(RequireRecord(fields["f370"])["items"])
    require(
        active is fields["f368"]
        and active is selected["o"]
        and FieldInt(active.FieldsValue, "f08") == 0,
        "the active configuration is outside the saved part keyword profile",
    )
    roots = tuple(RequireNative(node) for node in link.ResolvedValue.RootsValue)
    environment = RequireNative(root.FieldsValue["f1e0"], "moEnvFolder_c")
    require(
        sum(node is environment for node in roots) == 1,
        "saved part environment alias differs",
    )
    material = next(
        node for node in roots if node.ClassValue.NameValue == "moMaterialFolder_c"
    )
    helpers = {key: root.FieldsValue.get(key) for key in ("f1018", "f13f8")}
    profiles = helpers["f13f8"] is not None
    if profiles:
        exploded = RequireNative(helpers["f13f8"], "moPrtExplViewManager_c")
        require(
            exploded not in roots and exploded.FieldsValue["f18"] is None,
            "saved part exploded helper is not its direct nameless owner",
        )
    else:
        require(
            helpers["f1018"] is None
            and sum(n.ClassValue.NameValue == "moBaseBody_c" for n in roots) == 1
            and all(n.ClassValue.NameValue in KImportKeyRoles for n in roots),
            "the legacy lexical branch requires its ordinary local import",
        )
    if helpers["f1018"] is not None:
        sheet = RequireNative(helpers["f1018"], "moSheetMetalMaster_c").FieldsValue
        require(
            sheet["f08"] == -1
            and sheet["f18"] is None
            and sheet["n370"] == 0
            and sheet["f358"] == [],
            "active sheet-metal records are outside the classified helper",
        )
    label = material_label(active, material, profiles)
    typed_conf = KeywordConfig(active.FieldsValue["f08"], ReadNativeName(active), label)
    epoch = link.ConfigValue.HeaderValue.FieldsValue["f38"].FieldsValue["shared"]["f28"]
    nodes = list(roots)
    for node in roots:
        if profiles and node.ClassValue.NameValue in {
            "moEnvFolder_c",
            "moDetailCabinet_c",
        }:
            nodes.extend(ReadChildren(node))
    nodes.extend(node for node in helpers.values() if node is not None)
    rows = []
    for node in nodes:
        k = node.ClassValue.NameValue
        identifier = node.FieldsValue["f08"]
        signal = dissection_root = None
        children = ()
        if k == "moProfileFeature_c":
            tag, native_type, signal = "Sketch", None, True
        elif k == "moExtrusion_c":
            tag, native_type = "Extrusion", "Boss-Extrude"
        elif k == "moICE_c":
            tag, native_type = "Extrusion", None
            selected = tuple(
                parent
                for parent in ReadParents(node)
                if parent.ClassValue.NameValue == "moProfileFeature_c"
            )
            require(
                len(selected) == 1 and selected[0] in roots,
                "a cut dissection row requires its real resolved sketch",
            )
            children = tuple(p.FieldsValue["f08"] for p in selected)
            signal = dissection_root = True
        elif k == "moRevolution_c":
            tag, native_type = "Feature", "Revolve"
        elif k == "moSweep_c":
            tag, native_type = "Feature", "Sweep"
        elif k == "moSheetMetalMaster_c":
            tag, native_type = "Feature", "Sheet-Metal Master"
        elif k == "moBaseBody_c":
            tag, native_type = "Feature", "Imported"
        elif not profiles:
            tag, native_type = "Feature", k
        elif k in KImportKeyRoles:
            tag, native_type = KImportKeyRoles[k]
        else:
            tag, native_type = KAsmXmlRoles[k]
        title = "" if node.FieldsValue.get("f18") is None else ReadNativeName(node)
        rows.append(
            KeywordFeature(
                identifier,
                title,
                native_type,
                tag,
                drivers.get(identifier, ()),
                children,
                signal,
                dissection_root,
            )
        )
    if profiles:
        rows.sort(key=KeyIndexOrder)
    data = MakeKeywords(
        ReadNativeName(root),
        epoch,
        (typed_conf,),
        tuple(rows),
        CompactTags=profiles,
        NativeRows=True,
    )
    return data, len(rows), sum(map(len, parameter_ids.values()))


BINARY = frozenset(
    {
        "Contents/Config-0",
        "Contents/Config-0-ModelHeader",
        "Contents/Config-0-ResolvedFeatures",
        "Contents/CMgr",
    }
)


def order_only(projected, saved):
    left, right = (ReadKeyIndex(data) for data in (projected, saved))
    canonical = lambda index: replace(
        index,
        FeatureValues=tuple(
            replace(
                row,
                DimensionValues=tuple(
                    sorted(row.DimensionValues, key=lambda dim: dim.NameValue)
                ),
            )
            for row in index.FeatureValues
        ),
    )
    require(
        canonical(left).ToBytes() == canonical(right).ToBytes(),
        "complete keyword difference exceeds unregistered dimension order",
    )
    return [
        {
            "identity": a.IdValue,
            "model_order": [row.NameValue for row in a.DimensionValues],
            "saved_order": [row.NameValue for row in b.DimensionValues],
        }
        for a, b in zip(left.FeatureValues, right.FeatureValues, strict=True)
        if a.DimensionValues != b.DimensionValues
    ]


def main():
    parser = ArgumentParser()
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output
    for encoding in ("ascii", "latin-1", "utf-16-le"):
        _ = lookup(encoding)
    audit = {"enabled": False, "required_owner_refusals": 0}

    def no_file_reads(event, args):
        if audit["enabled"] and event == "open":
            raise RuntimeError(f"keyword model accessed a runtime file: {args[0]}")

    sys.addaudithook(no_file_reads)
    counts = Counter()
    documents = {}
    fingerprint = sha256()
    for path, raw in chain(pinned_documents(SOURCE), recovered_documents()):
        if not path.casefold().endswith(".sldprt"):
            continue
        original = SldprtArchive.from_bytes(raw)
        require(
            original.format_version == 4 and ContainerMo(original.streams) == 19000,
            "saved part is outside the measured version",
        )
        records = tuple(
            record
            for record in original.records
            if record.name in BINARY
            or record.name.split("/", 1)[0] == "_MO_VERSION_19000"
        )
        binary_only = replace(original, records=records)
        require(
            set(binary_only.streams) >= BINARY and KEYWORDS not in binary_only.streams,
            "the binary-only input contains the wrong stream roles",
        )
        audit["enabled"] = True
        try:
            projected, features, dimensions = build(binary_only, read_link(binary_only))
            if not documents:
                for name in sorted(BINARY):
                    incomplete = replace(
                        binary_only,
                        records=tuple(
                            record for record in records if record.name != name
                        ),
                    )
                    try:
                        _ = build(incomplete, read_link(incomplete))
                    except SldprtFormat as error:
                        require(
                            str(error) == f"required stream is missing: {name}",
                            "binary owner refusal reported a different error",
                        )
                        audit["required_owner_refusals"] += 1
                    else:
                        raise ValueError(
                            f"keyword model accepted missing binary owner {name}"
                        )
        finally:
            audit["enabled"] = False
        saved = original.require(KEYWORDS)
        row = {
            "saved_keyword_sha256": digest(saved),
            "projected_keyword_sha256": digest(projected),
            "source_sha256": digest(raw),
            "feature_owners": features,
            "parameter_owners": dimensions,
        }
        fingerprint.update(json_bytes((path, row["source_sha256"])))
        if projected == saved:
            counts["complete_streams_exact"] += 1
        else:
            row["dimension_order_variants"] = order_only(projected, saved)
            require(
                row["dimension_order_variants"],
                "different stream has no modeled order variants",
            )
            counts["only_dimension_order_varies"] += 1
        counts.update(
            part_models=1, feature_owners=features, parameter_owners=dimensions
        )
        documents[path] = row
    require(
        counts
        == {
            "complete_streams_exact": 196,
            "only_dimension_order_varies": 7,
            "part_models": 203,
            "feature_owners": 5330,
            "parameter_owners": 309,
        },
        "explicit source model coverage changed",
    )
    require(
        audit["required_owner_refusals"] == len(BINARY),
        "binary owner refusal controls changed",
    )
    result = {
        "schema": "kit.sw2026.saved-part-keyword-owners.v1",
        "tracked_source": SOURCE,
        "recovered_source_sha256": MANIFEST,
        "disclosed_documents_sha256": fingerprint.hexdigest(),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "binary_owners": sorted(BINARY),
        "keyword_available_during_generation": False,
        "statistics": dict(counts),
        "documents": documents,
        "model_runtime_file_reads": 0,
        "required_owner_refusals": audit["required_owner_refusals"],
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
    }
    raw = json_bytes(result)
    with output.open("xb") as target:
        target.write(raw)
    print(json.dumps({"sha256": digest(raw), **result["statistics"]}))


if __name__ == "__main__":
    main()
