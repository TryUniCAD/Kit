from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from gzip import decompress
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from platform import machine
from tempfile import TemporaryDirectory
import sys
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))

from ProveMeasuredPrincipalRevolve import WriterAudit, denied, digest, neutral, written
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.BuildRevBodyGeom import BuildRevBody
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument

FIXTURE = ROOT / "re/solidworks/v2026/corpus/revolve/MeasuredPrincipal01"
FORMAT = "solidworks.sldprt"


def reject_sparse_slots(candidate):
    link = ReadNativeLink(SldprtArchive.from_bytes(candidate), 0)
    owner, = ReadRevOwners(link)
    fields = owner.SketchValue.FieldsValue
    points = list(fields["points"])
    # Exchange a contour slot with an axis endpoint, repairing every line reference.
    # No owner, relation, or coordinate changes; the contour indices are now sparse.
    contour_index = owner.ProfileGraph.LoopValue.PointsValue[-1].IndexValue
    axis_index = owner.ProfileGraph.AxisValue.EndValue
    points[axis_index], points[contour_index] = points[contour_index], points[axis_index]
    fields["points"] = points
    swap = {contour_index: axis_index, axis_index: contour_index}
    for row in fields["lines"]:
        for endpoint in ("fc8_s", "fcc_s"):
            index = row["line"][endpoint]
            row["line"][endpoint] = swap.get(index, index)
    try:
        ReadRevOwners(link)
    except ValueError as error:
        assert str(error) == "cache-free revolve does not support sparse contour or axis slots"
    else:
        raise AssertionError("sparse contour slots were accepted")


def verify(case, scratch):
    request = loads((FIXTURE / (case + ".json")).read_bytes())
    job = (FIXTURE / "InspectJob.json").read_bytes()
    source = next(row for row in loads(job)["cases"] if row["model"]["plane"].casefold() == case.casefold())
    report = decompress((FIXTURE / "Inspection.json.gz").read_bytes()).decode("utf-8")
    summary = (ROOT / "re/solidworks/measurements/2026/SdkPrincipalRevolveMacNative01.json").read_bytes().decode("utf-8")
    evidence = {"summary": summary, "native_result": report, "inspection_job": job.decode("utf-8")}
    document = neutral(request)
    values = {"final_destination": source["source"],
              "solidworks_native_measurement": {"written_at": request["epoch"], "receipt": evidence}}
    opts = WriteOptions(values=values)
    direct = SldprtWriter()
    front = (FIXTURE / "FrontFull.SLDPRT").read_bytes()
    assert digest(front) == "0a4b996b35316aa12c43222113e6d033d3a9e5fc617109056315120a907287c5"
    import_module("interchange.brep.Validation.BrepValidate")
    import_module("interchange.document.Models.DocumentProvenance")
    lookup("utf-16-le")
    audit = WriterAudit(scratch)
    candidate = audit.run(lambda: PrepareRevolve(document, BytesIO(), request["epoch"], opts).BytesValue)
    exact = digest(candidate) == source["sha256"]
    if (sys.platform, machine(), sys.version_info[:3], ZLIB_RUNTIME_VERSION) == ("darwin", "arm64", (3, 14, 7), "1.2.12"):
        assert exact, "the measured classic runtime produced a different complete archive"
    link = ReadNativeLink(SldprtArchive.from_bytes(candidate), 0)
    owner, = ReadRevOwners(link)
    profile = owner.ProfileGraph
    loop = profile.LoopValue
    order = (2, 0, 3, 1)
    indices = {old: new for new, old in enumerate(order)}
    points = tuple(replace(loop.PointsValue[old], IndexValue=new) for new, old in enumerate(order))
    lines = tuple(replace(line, StartValue=indices[line.StartValue], EndValue=indices[line.EndValue])
                  for line in loop.LinesValue)
    moved = replace(owner, ProfileGraph=replace(profile, LoopValue=replace(loop, PointsValue=points, LinesValue=lines)))
    assert audit.run(lambda: BuildRevBody(owner, "body")) == audit.run(lambda: BuildRevBody(moved, "body"))
    reject_sparse_slots(candidate)
    legacy = audit.run(lambda: open_document(front, source_format=FORMAT, strict=True, include_brep=False))
    assert legacy.brep is None and len(legacy.sketches) == 1 and len(legacy.feature_timeline) == 19
    history = audit.run(lambda: open_document(candidate, source_format=FORMAT, strict=True, include_brep=False))
    full = audit.run(lambda: open_document(candidate, source_format=FORMAT, strict=True))
    assert full.brep is not None and history.brep is None and full.feature_timeline == history.feature_timeline
    published = 0
    for model in (document, CadDocument.from_json(history.to_json())):
        for route in ("direct", "registry"):
            sink = BytesIO()
            def send():
                if route == "direct":
                    return direct.write(model, sink, opts)
                return write_document(model, sink, destination_format=FORMAT, allow_carrier=False, values=values)
            if exact:
                written(lambda: audit.run(send), candidate, sink)
                published += 1
            else:
                denied(lambda: audit.run(send), "no matching native measurement")
                assert sink.getvalue() == b""
    return {"case": case, "exact_native_hash": exact, "publications": published,
            "permuted_contour_equal": True, "legacy_design_only": True, "audit": audit.report()}


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--case", choices=("Top", "Right"), required=True)
    args = cli.parse_args()
    with TemporaryDirectory(prefix="KitPrincipalQueue-") as area:
        print(dumps(verify(args.case, Path(area).resolve()), sort_keys=True))
