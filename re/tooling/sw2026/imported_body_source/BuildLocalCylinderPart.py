from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict
from importlib import import_module
import json
from pathlib import Path, PureWindowsPath
import re

from BuildImportedLocalPart import AUTHORED_AMBIENT, DEFAULT_FEATURE_NAME, EPOCH
from BuildLocalBodyKernel import CASES as PRISMS, prism_model
from BuildLocalCylinder import (
    CASES,
    expected_measures,
    make_neutral,
    measure_neutral,
    make_nodes,
    read_typed,
    verify_graph,
    write_typed,
)
from LocalBodyEnvelope import LocalBody, decode, encode
from LocalBodyKernel import _render_local, fingerprint, require
from ObserveCylinderExchange import GENERATED
from VerifyBareImportPackage import (
    BareLabels,
    ambient_input,
    guard_build,
    recipe,
    verify_graph as verify_part_graph,
)
from convert import open_document
from convert.Geometry.Parasolid import DecodeBrepModel
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrRows import ReadCmgrRows
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.BindImportMut import (
    BindImportMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.BindImportScene import (
    BindImportScene,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.CheckBareImport import (
    CheckBareImport,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.FinishImportMut import (
    FinishImportMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportCandidate import (
    ImportCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.LogImportMut import (
    LogImportMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import (
    MakeBareImport,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeImportKeys import (
    MakeImportKeys,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadImportScene import (
    ReadImportScene,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Partition.ImportHistory.ImportEvent import (
    ImportEvent,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeImportHist import (
    MakeImportHist,
)
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import (
    ReadLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import (
    ReadLocalWrap,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    ReadLocalPay,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.api.ApiContext import KConvertEngine
from interchange import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from para.Partition import frame_payloads, read_partition, write_payloads

ROOT = Path(__file__).resolve().parents[4]
SOLIDWORKS = "solidworks.sldprt"
SCHEMA = "kit.sw2026.bare-cylinder-part-host.v1"
STRICT_DIAGNOSTIC = (
    "SLDPRT local geometry rejected: local body has an unqualified node inventory"
)
OWNING_SOURCES = (
    "re/tooling/sw2026/imported_body_source/BuildLocalCylinder.py",
    "re/tooling/sw2026/imported_body_source/LocalBodyEnvelope.py",
    "re/tooling/sw2026/imported_body_source/LocalBodyKernel.py",
    "re/tooling/sw2026/imported_body_source/VerifyBareImportPackage.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/Imports/MakeBareImport.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/Imports/BindImportMut.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/Imports/FinishImportMut.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/Imports/LogImportMut.py",
    "src/convert/adapters/solidworks/Archive/Construction/Part/EmitPartArchive.py",
    "src/convert/adapters/solidworks/Archive/Partition/ImportHistory/MakeImportHist.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/ReadLocalImport.py",
)


def neutral_document(body):
    return CadDocument(
        CadSource("kit.neutral", "", ""),
        (Configuration("active", "Default", True),),
        (),
        (),
        (),
        (),
        (),
        (),
        brep=body,
    )


def make_part(model, destination):
    require(
        type(destination) is PureWindowsPath
        and destination.is_absolute()
        and destination.suffix == ".SLDPRT",
        "cylinder part needs its explicit native destination",
    )
    raw = _render_local(make_nodes(model))
    _, nodes, offsets = read_typed(raw)
    verify_graph(nodes)
    document = neutral_document(make_neutral(nodes, offsets))
    labels = BareLabels(destination.stem, "Default", DEFAULT_FEATURE_NAME)
    settings = recipe(labels, destination, EPOCH)
    ambient = ambient_input(AUTHORED_AMBIENT, EPOCH)
    scene = ReadImportScene(ambient, ())
    CheckBareImport(document, settings, labels, scene)
    local = encode(LocalBody(labels.FeatureName, raw))
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, labels, allocator)
    target = settings.TargetValue
    history = MakeImportHist(
        target.FileVersion, (ImportEvent.KActivation, ImportEvent.KLocalAttach)
    )
    feature, atom_id = BindImportMut(
        system, allocator, target, labels.FeatureName, history.MarkIds
    )
    BindImportScene(system, scene, target, allocator)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    LogImportMut(feature, headers, settings.HeaderValue)
    FinishImportMut(system, feature, headers, settings)
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    keywords = MakeImportKeys(system, feature, settings.HeaderValue.ModifiedAt, None)
    streams, config, resolved = EmitPartArchive(
        system,
        (*system.FeatureValues, feature),
        headers,
        definition,
        settings,
        keywords,
        BodyMapFields={"n": 0, "fcd8": []},
    )
    streams.update({KLocalBodyStream: local, KPartitionStream: history.BytesValue})
    part = ImportCandidate(
        system,
        feature,
        atom_id,
        headers,
        definition,
        config,
        resolved,
        streams,
        BuildSldprt(streams, FormatVersion=4),
    )
    verify_part_graph(part, labels)
    return part, raw, labels, settings, ambient


def raw_document(blob):
    return KConvertEngine.read(
        blob,
        format_id=SOLIDWORKS,
        options=ReadOptions(
            strict=True,
            include_brep=True,
            include_tessellation=False,
            extract_raw_brep=True,
        ),
    )


def ordered_payloads(blob, archive):
    document = raw_document(blob)
    local, mark = ReadLocalPay(
        document.brep_payloads, archive.require(KPartitionStream)
    )
    group = ReadLocalWrap(archive.require(KLocalBodyStream), local)
    return document, local, group, mark


def read_owners(archive, group, mark):
    version = 19000
    link = ReadNativeLink(archive, 0)
    atom, feature_id = ReadLocalOwner(link, group, mark)
    resolved = link.ResolvedValue
    (feature,) = tuple(
        row for row in resolved.RootsValue if row.ClassValue.NameValue == "moBaseBody_c"
    )
    owner = link.ConfigValue.RootValue
    header = link.ConfigValue.HeaderValue
    top_header = ReadHeaderGraph(archive.require("Header2"), version)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), version).RootValue
    (configuration,) = ReadCmgrRows(manager)
    require(
        manager.FieldsValue["f360"] is manager.FieldsValue["f368"] is configuration
        and ReadNativeName(configuration) == "Default"
        and configuration.FieldsValue["f6f8"] == 1
        and header.FieldsValue["f40"]
        == top_header.FieldsValue["f40"]
        == configuration.FieldsValue["f860"]
        and header.FieldsValue["f44"] == top_header.FieldsValue["f44"]
        and feature.FieldsValue["f29c"] == configuration.FieldsValue["f860"],
        "readback lost its completed configuration and both header stamps",
    )
    require(
        feature.FieldsValue["source_filename"] == ""
        and feature.FieldsValue["local_body_switch"] == 1
        and feature.FieldsValue["segment_mesh_count"] == 0
        and atom.FieldsValue["f180"] == atom.FieldsValue["f1b0"] == 0
        and atom.FieldsValue["f19c"] == 6,
        "readback lost the ordinary fresh local feature or atom route",
    )
    partition_bytes = archive.require(KPartitionStream)
    partition = read_partition(partition_bytes)
    activation = owner.FieldsValue["fe38"].FieldsValue["f18"]
    require(
        partition.nodes[0].fields["body"] == 0
        and [item.mark.fields["id"] for item in partition.history]
        == [mark, 1, activation]
        and all(
            not item.mark.fields[n]
            for item in partition.history
            for n in ("n_new_nodes", "n_del_nodes", "n_copy_mod_nodes")
        )
        and frame_payloads(write_payloads(partition)) == partition_bytes,
        "readback lost the body-free activation and local attachment history",
    )
    config_bytes, config = WriteConfigMut(owner, version, header)
    resolved_bytes, _ = WriteResolMut(
        resolved.RootsValue,
        resolved.ExtraFields,
        version,
        config.MapValue,
        resolved.ContextValue,
    )
    checked = {
        link.ConfigName: config_bytes,
        link.StreamName: resolved_bytes,
        "Contents/CMgr": WriteCmgrMut(manager, version),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(header, version),
        "Header2": WriteHeadGraph(top_header, version),
    }
    require(
        all(archive.require(name) == data for name, data in checked.items()),
        "the linked part archive graph failed exact typed replay",
    )
    return {
        "feature_id": feature_id,
        "configured_body_count": configuration.FieldsValue["f6f8"],
        "atom_id": atom.FieldsValue["f140"],
        "atom_map_index": atom.IndexValue,
        "atom_body_tag": atom.FieldsValue["f180"],
        "atom_display_mode": atom.FieldsValue["f19c"],
        "local_group": group,
        "activation_mark": activation,
        "selected_mark": mark,
        "model_update": header.FieldsValue["f40"],
        "body_stamp": header.FieldsValue["f44"],
        "typed_stream_replay": sorted(checked),
    }


def read_public(blob, owners, raw_intake):
    settings = {
        "source_format": SOLIDWORKS,
        "strict": True,
        "include_tessellation": False,
    }
    metadata = open_document(blob, include_brep=False, **settings)
    (configuration,) = metadata.configurations
    steps = tuple(
        step for step in metadata.feature_timeline if step.kind == FeatureKind.IMPORTED
    )
    feature_id = f"sldprt:feature:{owners['feature_id']}"
    require(
        len(steps) == 1
        and steps[0].id == feature_id
        and steps[0].name == owners["local_group"]
        and configuration.name == "Default"
        and configuration.active,
        "metadata-only read lost the actual local feature or configuration",
    )
    require(
        raw_intake.brep is None
        and all(
            payload.data is not None and DecodeBrepModel(payload.data) is None
            for payload in raw_intake.brep_payloads
        ),
        "ordinary decoder changed its bare cylinder payload precedence",
    )
    try:
        open_document(blob, include_brep=True, **settings)
    except SldprtFormat as error:
        require(
            str(error) == STRICT_DIAGNOSTIC,
            f"unexpected strict reader frontier: {error}",
        )
    else:
        raise ValueError("the planar SDK loader unexpectedly admitted a bare cylinder")
    return {
        "metadata_feature_id": feature_id,
        "raw_payloads": [
            [payload.source_stream, payload.kind, fingerprint(payload.data)]
            for payload in raw_intake.brep_payloads
        ],
        "ordinary_geometry_decoders": 0,
        "strict_geometry_refusal": STRICT_DIAGNOSTIC,
    }


def read_part(part, raw):
    archive = SldprtArchive.from_bytes(part.BytesValue)
    require(
        archive.format_version == 4 and archive.streams == part.StreamsValue,
        "generated ordinary part changed its logical streams",
    )
    intake, selected, group, mark = ordered_payloads(part.BytesValue, archive)
    envelope = decode(archive.require(KLocalBodyStream))
    require(
        envelope == LocalBody(group, selected) and selected == raw,
        "archive selected a different model-generated periodic kernel",
    )
    owners = read_owners(archive, group, mark)
    header, nodes, offsets = read_typed(selected)
    verify_graph(nodes)
    require(
        write_typed(header, nodes) == selected,
        "typed cylinder replay differs after archive attachment",
    )
    counts, measured = measure_neutral(make_neutral(nodes, offsets))
    public = read_public(part.BytesValue, owners, intake)
    return {
        "owners": owners,
        "public_read_boundary": public,
        "typed_kernel_replay": True,
        "resident_nodes": len(nodes),
        "brep_counts": counts,
        "measured": measured,
    }


def planar_delta(part, labels, settings, ambient):
    points, levels, _ = PRISMS["Rectangular"]
    planar = neutral_document(prism_model("IndependentPlanarControl", points, levels))
    control = MakeBareImport(planar, settings, labels, AmbientValue=ambient)
    actual = part.StreamsValue
    require(
        actual.keys() == control.StreamsValue.keys(),
        "same-locator planar control changed the ordinary archive inventory",
    )
    changed = sorted(
        name for name in actual if actual[name] != control.StreamsValue[name]
    )
    require(
        changed == [KLocalBodyStream],
        "shape change leaked into completed archive ownership",
    )
    normal = open_document(
        control.BytesValue,
        source_format=SOLIDWORKS,
        strict=True,
        include_brep=True,
        include_tessellation=False,
    )
    require(
        normal.brep is not None
        and len(normal.brep.faces) == 6
        and normal.bodies[0].topology.solid_count == 1,
        "same-locator planar positive control failed",
    )
    return {
        "changed": changed,
        "part": fingerprint(control.BytesValue),
        "reader_solid_count": normal.bodies[0].topology.solid_count,
    }


def case_report(name, model, directory):
    destination = directory / "Candidates" / (name + ".SLDPRT")
    part, raw, labels, settings, ambient = make_part(model, destination)
    require(
        fingerprint(raw) == {"bytes": 1414, "sha256": GENERATED[name]},
        "part did not use the exact model-generated raw exchange candidate",
    )
    control = planar_delta(part, labels, settings, ambient)
    readback = read_part(part, raw)
    expected = expected_measures(model)
    require(
        readback["measured"] == expected,
        "part attachment changed the independent cylinder geometry",
    )
    return part.BytesValue, {
        "native_path": str(destination),
        "feature": labels.FeatureName,
        "configuration": labels.ConfigName,
        "input": asdict(model),
        "kernel": fingerprint(raw),
        "part": fingerprint(part.BytesValue),
        "expected_mm": expected,
        "readback": readback,
        "same_locator_planar_control": control,
        "streams": {
            name: fingerprint(data) for name, data in part.StreamsValue.items()
        },
    }


def broken_owners(blob):
    archive = SldprtArchive.from_bytes(blob)
    local = decode(archive.require(KLocalBodyStream))
    broken_group = dict(archive.streams) | {
        KLocalBodyStream: encode(LocalBody("Unowned group", local.kernel_stream))
    }
    missing_partition = {
        name: value
        for name, value in archive.streams.items()
        if name != KPartitionStream
    }
    refused = {}
    for name, streams, reason in (
        (
            "missing_partition",
            missing_partition,
            "local body rollback history is missing",
        ),
        (
            "wrong_group",
            broken_group,
            "native feature does not own the stored local group and mark",
        ),
    ):
        data = BuildSldprt(streams, FormatVersion=4)
        invalid = SldprtArchive.from_bytes(data)
        try:
            if name == "missing_partition":
                ReadLocalPay(raw_document(data).brep_payloads)
            else:
                _, _, group, mark = ordered_payloads(data, invalid)
                read_owners(invalid, group, mark)
        except ValueError as error:
            require(
                str(error) == reason,
                f"archive control reached a different guard: {error}",
            )
            refused[name] = str(error)
        else:
            raise ValueError(f"archive owner gate accepted {name}")
    return refused


def main():
    parser = ArgumentParser(
        description="Generate and inspect a completed local cylinder part in memory"
    )
    parser.add_argument("native_root")
    parser.add_argument("--artifacts", type=Path)
    args = parser.parse_args()
    require(
        re.fullmatch(r"C:\\KitCylinderPart[0-9]{2}", args.native_root),
        "specify a new C:\\KitCylinderPartNN native root",
    )
    directory = PureWindowsPath(args.native_root)
    destination = args.artifacts.resolve() if args.artifacts is not None else None
    if destination is not None:
        require(
            not args.artifacts.is_symlink()
            and not destination.exists()
            and not destination.is_relative_to(ROOT),
            "use an unused artifact directory outside Kit",
        )
    for codec in ("ascii", "latin-1", "utf-8", "utf-16-le", "cp1252"):
        lookup(codec)
    for module in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Models.DocumentWalk",
    ):
        import_module(module)
    with guard_build():
        reports = {
            name: case_report(name, model, directory) for name, model in CASES.items()
        }
        require(
            len({result["part"]["sha256"] for _, result in reports.values()})
            == len(reports),
            "different source cylinders generated the same part bytes",
        )
        refusals = broken_owners(reports["TranslatedZ"][0])
    if destination is not None:
        destination.mkdir()
        for name, (data, _) in reports.items():
            with (destination / (name + ".SLDPRT")).open("xb") as handle:
                handle.write(data)
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "observer": fingerprint(Path(__file__).read_bytes()),
                "owning_sources_sha256": {
                    name: fingerprint((ROOT / name).read_bytes())["sha256"]
                    for name in OWNING_SOURCES
                },
                "construction_runtime_reads": 0,
                "embedded_native_processes": 0,
                "embedded_native_acceptance": False,
                "public_writer_qualified": False,
                "heldout_cases": 0,
                "cases": {name: report for name, (_, report) in reports.items()},
                "owner_refusals": refusals,
            },
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
