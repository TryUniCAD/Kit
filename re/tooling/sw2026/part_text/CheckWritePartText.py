from functools import partial
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PartTextProbe import (
    PROPERTY_DIAGNOSTIC, PROPERTY_STATUS, check_model, model_state, read_part, refuse_output, refuse_write,
)
from convert import convert, open_document, write_document
from convert.adapters.base.ReadOptions import ReadOptions
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

CAUSE = "part properties require an empty compatible native manager"


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
        mode: refuse_output(call, "native-only feature definitions cannot be exported", "sldprt:feature:1", "Annotations")
        for mode, call in operations.items()
    }


def check_neutral_copy(document, legacy):
    source = document.to_json().encode("utf-8")
    first, second = BytesIO(), BytesIO()
    convert(source, first, source_format="interchange.json", destination_format="interchange.json",
            allow_carrier=False)
    legacy.ConvertData(source, second, SourceFormat="interchange.json", DestFormat="interchange.json")
    result = {}
    for mode, stream in (("ordinary", first), ("compatibility", second)):
        restored = open_document(stream.getvalue(), source_format="interchange.json", strict=True)
        if restored != document:
            raise ValueError("neutral JSON copy changed the full authored inspection document")
        result[mode] = model_state(restored)["status"]
    if first.getvalue() != second.getvalue():
        raise ValueError("ordinary and compatibility snapshots differ")
    return result


def check_filtered_copy(document):
    source = document.to_json().encode()
    options = {"source_format": "interchange.json", "destination_format": "interchange.json"}
    restrictions = {"geometry": {"include_brep": False}, "mesh": {"include_tessellation": False},
                    "configuration": {"configuration": document.configurations[0].name}}
    return {name: refuse_write(partial(convert, source, **options, **selected), CAUSE)
            for name, selected in restrictions.items()}


def inspect(source):
    raw = source.read_bytes()
    document = read_part(source)
    relaxed = read_part(source, strict=False)
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
        "strict": partial(convert, source, **options),
        "nonstrict": partial(convert, source, strict=False, **options),
        "public_write": partial(
            write_document, relaxed, destination_format="interchange.json",
            validate=False, allow_carrier=True,
        ),
        "registry": partial(registry.write, relaxed, format_id="interchange.json"),
        "compatibility": partial(
            legacy.ConvertData, source, SourceFormat="solidworks.sldprt",
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
    state["refusals"] = refusals
    state["implicit_path_unchanged"] = True
    state["native_copy_refusals"] = native_copy_refusals(document, legacy)
    snapshot = authored_snapshot()
    state["neutral_snapshot"] = model_state(snapshot)
    state["neutral_copies"] = check_neutral_copy(snapshot, legacy)
    state["filtered_copies_refused"] = check_filtered_copy(snapshot)
    return state


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True))
