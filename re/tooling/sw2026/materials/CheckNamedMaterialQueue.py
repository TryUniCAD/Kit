from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from convert import open_document, write_document
from convert.adapters.json.Adapter import JsonAdapter
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc


def checked_source(path, digest):
    data = (ROOT / "re/solidworks/v2026/corpus" / path).read_bytes()
    if sha256(data).hexdigest() != digest:
        raise ValueError(f"disclosed source changed: {path}")
    return data


def refuse_writes(document):
    for route in ("registry", "direct"):
        sink = BytesIO(b"original")
        try:
            if route == "direct":
                SldprtWriter().write(document, sink)
            else:
                write_document(document, sink, destination_format="solidworks.sldprt")
        except ValueError as error:
            if str(error) != "unresolved material assignments cannot be exported":
                raise
        else:
            raise ValueError(f"{route} accepted unresolved material")
        if sink.tell() != 0 or sink.getvalue() != b"original":
            raise ValueError(f"{route} touched the destination")
    return 2


def preserve_json(document):
    neutral = MakePlainDoc("MaterialInspection", ((0.0, 0.0), (20.0, 0.0), (20.0, 10.0), (0.0, 10.0)), 5.0)
    observed = document.materials
    body, = neutral.bodies
    neutral = replace(
        neutral,
        materials=observed,
        bodies=(replace(body, material_id=observed[0].id if observed else None),),
        diagnostics=tuple(row for row in document.diagnostics if row.code.startswith("sldprt.material_")),
    )
    for route in ("registry", "direct"):
        sink = BytesIO()
        if route == "registry":
            write_document(neutral, sink, destination_format="interchange.json")
        else:
            JsonAdapter().write(neutral, sink)
        recovered = CadDocument.from_json(sink.getvalue().decode("utf-8"))
        if (recovered.materials != neutral.materials
                or recovered.bodies[0].material_id != neutral.bodies[0].material_id
                or recovered.diagnostics != neutral.diagnostics):
            raise ValueError(f"{route} lost unresolved material evidence")
    return 2


def check():
    data = checked_source(
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
    )
    assigned = checked_source(
        "named-material/AssignedDensityProbe.SLDPRT",
        "04ddbe3934185b0c484ca60579312aac6dc0d2412317cda58d8c518f8d214583",
    )
    archive = SldprtArchive.from_bytes(data)
    name = "swXmlContents/MATERIALTREE"
    if name in archive.streams:
        raise ValueError("unassigned part acquired a material stream")
    contrast = BuildSldprt(dict(archive.streams) | {name: b"unsupported material evidence"},
                           FormatVersion=archive.format_version)
    results = {"assignment": {}, "invalid_assignment": {},
               "writes_refused": 0, "json_material_states_preserved": 0}
    for mode, include_brep in (("design", False), ("geometry", True)):
        options = dict(source_format="solidworks.sldprt", strict=True, include_brep=include_brep)
        control = open_document(BytesIO(data), **options)
        rejected = open_document(BytesIO(contrast), **options)
        resolved = open_document(BytesIO(assigned), **options)
        if (control.materials or rejected.materials or control.bodies != rejected.bodies
                or control.feature_timeline != rejected.feature_timeline or control.brep != rejected.brep
                or any("solidworks.assigned_part_material" in row.attributes for row in rejected.bodies)
                or (control.brep is not None) != include_brep
                or any(row.code.startswith("sldprt.material_") for row in control.diagnostics)):
            raise ValueError("material evidence changed unassigned semantics")
        outcome, = (row for row in rejected.diagnostics if row.code == "sldprt.material_assignment_unresolved")
        expected = "SOLIDWORKS assigned material density is absent, overridden or inconsistent"
        if outcome.message != expected:
            raise ValueError("unexpected reason to decline unowned material")
        material, = resolved.materials
        body, = resolved.bodies
        assignment = body.attributes["solidworks.assigned_part_material"]
        record = (material.id, material.Density, material.ColorValue, body.material_id)
        if (record != ("sldprt:material:258", 2700.0, None, material.id)
                or assignment["native_atom_id"] != 101
                or assignment["native_feature_id"] != 34
                or assignment["name"] != material.name
                or (resolved.brep is not None) != include_brep
                or not any(row.code == "sldprt.material_domains_unresolved" for row in resolved.diagnostics)):
            raise ValueError("assigned reader lost its owning body, material or actual density")
        reopened = CadDocument.from_json(resolved.to_json())
        if reopened.materials != resolved.materials or reopened.bodies[0].material_id != body.material_id:
            raise ValueError("neutral json lost the physical material or body link")
        results["assignment"][mode] = record
        results["invalid_assignment"][mode] = outcome.message
        results["writes_refused"] += refuse_writes(reopened) + refuse_writes(rejected)
        results["json_material_states_preserved"] += preserve_json(reopened) + preserve_json(rejected)
    return results


if __name__ == "__main__":
    print(dumps(check(), sort_keys=True))
