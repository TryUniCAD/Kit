from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from math import isclose
from pathlib import Path, PureWindowsPath
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PreparePlainPartEvidence import gather
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.api import open_document
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource
from interchange.document.Models.DocumentModel import CadDocument

DEFAULT_SOURCE = (
    ROOT
    / "re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT"
)
DEFAULT_MEASUREMENTS = (
    ROOT / "re/automation/PairedCaptures/P03/solidworks-db1390476325/measurements.json"
)
DEFAULT_WRITTEN_AT = 1795331800


def digest_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def verify_decoded_against_inventory(source_path: Path, measurements_path: Path) -> CadDocument:
    decoded = open_document(source_path, strict=True)
    measurements = loads(measurements_path.read_text(encoding="utf-8"))
    baseline = measurements["observations"]["baseline"]

    if len(decoded.bodies) != baseline["body_count"] or len(decoded.bodies) != 1:
        raise ValueError("decoded body count differs from independent inventory")
    body = decoded.bodies[0]
    if body.topology.volume is None or not isclose(
        body.topology.volume, baseline["volume_mm3"], rel_tol=1e-9, abs_tol=1e-6
    ):
        raise ValueError("decoded body volume differs from independent inventory")
    centroid = body.attributes.get("solidworks.body_centroid_mm")
    if centroid is None or any(
        not isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-6)
        for a, b in zip(centroid, baseline["center_of_mass_mm"], strict=True)
    ):
        raise ValueError("decoded body centroid differs from independent inventory")
    if decoded.configurations[0].name != baseline["configuration"]:
        raise ValueError("decoded configuration differs from independent inventory")
    if not decoded.sketches or not decoded.sketches[0].closed_profile_entity_ids:
        raise ValueError("decoded part lacks a closed sketch profile")
    expected_params = {
        dim["name"]: float(dim["system_value"]) * 1000.0
        for node in baseline["feature_tree"]
        for dim in node.get("dimensions", ())
    }
    decoded_params = {p.name: float(p.value.value) for p in decoded.parameters}
    if set(decoded_params) != set(expected_params):
        raise ValueError("decoded parameter names differ from independent inventory")
    for name, expected_val in expected_params.items():
        if not isclose(decoded_params[name], expected_val, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(f"decoded parameter {name} differs from independent inventory")
    return decoded


def compute_loop_area_and_centroid(doc: CadDocument) -> tuple[float, tuple[float, float]]:
    sketch = doc.sketches[0]
    pts = [
        (float(entity.geometry.start.x), float(entity.geometry.start.y))
        for entity in sketch.entities
    ]
    signed_area_2 = 0.0
    cx_sum = 0.0
    cy_sum = 0.0
    count = len(pts)
    for i in range(count):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % count]
        cross = x0 * y1 - x1 * y0
        signed_area_2 += cross
        cx_sum += (x0 + x1) * cross
        cy_sum += (y0 + y1) * cross
    area = abs(signed_area_2) / 2.0
    if area <= 0.0:
        raise ValueError("decoded sketch loop has non-positive area")
    factor = 1.0 / (3.0 * signed_area_2)
    return area, (cx_sum * factor, cy_sum * factor)


def extract_plain_blind_boss(decoded: CadDocument, name: str, depth_mm: float) -> CadDocument:
    sketch = decoded.sketches[0]
    plane = next(p for p in decoded.support_planes if p.id == sketch.support_plane_id)
    loop_ids = sketch.closed_profile_entity_ids[0]
    by_id = {entity.id: entity for entity in sketch.entities}
    entities = []
    for index, entity_id in enumerate(loop_ids):
        orig = by_id[entity_id]
        if orig.kind != GeometryKind.KLine or not isinstance(orig.geometry, LineGeometry):
            raise ValueError("expected closed straight-line loop")
        start = PlaneVector(float(orig.geometry.start.x), float(orig.geometry.start.y))
        end = PlaneVector(float(orig.geometry.end.x), float(orig.geometry.end.y))
        entities.append(
            SketchEntity(f"edge/{index}", GeometryKind.KLine, LineGeometry(start, end))
        )
    plain_sketch = Sketch(
        "sketch/profile",
        "Sketch1",
        "plane/front",
        tuple(entities),
        closed_profile_entity_ids=(tuple(e.id for e in entities),),
    )
    length_value = ParameterValue(depth_mm, ValueKind.KLength, "mm")
    feature = FeatureStep(
        "feature/boss",
        "Boss-Extrude1",
        FeatureKind.KExtrusion,
        0,
        sketch_id=plain_sketch.id,
        parameter_ids=("parameter/depth",),
        operation=BooleanOp.KCreate,
        definition=ExtrudeFeature(length_value, ExtrudeEnd.KBlind, False, False),
    )
    return CadDocument(
        CadSource("kit-neutral", "<authored-in-memory>", "0" * 64),
        (Configuration("configuration/default", "modeled default", True),),
        (
            Parameter(
                "parameter/depth",
                "D1",
                length_value,
                ParameterRole.KDriving,
                owner_id=feature.id,
            ),
        ),
        (SupportPlane("plane/front", plane.name, Transform()),),
        (plain_sketch,),
        (),
        (feature,),
        (DesignBody("body/boss", feature.name, feature.id),),
        metadata={"name": name},
        units=UnitSystem.KMillimeter,
    )


def prepare_candidate(
    doc: CadDocument,
    locator: str,
    written_at: int,
    role_dir: Path,
    expected_centroid_xy: tuple[float, float],
    expected_depth_mm: float,
) -> dict[str, object]:
    role_dir.mkdir(parents=True, exist_ok=False)
    neutral_path = role_dir / "Neutral.json"
    neutral_path.write_text(doc.to_json(), encoding="utf-8")
    scratch_dir = role_dir / "Candidate"

    class Args:
        neutral = neutral_path
        native_locator = locator
        scratch = scratch_dir

    Args.written_at = written_at
    summary = gather(Args)
    part_name = PureWindowsPath(locator).name
    part_path = scratch_dir / part_name
    candidate_json_path = scratch_dir / "Candidate.json"
    receipt = loads(candidate_json_path.read_text(encoding="utf-8"))

    raw = part_path.read_bytes()
    readback = open_document(raw, strict=True)
    cold_candidate = PrepareNative(
        readback,
        BytesIO(),
        written_at,
        WriteOptions(values={"final_destination": locator}),
    )
    if cold_candidate.BytesValue != raw:
        raise ValueError(f"cold readback round-trip mismatch for {part_name}")

    if len(readback.sketches) != 1:
        raise ValueError(f"expected single sketch in {part_name}")
    sketch = readback.sketches[0]
    if len(sketch.entities) != 4 or any(
        e.kind != GeometryKind.KLine for e in sketch.entities
    ):
        raise ValueError(f"expected 4 line entities in {part_name}")
    if len(sketch.closed_profile_entity_ids) != 1 or len(sketch.closed_profile_entity_ids[0]) != 4:
        raise ValueError(f"expected 4-element closed profile loop in {part_name}")
    plane = next(
        (p for p in readback.support_planes if p.id == sketch.support_plane_id),
        None,
    )
    if plane is None or plane.name != "Front Plane":
        raise ValueError(f"expected Front Plane support in {part_name}")

    body = readback.bodies[0]
    centroid = body.attributes.get("solidworks.body_centroid_mm")
    expected_centroid = (expected_centroid_xy[0], expected_centroid_xy[1], expected_depth_mm / 2.0)
    if centroid is None or any(
        not isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-6)
        for a, b in zip(centroid, expected_centroid, strict=True)
    ):
        raise ValueError(f"readback centroid differs from expected in {part_name}")
    driver = readback.parameters[0]
    return {
        "native_locator": locator,
        "written_at": written_at,
        "part_file": str(part_path),
        "candidate_manifest_file": str(candidate_json_path),
        "neutral_file": str(neutral_path),
        "neutral_sha256": receipt["neutral_sha256"],
        "candidate_sha256": summary["candidate_sha256"],
        "candidate_bytes": receipt["archive_bytes"],
        "manifest_sha256": summary["manifest_sha256"],
        "runtime_input_reads": receipt["runtime_input_reads"],
        "streams": receipt["streams"],
        "kit_readback": {
            "bodies": len(readback.bodies),
            "volume_mm3": body.topology.volume,
            "centroid_mm": [float(c) for c in centroid],
            "driving_parameter": [driver.name, driver.value.value, driver.value.unit],
            "support_plane": plane.name,
            "sketch_lines": len(sketch.entities),
            "closed_profile_lines": len(sketch.closed_profile_entity_ids[0]),
            "cold_read_byte_exact": True,
        },
    }


def build_milestone(
    source_path: Path,
    measurements_path: Path,
    scratch: Path,
    written_at: int,
    baseline_depth_mm: float,
    edited_depth_mm: float,
) -> dict[str, object]:
    scratch = scratch.resolve()
    if scratch.is_relative_to(ROOT / "src"):
        raise ValueError("milestone evidence belongs outside the source tree")
    if scratch.exists():
        raise ValueError("prepare into a fresh scratch directory")
    scratch.mkdir(parents=True, exist_ok=False)

    decoded = verify_decoded_against_inventory(source_path, measurements_path)
    baseline_doc = extract_plain_blind_boss(decoded, "P03RectBoss10mm", baseline_depth_mm)
    edited_doc = extract_plain_blind_boss(decoded, "P03RectBoss15mm", edited_depth_mm)
    area_mm2, centroid_xy = compute_loop_area_and_centroid(baseline_doc)

    baseline_info = prepare_candidate(
        baseline_doc,
        r"C:\KitSdkCandidates\P03RectBoss10mm.SLDPRT",
        written_at,
        scratch / "baseline_10mm",
        centroid_xy,
        baseline_depth_mm,
    )
    edited_info = prepare_candidate(
        edited_doc,
        r"C:\KitSdkCandidates\P03RectBoss15mm.SLDPRT",
        written_at,
        scratch / "edited_15mm",
        centroid_xy,
        edited_depth_mm,
    )

    manifest = {
        "schema": "kit.sw2026.blind-boss-milestone-offline.v1",
        "source": {
            "path": str(source_path.relative_to(ROOT).as_posix()),
            "sha256": digest_file(source_path),
            "measurements_path": str(measurements_path.relative_to(ROOT).as_posix()),
            "measurements_sha256": digest_file(measurements_path),
            "decoded_volume_mm3": decoded.bodies[0].topology.volume,
            "decoded_centroid_mm": list(decoded.bodies[0].attributes["solidworks.body_centroid_mm"]),
        },
        "candidates": {
            "baseline_10mm": baseline_info,
            "edited_15mm": edited_info,
        },
        "expected_delta": {
            "depth_mm_before": baseline_depth_mm,
            "depth_mm_after": edited_depth_mm,
            "expected_volume_mm3_before": area_mm2 * baseline_depth_mm,
            "expected_volume_mm3_after": area_mm2 * edited_depth_mm,
            "expected_volume_delta_mm3": area_mm2 * (edited_depth_mm - baseline_depth_mm),
            "expected_centroid_mm_before": [centroid_xy[0], centroid_xy[1], baseline_depth_mm / 2.0],
            "expected_centroid_mm_after": [centroid_xy[0], centroid_xy[1], edited_depth_mm / 2.0],
        },
        "worker_checks_pending": [
            "Measure healthy bracketing controls before and after candidate checks",
            "Open P03RectBoss10mm.SLDPRT in fresh SOLIDWORKS process, rebuild, verify tree/D1/body/volume/CoM",
            "Open P03RectBoss15mm.SLDPRT in fresh SOLIDWORKS process, rebuild, compare against 15mm control",
            "Edit D1 inside SOLIDWORKS, rebuild, measure, restore depth, save, reopen, and measure again",
            "Publish both candidates through SDK/CLI with the resulting live measurement receipt",
        ],
    }
    manifest_bytes = (dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    manifest_path = scratch / "MilestoneManifest.json"
    manifest_path.write_bytes(manifest_bytes)
    return {
        "milestone_manifest_path": str(manifest_path),
        "milestone_manifest_sha256": digest_bytes(manifest_bytes),
        "baseline_candidate_sha256": baseline_info["candidate_sha256"],
        "edited_candidate_sha256": edited_info["candidate_sha256"],
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Prepare offline Milestone 1 blind-boss candidates and SHA-256 manifest")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--measurements", type=Path, default=DEFAULT_MEASUREMENTS)
    parser.add_argument("--written-at", type=int, default=DEFAULT_WRITTEN_AT)
    parser.add_argument("--baseline-depth-mm", type=float, default=10.0)
    parser.add_argument("--edited-depth-mm", type=float, default=15.0)
    parser.add_argument("--scratch", required=True, type=Path)
    args = parser.parse_args()
    result = build_milestone(
        args.source,
        args.measurements,
        args.scratch,
        args.written_at,
        args.baseline_depth_mm,
        args.edited_depth_mm,
    )
    print(dumps(result, sort_keys=True))
