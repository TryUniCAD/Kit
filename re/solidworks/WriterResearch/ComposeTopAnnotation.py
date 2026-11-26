from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from struct import pack
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from ConfigScene.Annotation import KAnnotation, KFirstViewId
from EncoderRoundTrip.Artifacts import canonical_json, digest, read_record, write_artifact
from EncoderRoundTrip.Source import encode_writer_input
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import PartCandidate
from convert.adapters.solidworks.Archive.Construction.Views.MakeViewNode import MakeViewNode
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


REQUEST_SCHEMA = "kit.sw2026.top-annotation-candidate.v1"
VIEW_FIELDS = {"configuration_id", "role", "projection", "frame_direction", "origin_unit", "transform"}
ANNOTATION_CLASS = RuntimeClass(KAnnotation, 1)
ANNOTATION_BASE_ID = KFirstViewId - 1


def components(vector: SpaceVector) -> tuple[float, float, float]:
    if type(vector) is not SpaceVector:
        raise ValueError("Top annotation Transform requires typed spatial vectors")
    values = (vector.x, vector.y, vector.z)
    if any(type(value) not in (int, float) for value in values):
        raise ValueError("Top annotation Transform requires numeric vector components")
    return values


@dataclass(frozen=True, slots=True)
class TopAnnotationIntent:
    configuration_id: str
    transform: Transform

    def __post_init__(self) -> None:
        if type(self.configuration_id) is not str or not self.configuration_id:
            raise ValueError("Top annotation requires a configuration ID")
        if type(self.transform) is not Transform:
            raise ValueError("Top annotation requires an existing typed Transform")
        vectors = tuple(
            components(value)
            for value in (self.transform.origin, self.transform.x_axis, self.transform.y_axis, self.transform.z_axis)
        )
        if vectors != ((0, 0, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0)):
            raise ValueError("Top annotation requires zero translation and the exact Top cardinal frame")


def read_request(payload: bytes) -> tuple[CadDocument, TopAnnotationIntent]:
    request = read_record(payload)
    if set(request) != {"schema", "document", "annotation_view"} or request["schema"] != REQUEST_SCHEMA:
        raise ValueError("expected a version-1 Top annotation candidate request")
    view = request["annotation_view"]
    if type(view) is not dict or set(view) != VIEW_FIELDS:
        raise ValueError("expected exact configuration-owned annotation view fields")
    if (view["role"], view["projection"], view["frame_direction"], view["origin_unit"]) != (
        "top", "orthographic", "view_to_model", "mm"
    ):
        raise ValueError("expected a Top orthographic view-to-model frame with millimetre origin")
    transform = FromData(view["transform"])
    intent = TopAnnotationIntent(view["configuration_id"], transform)
    if canonical_json(ToData(transform)) != canonical_json(view["transform"]):
        raise ValueError("Top annotation Transform must use its complete typed JSON representation")
    document = CadDocument.from_dict(request["document"])
    if encode_writer_input(document) != canonical_json(request["document"]):
        raise ValueError("Top annotation document changed during typed reconstruction")
    return document, intent


def annotation_matrix(intent: TopAnnotationIntent) -> dict[str, float]:
    frame = intent.transform
    rows = (
        *(abs(float(value)) for value in components(frame.x_axis)),
        *(abs(float(value)) for value in components(frame.y_axis)),
        *(-abs(float(value)) for value in components(frame.z_axis)),
    )
    return {f"m{index}": value for index, value in enumerate(rows)}


def add_top_annotation(root: ArchiveNode, intent: TopAnnotationIntent) -> None:
    fields = root.FieldsValue
    owner = fields["fa48"]
    if (
        not isinstance(owner, ArchiveNode)
        or owner.ClassValue != RuntimeClass("suObList", 1)
        or owner.FieldsValue != {"n": 0, "items": ()}
        or fields["feb0"] != ANNOTATION_BASE_ID
    ):
        raise ValueError("Top annotation requires the empty generated part annotation owner")
    view_id = fields["feb0"] + 1
    base = MakeViewNode("*Top", view_id, (1.0, 0.0, 0.0, 0.0)).FieldsValue
    base["f368"].update({"has_matrix": 1, "f08": annotation_matrix(intent)})
    view = ArchiveNode(ANNOTATION_CLASS, {
        **base,
        "f3d8": 0, "f3d0": None, "f3e8#0": None, "f3f0": 0,
        "f3e0": 0.0, "f3e8": None, "f3f4": 0, "f3f8": 1, "f2f0": None,
        "f3fc": -1, "f408": 0, "f400": -1, "f404": -1,
    })
    owner.FieldsValue.update({"n": 1, "items": ({"o": view},)})
    fields["feb0"] = view_id


def construct(document: CadDocument, intent: TopAnnotationIntent, locator: str, epoch: int) -> PartCandidate:
    if type(intent) is not TopAnnotationIntent:
        raise TypeError("Top annotation composition requires typed view intent")
    plan = PlanPartWrite(document)
    configuration, = document.configurations
    if not configuration.active or configuration.id != intent.configuration_id:
        raise ValueError("Top annotation must bind the active neutral configuration")
    output = RequirePartPath(locator, epoch)
    recipe = MakePartRecipe(plan, epoch)
    inputs = BindPartIntent(document, plan, recipe, output)
    CheckPartInput(document, inputs, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(inputs, plan, allocator)
    add_top_annotation(system.RootValue, intent)
    profile = MakePartProfMut(system, inputs, plan, allocator)
    return FinishBlindMut(system, profile, inputs, plan, allocator)


def inspect_candidate(candidate: PartCandidate, intent: TopAnnotationIntent) -> dict[str, object]:
    archive = SldprtArchive.from_bytes(candidate.BytesValue, "<generated Top annotation part>")
    config = ReadPartConfig(archive)
    resolved = ReadResolvedMut(
        archive.Require(KResolvedFeaturesStream), config.VersionValue,
        config.MapValue, candidate.ResolvedValue.ContextValue,
    )
    root = config.RootValue.FieldsValue
    owner = root["fa48"]
    item, = owner.FieldsValue["items"]
    view = item["o"]
    matrix = view.FieldsValue["f368"]["f08"]
    actual_matrix = tuple(matrix[f"m{index}"] for index in range(9))
    expected_matrix = tuple(annotation_matrix(intent).values())
    if (
        owner.FieldsValue["n"] != 1
        or view.ClassValue != ANNOTATION_CLASS
        or view.FieldsValue["f358"] != "*Top"
        or (root["feb0"], view.FieldsValue["f360"]) != (ANNOTATION_BASE_ID + 1,) * 2
        or root["feb4"] != ANNOTATION_BASE_ID
        or pack("<9d", *actual_matrix) != pack("<9d", *expected_matrix)
        or config.MapValue.CounterValue != candidate.ConfigValue.MapValue.CounterValue
        or resolved.MapBase != candidate.ConfigValue.MapValue.CounterValue
        or resolved.MapValue.CounterValue != candidate.ResolvedValue.MapValue.CounterValue
        or len(resolved.RootsValue) != len(candidate.ResolvedValue.RootsValue)
    ):
        raise ValueError("generated annotation graph or linked resolved map differs on readback")
    return {
        "role": "top",
        "configuration_id": intent.configuration_id,
        "matrix_binary64": [value.hex() for value in actual_matrix],
        "annotation_id": view.FieldsValue["f360"],
        "display_high_water": root["feb0"],
        "independent_view_seed": root["feb4"],
        "config_next_slot": config.MapValue.CounterValue,
        "resolved_base": resolved.MapBase,
        "resolved_next_slot": resolved.MapValue.CounterValue,
        "resolved_roots": len(resolved.RootsValue),
    }


def gather(args) -> dict[str, object]:
    scratch = args.scratch.resolve()
    if scratch.is_relative_to(ROOT / "src") or scratch.exists():
        raise ValueError("generated evidence requires a fresh output directory outside src")
    request = args.request.read_bytes()
    document, intent = read_request(request)
    candidate = construct(document, intent, args.native_locator, args.written_at)
    structure = inspect_candidate(candidate, intent)
    scratch.mkdir(parents=True, exist_ok=False)
    archive = write_artifact(scratch, PureWindowsPath(args.native_locator).name, candidate.BytesValue)
    evidence = {
        "schema": "kit.sw2026.top-annotation-measurement-input.v1",
        "stage": "awaiting_native_measurement",
        "request_sha256": digest(request),
        "archive": archive,
        "native_locator": args.native_locator,
        "written_at": args.written_at,
        "typed_readback": structure,
        "streams": {name: [len(data), digest(data)] for name, data in candidate.StreamsValue.items()},
    }
    manifest = write_artifact(scratch, "Candidate.json", canonical_json(evidence))
    return {"archive": archive, "manifest": manifest}


if __name__ == "__main__":
    parser = ArgumentParser(description="Construct a research SOLIDWORKS part with one Top annotation view")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--native-locator", required=True)
    parser.add_argument("--written-at", type=int, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    sys.stdout.buffer.write(canonical_json(gather(parser.parse_args())))
