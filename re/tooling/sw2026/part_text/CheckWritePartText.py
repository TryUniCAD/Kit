from dataclasses import replace
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PartTextProbe import (
    PROPERTY_DIAGNOSTIC, PROPERTY_STATUS, check_model, model_state, read_part, refuse_write,
)
from PropPolicyControl import CAUSE, unknown_policy
from convert import convert, open_document, write_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.api.ApiContext import GetRegistry
from convert.engine.EngineConvert import EngineConvert
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Severity
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordSource import CadSource
from interchange.Records.RecordTopology import TopologyCounts

MANAGER = "Contents/CusProps"


def authored_snapshot():
    body_id, feature_id = "portable:body", "portable:import"
    points = tuple(PlaneVector(*xy) for xy in ((-1, 2), (3, 2), (3, 5), (-1, 5)))
    profile = tuple(LineGeometry(a, b) for a, b in zip(points, points[1:] + points[:1], strict=True))
    geometry, volume, area, bounds = BuildPrism(body_id, KTransformIdentity, profile, 0.0, 2.5)
    topology = TopologyCounts(1, 1, len(geometry.faces), len(geometry.edges),
                              len(geometry.vertices), volume, area, bounds, True)
    source = CadSource("solidworks.sldprt", "authored neutral inspection control", "",
                       attributes={"authored_test_control": True})
    owner = Configuration("portable:config", "Inspection", active=True,
                          attributes={"native_configuration_id": 0})
    import_feature = FeatureStep(feature_id, "Imported prism", FeatureKind.IMPORTED, 0,
                                 operation=BooleanOp.CREATE)
    report = Diagnostic(code=PROPERTY_DIAGNOSTIC, message=CAUSE, severity=Severity.INFO)
    assert (volume, area) == (30.0, 59.0)
    return CadDocument(
        source=source,
        configurations=(owner,),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(import_feature,),
        bodies=(DesignBody(body_id, "Prism", feature_id, topology),),
        diagnostics=(report,),
        metadata={PROPERTY_STATUS: {"status": "unsupported", "diagnostic": CAUSE}},
        brep=geometry,
    )


def native_copy_refusals(document, legacy):
    source = document.to_json().encode("utf-8")
    operations = {
        "ordinary": partial(convert, source, source_format="interchange.json", destination_format="interchange.json"),
        "compatibility": partial(legacy.ConvertData, source, SourceFormat="interchange.json", DestFormat="interchange.json"),
    }
    return {
        mode: refuse_write(call, CAUSE)
        for mode, call in operations.items()
    }


def check_neutral_copy(document, legacy):
    source = document.to_json().encode("utf-8")
    restored = open_document(source, source_format="interchange.json", strict=True)
    if restored != document:
        raise ValueError("neutral JSON inspection changed the full authored inspection document")
    relabeled = replace(document, source=replace(document.source, format_id="interchange.json"))
    operations = {
        "ordinary": partial(convert, source, source_format="interchange.json",
                            destination_format="interchange.json", allow_carrier=False),
        "compatibility": partial(legacy.ConvertData, source, SourceFormat="interchange.json",
                                 DestFormat="interchange.json"),
        "source_relabel": partial(write_document, relabeled, destination_format="interchange.json"),
    }
    return {mode: refuse_write(call, CAUSE) for mode, call in operations.items()}


def check_filtered_copy(document):
    source = document.to_json().encode()
    options = {"source_format": "interchange.json", "destination_format": "interchange.json"}
    restrictions = {"geometry": {"include_brep": False}, "mesh": {"include_tessellation": False},
                    "configuration": {"configuration": document.configurations[0].name}}
    return {name: refuse_write(partial(convert, source, **options, **selected), CAUSE)
            for name, selected in restrictions.items()}


def inspect(source):
    raw = source.read_bytes()
    streams = SldprtArchive.from_bytes(raw).streams
    original_manager = streams[MANAGER]
    streams[MANAGER] = unknown_policy(original_manager)
    changed = BuildSldprt(streams, Template=raw)
    if SldprtArchive.from_bytes(changed).streams != streams:
        raise ValueError("the policy control changed unrelated part streams")
    document = read_part(changed)
    relaxed = read_part(changed, strict=False)
    check_model(read_part(raw), document)
    check_model(document, relaxed)
    state = model_state(document)
    if state != model_state(relaxed):
        raise ValueError("nonstrict inspection changed the explicit property refusal")
    registry = GetRegistry()
    legacy = EngineConvert()
    legacy.registry = registry
    options = {
        "source_format": "solidworks.sldprt",
        "destination_format": "interchange.json",
        "include_tessellation": False,
    }
    operations = {
        "strict": partial(convert, changed, **options),
        "nonstrict": partial(convert, changed, strict=False, **options),
        "public_write": partial(
            write_document, relaxed, destination_format="interchange.json",
            validate=False, allow_carrier=True,
        ),
        "registry": partial(registry.write, relaxed, format_id="interchange.json"),
        "compatibility": partial(
            legacy.ConvertData, changed, SourceFormat="solidworks.sldprt",
            DestFormat="interchange.json", ReadOpts=ReadOptions(
                strict=False, include_tessellation=False,
            ),
        ),
    }
    refusals = {name: refuse_write(call, CAUSE) for name, call in operations.items()}
    with TemporaryDirectory(prefix="KitRefusedPartText") as scratch:
        destination = Path(scratch) / "part.json"
        try:
            write_document(relaxed, destination)
        except ValueError as error:
            if str(error) != refusals["public_write"] or any(Path(scratch).iterdir()):
                raise ValueError("implicit path refusal changed its destination") from error
        else:
            raise ValueError("implicit path published unsupported text")
    if source.read_bytes() != raw:
        raise ValueError("native source changed")
    state["source_sha256"] = sha256(raw).hexdigest()
    state["original_manager_sha256"] = sha256(original_manager).hexdigest()
    state["changed_manager_sha256"] = sha256(streams[MANAGER]).hexdigest()
    state["geometry_equal"] = True
    state["refusals"] = refusals
    state["implicit_path_unchanged"] = True
    state["native_copy_refusals"] = native_copy_refusals(document, legacy)
    snapshot = authored_snapshot()
    state["neutral_snapshot"] = model_state(snapshot)
    state["neutral_copies_refused"] = check_neutral_copy(snapshot, legacy)
    state["filtered_copies_refused"] = check_filtered_copy(snapshot)
    return state


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True))
