from base64 import b64encode
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from math import isclose
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent / "default_parity"))

from PatternDefaultWorker import bridge, check_purity, ready
from PatternParityPacket import check_request, encode, require


FORMAT = "solidworks.sldprt"
NATIVE = {"body_structure", "configurations", "editable_sketches", "parameters", "parametric_history",
          "selections", "support_planes"}


def check_result(result, payload):
    from convert.adapters.base.TransferContract import TransferMode

    require(result.path is None and result.adapter == FORMAT and result.bytes_written == len(payload)
            and result.vendor_loadable and result.application_usable and result.roundtrip_safe
            and not result.dropped and not result.carrier_capabilities and not result.requirements
            and len(result.transfers) == len(NATIVE) and all(item.mode is TransferMode.KNative for item in result.transfers)
            and {item.value for item in result.native_capabilities} == NATIVE,
            "public stream changed its native result contract")


def require_strict(payload, expected, config):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import ReadLength

    restored = open_document(BytesIO(payload), source_format=FORMAT, configuration=config, strict=True)
    require(restored.brep is not None and len(restored.brep.bodies) == len(restored.bodies) == 1
            and restored.configurations[0].name == config, "ordinary strict read lost the joined body or configuration")
    source = expected.feature_timeline[-1]
    probe, = (step for step in restored.feature_timeline if step.id == restored.bodies[0].final_feature_id)
    topology, authored = restored.bodies[0].topology, expected.bodies[0].topology
    counts = ("solid_count", "shell_count", "face_count", "edge_count", "vertex_count")
    pitch, = (parameter for parameter in restored.parameters if parameter.id == probe.parameter_ids[1])
    require(topology.valid is True and all(getattr(topology, key) == getattr(authored, key) for key in counts)
            and probe.name == source.name and type(probe.definition) is type(source.definition)
            and probe.definition.instance_count == source.definition.instance_count
            and pitch.owner_id == probe.id and pitch.value == probe.definition.spacing
            and pitch.attributes.get("native_value") == ReadLength(source.definition.spacing)
            and pitch.attributes.get("native_unit") == "m"
            and isclose(ReadLength(probe.definition.spacing), ReadLength(source.definition.spacing), rel_tol=1e-14)
            and probe.definition.reversed is source.definition.reversed,
            "ordinary strict read disagrees with the frozen configuration, drivers or final topology")


def emit():
    from LocalPatternContainerProcess import audit, linked
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from interchange import CadDocument, PlaneAxis

    request = check_request(ready())
    wire = encode(request["document"])
    target = SelfFileInput(**request["target"])
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(codec)
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut").ReadTime = lambda: target.SavedAt
    audit.BeginBuild()
    document = CadDocument.from_json(wire.decode("utf-8"))
    (config,) = document.configurations
    require(config.active and type(document.feature_timeline[2].definition) is PlaneAxis,
            "exact portable axis and active configuration required")
    registry, direct = BytesIO(), BytesIO()
    values = {"final_destination": target.PathName, "allow_carrier": False, "require_native_transfers": True}
    registered_result = write_document(document, registry, destination_format=FORMAT,
                                       configuration=config.id, allow_carrier=False, values=values)
    direct_result = SldprtAdapter().write(document, direct, WriteOptions(configuration=config.name, values=values))
    payload = registry.getvalue()
    require(payload == direct.getvalue() and encode(document.to_dict()) == wire, "public writer routes differ")
    check_result(registered_result, payload)
    check_result(direct_result, payload)
    archive = SldprtArchive.FromBytes(payload)
    streams = {name: archive.Require(name) for name in archive.Streams}
    link, headers = linked(payload, streams)
    require(len(streams) == 10 and len(link.ResolvedValue.RootsValue) == 24 and len(headers) == 2,
            "typed public output inventory differs")
    require_strict(payload, document, config.name)
    check_purity(audit)
    sys.stdout.buffer.write(encode({
        "payload": b64encode(payload).decode("ascii"), "sha256": sha256(payload).hexdigest(), "bytes": len(payload),
        "streams": {name: sha256(raw).hexdigest() for name, raw in streams.items()}, "root_count": 24,
        "typed_replays": 9, "runtime_reads": len(audit.DeniedReads),
    }))


if __name__ == "__main__":
    if sys.argv[1:] == ["--bridge"]:
        bridge()
    elif sys.argv[1:] == ["--emit"]:
        emit()
    else:
        raise SystemExit("invalid public pattern process mode")
