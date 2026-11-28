import argparse
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import re
import sys

from GenerateBodySceneContrast import build, install_scope, require


def digest(data):
    return sha256(data).hexdigest()


def block_archive_read(event, args):
    if event != "open" or args[2] & (os.O_WRONLY | os.O_RDWR):
        return
    path = os.fsdecode(args[0]) if isinstance(args[0], (str, bytes)) else ""
    if path.lower().endswith((".archive", ".f3d", ".f3z")):
        raise RuntimeError("A JSON-only height edit attempted to read a native archive")


def source_request(original, model):
    from AppearanceGraph import projection

    # Only the generated scene grammar may be explicitly removed for request
    # extraction. The full source, including Graphics, is verified after regeneration.
    return projection(replace(model, Graphics=None), original)


def height_edit(original, edited, request):
    from interchange.Features.FeatureDistExt import DistanceExtrude

    cuboid = request["material_request"]["configuration_request"]["camera_request"][
        "cuboid"
    ]
    params = cuboid["parameters"]
    _, feature = original.feature_timeline
    require(
        isinstance(feature.definition, DistanceExtrude),
        "Expected one distance-driven extrusion",
    )
    (model,) = (
        p for p in original.parameters if p.id == feature.definition.AlongParameterId
    )
    require(
        model.name == params["height"]["user_name"] and model.expression is not None,
        "Extrusion disagrees with the height model role",
    )
    (driver_id,) = model.expression.parameter_ids
    (driver,) = (p for p in original.parameters if p.id == driver_id)
    require(
        driver.name == params["height_driver"]["user_name"]
        and driver.expression is not None
        and not driver.expression.parameter_ids
        and driver.value.unit == "mm",
        "Expected one independent millimetre height driver",
    )
    (changed,) = (p for p in edited.parameters if p.id == driver_id)
    require(
        changed.expression is not None and isinstance(changed.expression.source, str),
        "Height edit requires an explicit expression",
    )
    literal = changed.expression.source
    require(
        re.fullmatch(r"[0-9]+(?:\.[0-9]+)? mm", literal) is not None,
        "Height edit requires a positive decimal millimetre literal",
    )
    value = float(literal.removesuffix(" mm"))
    require(
        isfinite(value) and value > 0 and value != driver.value.value,
        "Expected a distinct positive height",
    )
    proposed = replace(
        driver,
        value=replace(driver.value, value=value),
        expression=replace(driver.expression, source=literal),
    )
    expected = replace(
        original,
        parameters=tuple(
            proposed if p.id == driver_id else p for p in original.parameters
        ),
    )
    require(
        edited == expected, "Edited JSON changes other source semantics or typed state"
    )
    copied = deepcopy(request)
    changed_cuboid = copied["material_request"]["configuration_request"][
        "camera_request"
    ]["cuboid"]
    changes = changed_cuboid["parameters"]
    changes["height_driver"].update(expression=literal, value=value * 0.1)
    changes["height"]["value"] = value * 0.1
    return copied, driver.name, value


def generate(edited_raw, producer, epoch):
    from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
    from convert.adapters.Fusion.Native.Projection.ProjectVendor import ProjectVendor
    from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
    from interchange import CadDocument

    edited = CadDocument.from_json(edited_raw.decode("utf-8"))
    require(
        set(edited.metadata) == {"fusion.native_state", "fusion.read_only"}
        and edited.metadata["fusion.read_only"] is True,
        "Expected the strict saved cuboid typed JSON contract",
    )
    native = edited.metadata["fusion.native_state"]
    model = CheckContract(native, "model", Version=2)
    require(
        isinstance(model, DocumentModel) and model.Graphics is not None,
        "Expected a complete typed source scene",
    )
    original = ProjectVendor(model, edited.source)
    require(
        original.metadata == edited.metadata,
        "Typed source is not the strict public projection",
    )
    request = source_request(original, model)
    requested, driver, height_mm = height_edit(original, edited, request)
    _, original_payload, original_neutral, verification = build(
        request, epoch, producer
    )
    regenerated = CadDocument.from_json(original_neutral.decode("utf-8"))
    require(
        digest(original_payload) == original.source.sha256
        and replace(regenerated, source=original.source) == original,
        "Original saved model contains fields outside the complete generated source scope",
    )
    _, candidate, neutral, edited_report = build(requested, epoch, producer)
    require(
        edited_report["candidate_sha256"] != verification["candidate_sha256"],
        "Regenerated candidate did not change after editing the height",
    )
    return (
        candidate,
        neutral,
        requested,
        {
            "native_acceptance": "unmeasured",
            "public_write_admission": False,
            "scope": "strict SDK JSON height edit of a fully reproducible authored graphics cuboid",
            "source_archive_sha256": original.source.sha256,
            "edited_input_json_sha256": digest(edited_raw),
            "candidate_sha256": digest(candidate),
            "validated_height_driver": driver,
            "height_mm": height_mm,
            "unchanged_source_fully_regenerated": True,
            "strict_edited_readback": True,
        },
    )


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate a scoped cuboid height edit from strict saved SDK JSON"
    )
    parser.add_argument("checkout", type=Path)
    parser.add_argument("edited_json", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--written-at", required=True, type=int)
    args = parser.parse_args()
    try:
        require(
            not args.output.exists() and not args.output.is_symlink(),
            "Output directory must be new",
        )
        producer = install_scope(args.checkout.resolve())
        sys.addaudithook(block_archive_read)
        archive, neutral, request, report = generate(
            args.edited_json.read_bytes(), producer, args.written_at
        )
    except (OSError, ValueError, RuntimeError, TypeError, KeyError) as error:
        parser.exit(1, f"Saved cuboid height edit refused: {error}\n")
    args.output.mkdir()
    (args.output / "Candidate.archive").write_bytes(archive)
    (args.output / "Document.json").write_bytes(neutral)
    (args.output / "Request.json").write_text(
        json.dumps(request, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (args.output / "Generation.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
