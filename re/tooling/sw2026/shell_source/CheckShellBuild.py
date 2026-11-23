from dataclasses import replace
from io import BytesIO
from pathlib import PureWindowsPath

from convert import write_document
from convert.adapters.solidworks.Core.Preparation.Shells.BuildShellPart import BuildShellPart
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.geometry.Models.Selection import SelectPathElem


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def reject(action, reason):
    try:
        action()
    except (ValueError, RuntimeError) as error:
        require(reason in str(error), f"unexpected shell refusal: {error}")
    else:
        raise ValueError("unqualified shell source reached the candidate")


def compile_refusals(source, settings, epoch):
    stock, shell = source.feature_timeline[-2:]
    cap, = source.selections
    body, = source.bodies
    depth, wall = source.parameters
    wrong_owner = replace(stock, input_feature_ids=(source.feature_timeline[0].id,))
    bottom = replace(cap, path=(SelectPathElem("feature", stock.id, "face:0"),))
    different_wall = replace(wall, value=replace(wall.value, value=wall.value.value + 0.5))
    changed = replace(shell, definition=replace(shell.definition, thickness=different_wall.value))
    locator = PureWindowsPath(settings.values["final_destination"])
    candidates = (
        ("foreign_sketch", replace(source, feature_timeline=(*source.feature_timeline[:-2], wrong_owner, shell)),
         settings, epoch, "linked stock history"),
        ("wrong_cap", replace(source, selections=(bottom,)), settings, epoch, "actual upper stock cap"),
        ("changed_wall", replace(source, parameters=(depth, different_wall),
                                 feature_timeline=(*source.feature_timeline[:-1], changed)),
         settings, epoch, "metre value disagrees"),
        ("changed_body_name", replace(source, bodies=(replace(body, name="Edited body label"),)),
         settings, epoch, "cold readback differs"),
        ("foreign_metadata", replace(source, metadata={**source.metadata, "unmodeled": True}),
         settings, epoch, "cold readback differs"),
        ("stale_event", source, settings, epoch + 1, "cold readback differs"),
        ("changed_locator", source, replace(settings, values={
            **settings.values, "final_destination": str(locator.with_name("OtherShell.SLDPRT"))
        }), epoch, "cold readback differs"),
    )
    for name, document, options, event, reason in candidates:
        reject(lambda: BuildShellPart(document, BytesIO(), event, options), reason)
    return [row[0] for row in candidates]


def public_refusals(source, settings):
    sentinel = b"caller owned shell sink"
    sink = BytesIO(sentinel)
    read_geometry = source.brep is not None
    refuse_history = "native-only feature definitions"
    reject(lambda: write_document(source, sink, destination_format="solidworks.sldprt",
                                  allow_carrier=False, values=settings.values),
           "does not support the destination" if read_geometry else refuse_history)
    reject(lambda: SldprtWriter().write(source, sink, settings),
           "requires an offline native measurement receipt" if read_geometry else refuse_history)
    require(sink.getvalue() == sentinel and sink.tell() == 0, "unqualified shell modified the sink")
    return 2


def check_shell_build(documents, candidate, settings, epoch):
    fields = ("units", "configurations", "parameters", "support_planes", "sketches",
              "feature_timeline", "selections", "bodies")
    full, design = documents
    require(full.brep is not None and design.brep is None
            and all(getattr(full, key) == getattr(design, key) for key in fields),
            "source modes do not reach the same typed shell and body owners")
    compilations, unpublished, refusals = 0, 0, {}
    for mode, source in zip(("full", "design_only"), documents, strict=True):
        unchanged = source.to_json()
        portable = type(source).from_json(unchanged)
        require(portable.to_json() == unchanged, "inspection JSON changed the whole strict source")
        for value in (source, portable):
            artifact = BuildShellPart(value, BytesIO(), epoch, settings)
            require(artifact.BytesValue == candidate.BytesValue
                    and artifact.StreamsValue == candidate.StreamsValue,
                    "regeneration changed complete archives or logical streams")
            compilations += 1
        refusals[mode] = compile_refusals(source, settings, epoch)
        unpublished += public_refusals(source, settings)
        require(source.to_json() == unchanged, "shell preparation mutated the original source")
    return {"compilations": compilations, "logical_stream_comparisons": compilations * len(candidate.StreamsValue),
            "compiler_refusals": refusals, "public_write_refusals": unpublished}
