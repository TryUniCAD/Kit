from base64 import b64encode
from codecs import lookup
from dataclasses import dataclass, replace
from importlib import import_module
import os
from pathlib import Path, PureWindowsPath
import sys

TOOLS = Path(__file__).resolve().parent
CODE = TOOLS.parent / "Code"


def install_frozen_imports():
    sys.path[0:0] = [str(CODE / "src"), str(CODE), str(TOOLS)]


def produce(request, repository):
    from SealedCylinderModel import geometry_document
    from SealedCylinderPacket import FEATURE, SLOTS, digest, guest_directory, require
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
        FeatureInstant,
    )
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
        SelfFileInput,
    )
    from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import (
        MakeBareImport,
    )
    from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
        LightInput,
    )
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import (
        MakePartRecipe,
    )
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from interchange.Enums.EnumFeatures import FeatureKind
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    require(
        set(request) == {"slot", "guest_root", "epoch", "specification"}
        and request["slot"] in SLOTS
        and type(request["epoch"]) is int
        and 0 < request["epoch"] < 2**31,
        "sealed producer accepts one target and its typed SI recipe",
    )
    root = guest_directory(request["guest_root"])
    target = PureWindowsPath(root) / "Candidates" / (request["slot"] + ".SLDPRT")
    epoch = request["epoch"]

    @dataclass(frozen=True)
    class Labels:
        NameValue: str
        ConfigName: str = "Default"
        FeatureName: str = FEATURE
        PlaneName: str = "Front Plane"
        AxisValue: str = "z"
        SketchName: str = ""

    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "cp1252"):
        lookup(codec)
    for module in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Models.DocumentWalk",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)
    require(
        not any(
            name == "Swapp"
            or name.startswith(("win32com", "pythoncom", "BuildLocalCylinder"))
            for name in sys.modules
        ),
        "CAD automation or historical recipe entered the construction process",
    )
    audit = BuildAudit(repository / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    recording = True

    def deny_io(event, arguments):
        if recording:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError(
                    "sealed constructor attempted native or network access"
                )

    sys.addaudithook(deny_io)
    try:
        neutral = geometry_document(request["specification"])
        labels = Labels(target.stem)
        settings = replace(
            MakePartRecipe(labels, epoch), OutputValue=SelfFileInput(str(target), epoch)
        )
        ambient = LightInput(
            "ambient",
            "Import ambient",
            "KitImportAmbient",
            0.5,
            0.5,
            0.0,
            0x00FFFFFF,
            True,
            False,
            True,
            1.0,
            True,
            16.0,
            None,
            None,
            FeatureInstant(epoch, 0),
        )
        candidate = MakeBareImport(neutral, settings, labels, AmbientValue=ambient)
        payload = candidate.BytesValue
        recovered = open_document(
            payload,
            source_format="solidworks.sldprt",
            strict=True,
            include_tessellation=False,
        )
        shape = recovered.brep
        (feature,) = (
            item
            for item in recovered.feature_timeline
            if item.kind is FeatureKind.IMPORTED
        )
        (body,) = recovered.bodies
        require(
            shape is not None
            and len(shape.bodies) == 1
            and len(shape.faces) == 3
            and len(shape.edges) == len(shape.vertices) == 2
            and shape.bodies[0].design_body_id == body.id
            and body.final_feature_id == feature.id
            and feature.operation is None
            and not recovered.parameters
            and not shape.validate(frozenset({body.id}))
            and len(candidate.StreamsValue) == 12,
            "generated cylinder did not return a complete bound neutral solid",
        )
    finally:
        recording = False
    require(not audit.DeniedReads, "sealed constructor attempted runtime input reads")
    return {
        "slot": request["slot"],
        "sha256": digest(payload),
        "bytes": len(payload),
        "native_path": str(target),
        "feature": FEATURE,
        "feature_id": NativeNodeId(candidate.FeatureValue),
        "payload_base64": b64encode(payload).decode("ascii"),
        "runtime_input_file_reads": len(audit.DeniedReads),
        "native_calls": 0,
        "stream_count": len(candidate.StreamsValue),
    }


def main():
    if os.name != "nt" or not (CODE / "src").is_dir():
        raise ValueError("run the frozen producer only within its Windows packet")
    install_frozen_imports()
    from SealedCylinderPacket import encode, parse

    result = produce(parse(sys.stdin.buffer.read(16384)), CODE)
    sys.stdout.buffer.write(encode(result))


if __name__ == "__main__":
    main()
