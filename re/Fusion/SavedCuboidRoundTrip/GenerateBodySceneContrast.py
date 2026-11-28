import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import sys

DEPENDENCY = "bb22f5b434fbb056a7bd0960d5286eefe8c88568"


def digest(value):
    return sha256(value).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def install_scope(checkout):
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=checkout, text=True
    ).strip()
    require(head == DEPENDENCY, "writer dependency revision changed")
    status = subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=normal",
            "--",
            "src",
            "re/Fusion",
        ],
        cwd=checkout,
    )
    require(not status, "writer dependency code has local changes")
    research = checkout / "re/Fusion"
    sys.path[:0] = [
        str(checkout / "src"),
        str(research / "DistinctMaterialAppearances"),
        str(research / "SavedCuboidGeneration"),
    ]
    return research / "DistinctMaterialAppearances/GenerateSavedCuboid.py"


def block_native_open(event, args):
    if event != "open":
        return
    path = args[0]
    if isinstance(path, bytes):
        path = path.decode(errors="replace")
    if isinstance(path, str) and path.lower().endswith((".f3d", ".f3z")):
        raise RuntimeError("A source-free emitter attempted a native archive file open")


def build(request, epoch, producer):
    from AppearanceGraph import projection, project_appearances
    from BuildLeafPlan import leaf_plan
    from ProbeSceneWire import structural_world
    from convert import open_document
    from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
    from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
    from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
    from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
    from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismGraph import (
        ReadPrismGraph,
    )
    from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismRoles import (
        ReadPrismRoles,
    )
    from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismWire import (
        ReadPrismWire,
    )
    from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
    from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
    from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    from convert.Formats.Fusion.GraphicsCodec.EmitGraphics import EmitGraphics
    from convert.Formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
    from convert.Formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
    from convert.Formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics
    from convert.Formats.Fusion.GraphicsCodec.Validation.SceneTargets import (
        SceneTargets,
    )
    from interchange import CadDocument

    def history_order(data, name):
        (part,) = (part for part in ReadContainer(data).Parts if part.Name == name)
        wire = ReadPrismWire(part.Payload)
        roles = ReadPrismRoles(ReadPrismGraph(wire.Table))
        return {
            "edges": [roles.Edges[slot] for slot in sorted(roles.Edges)],
            "faces": [roles.Faces[slot] for slot in sorted(roles.Faces)],
        }

    sys.addaudithook(block_native_open)
    base, generation = runpy.run_path(str(producer))["build"](request, written_at=epoch)
    public = open_document(base, source_format="f3d", strict=True)
    neutral = public.to_json().encode()
    model = CheckContract(
        CadDocument.from_json(neutral.decode()).metadata["fusion.native_state"],
        "model",
        Version=2,
    )
    require(
        ReadDocument(base) == model,
        "Generated JSON does not retain the complete typed document",
    )
    require(
        model.Graphics is None and len(model.Bodies) == 1,
        "Unexpected graphics or body inventory",
    )
    (body,) = model.Bodies
    require(isinstance(body.History, PrismHistory), "Expected one typed prism")
    graph = BuildGraph(model)
    extrusion = SelectExtrusion(graph)
    owner = extrusion.BodyNode
    target = EntityRef(owner.SegmentId, owner.ObjectId)
    require(
        graph.Resolve(extrusion.DcBody.Fields["rBody"]) == owner
        and owner.Fields["actIdentifier"] == f"{target.SegmentId}_{target.ObjectId}",
        "The driven extrusion and graphics have different live owners",
    )
    style = project_appearances(model)
    require(
        style[-2].InstanceId != style[-1].InstanceId,
        "Physical and visual style owners alias",
    )
    plan = leaf_plan(body.History.Model)
    expected_order = {
        group: [row["role"] for row in plan[group]] for group in ("edges", "faces")
    }
    require(
        history_order(base, body.PartName) == expected_order,
        "History slots and generated leaf roles differ",
    )
    group = ObjectRef("GroupNode", f"{1:016X}")
    scene = structural_world(plan, target, group)
    wire = EmitGraphics(scene)
    require(
        ReadGraphics(wire.WorldData, wire.MeshStreams, wire.FusionStreams) == scene,
        "Generated scene failed typed wire readback",
    )
    require(
        SceneTargets(scene, graph.OneClass("ACTTable", 1).SegmentId) == (target,),
        "Scene target is not the live body",
    )
    rebuilt = replace(model, Graphics=scene)
    candidate = EmitParsed(rebuilt)
    require(
        ReadDocument(candidate) == rebuilt,
        "The new scene changed unrelated typed fields",
    )
    require(
        history_order(candidate, body.PartName) == expected_order,
        "Emitting the scene changed physical history roles",
    )
    graphic_document = open_document(candidate, source_format="f3d", strict=True)
    require(
        graphic_document.metadata.get("fusion.read_only") is True,
        "Research scene bypassed the public write guard",
    )
    restored = CadDocument.from_json(graphic_document.to_json())
    graphic_model = CheckContract(
        restored.metadata["fusion.native_state"], "model", Version=2
    )
    require(
        graphic_model == rebuilt and restored == graphic_document,
        "Strict persisted readback lost the generated scene",
    )
    require(
        replace(graphic_model, Graphics=None) == model,
        "A scoped scene repair changed other document fields",
    )
    require(
        projection(model, public) == request,
        "Underlying generated document differs from the authored request",
    )
    require(
        set(restored.metadata)
        == set(public.metadata)
        == {"fusion.native_state", "fusion.read_only"}
        and replace(restored, metadata=public.metadata, source=public.source) == public,
        "The generated scene changes the public authored graph",
    )
    return (
        base,
        candidate,
        restored.to_json().encode(),
        {
            "baseline_sha256": digest(base),
            "candidate_sha256": digest(candidate),
            "source_free_strict_json_sha256": digest(neutral),
            "graphics_world_sha256": digest(wire.WorldData),
            "body_owner": [target.SegmentId, target.ObjectId],
            "body_appearance": style[-1].InstanceId,
            "physical_aspect_appearance": style[-2].InstanceId,
            "history_order": expected_order,
            "body_edge_leaves": len(plan["edges"]),
            "body_face_leaves": len(plan["faces"]),
            "material_and_scene_exact_strict_readback": True,
            "rich_appearance_projection_supported_with_scene": False,
            "native_acceptance": "unmeasured",
            "research_scene_scope": "uniform style on one generated body, structural zero-LOD contrast",
            "open_scope": generation["open_saved_scope"],
        },
    )


def main():
    parse = argparse.ArgumentParser(
        description="Prepare an exact source-free body scene research contrast"
    )
    parse.add_argument("checkout", type=Path)
    parse.add_argument("request", type=Path)
    parse.add_argument("output", type=Path)
    parse.add_argument("--written-at", type=int, required=True)
    args = parse.parse_args()
    producer = install_scope(args.checkout.resolve())
    raw = args.request.read_bytes()
    args.output.mkdir()
    try:
        base, scene, neutral, report = build(json.loads(raw), args.written_at, producer)
    except Exception:
        import traceback

        (args.output / "Failure.txt").write_text(
            traceback.format_exc(), encoding="utf-8"
        )
        raise
    # Publicly visible path types are published by the caller after all readbacks.
    for filename, contents in (
        ("Control.archive", base),
        ("Candidate.archive", scene),
        ("Document.json", neutral),
        (
            "Generation.json",
            (
                json.dumps(
                    {
                        **report,
                        "request_sha256": digest(raw),
                        "written_at": args.written_at,
                    },
                    indent=2,
                )
                + "\n"
            ).encode(),
        ),
    ):
        with (args.output / filename).open("xb") as file:
            file.write(contents)


if __name__ == "__main__":
    main()
