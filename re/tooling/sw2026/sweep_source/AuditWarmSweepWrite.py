from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from math import atan2
from pathlib import Path, PureWindowsPath
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent), str(ROOT / "src")]

from AuditSavedSweepMain import checked, demand, disclosed
from CheckSavedSweepSdk import job_bytes, preload
from CheckScopedSweep import RECEIPT, RECEIPT_SHA
from SavedSweepReplay import guard_runtime
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import BuildSweepPart
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwGraph import ReadSwGraph
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter


def inspect(raw, source, case, receipt):
    demand(source["file_sha256"] == case["independent_source_sha256"][source["role"]],
           "saved source missed the exact independent observation")
    model = open_document(BytesIO(raw), source_format=KPartFormatId, strict=True)
    graph = ReadSwGraph(SldprtArchive.from_bytes(raw), Saved=True)
    target = RequirePartPath(case["locator"], case["written_at"])
    intent = SweepIntent(
        PureWindowsPath(target.PathName).stem, graph.SectionValue.CurveValue,
        graph.PathValue.CurveValue, graph.DensityValue.FieldsValue["f58"], target,
    )
    candidate = BuildSweepPart(intent).BytesValue
    candidate_sha = sha256(candidate).hexdigest()
    cold = open_document(BytesIO(candidate), source_format=KPartFormatId, strict=True)
    seam = model.sketches[0].entities[0].attributes["periodic_seam"]
    props = {key: (len(model.metadata[key]) if key in model.metadata else 0)
             for key in ("document_summary", "custom_properties")}
    config = model.configurations[0]
    body = model.bodies[0]
    cold_body = cold.bodies[0]
    demand(body.topology == cold_body.topology, "geometry-only contrast lost actual summary")
    evidence = {
        "final_destination": target.PathName,
        "solidworks_native_measurement": {"written_at": target.SavedAt, "receipt": receipt},
    }
    refusals = []
    for document in (model, open_document(
        BytesIO(raw), source_format=KPartFormatId, strict=True, include_brep=False,
    )):
        for route in ("registry", "direct"):
            sink = BytesIO(b"unchanged")
            try:
                if route == "registry":
                    write_document(document, sink, destination_format=KPartFormatId, values=evidence)
                else:
                    SldprtWriter().write(document, sink, options=WriteOptions(values=evidence))
            except (NotFoundError, TypeError, ValueError) as error:
                expected = {
                    "registry": "solidworks.sldprt does not support the destination",
                    "direct": "sweep requires an ordinary millimetre part with editable geometry only",
                }[route]
                demand(str(error) == expected and sink.getvalue() == b"unchanged" and sink.tell() == 0,
                       "saved writer refusal changed the output")
                refusals.append({"route": route, "include_brep": document.brep is not None,
                                 "category": type(error).__name__, "diagnostic": str(error)})
            else:
                raise ValueError("warm source entered measured cold publication")
    return {
        "slot": source["slot"], "role": source["role"], "source_sha256": source["file_sha256"],
        "same_archive_as_measured_cold": candidate_sha == case["archive_sha256"],
        "geometry_only_candidate_sha256": candidate_sha, "measured_cold_sha256": case["archive_sha256"],
        "identical_neutral_part_name": model.metadata["name"] == cold.metadata["name"],
        "literal_property_counts": {**props, "configuration": len(config.attributes.get("custom_properties", {}))},
        "retained_body_fields_absent_from_cold_projection": sorted(set(body.attributes) - set(cold_body.attributes)),
        "source_body_rgb": body.attributes["native_rgb"],
        "source_body_translucency": body.attributes["native_translucency"],
        "source_body_atom": body.attributes["native_atom_id"],
        "section_seam_rad": atan2(seam["point_mm"][1], seam["point_mm"][0]),
        "cold_section_seam_retained": "periodic_seam" in cold.sketches[0].entities[0].attributes,
        "native_part_publication_refusals": refusals,
    }


def run(path):
    _, jobs = disclosed(path)
    receipt = loads(checked(RECEIPT, RECEIPT_SHA))
    sources = [(job_bytes(job), job, receipt["cases"][job["slot"] - 1]) for job in jobs]
    preload()
    attempts = guard_runtime()
    rows = [inspect(raw, job, case, receipt) for raw, job, case in sources]
    demand(not attempts and len(rows) == 6
           and all(row["same_archive_as_measured_cold"] is (row["role"] == "original") for row in rows)
           and all(not row["cold_section_seam_retained"] for row in rows),
           "warm geometry-only contrast has a changed authority or boundary")
    return {
        "schema": "kit.sw2026.saved-sweep-writer-frontier.v1", "cases": rows,
        "native_calls": 0, "runtime_accesses": len(attempts),
        "published_archives": 0, "protected_inputs": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path, required=True)
    args = parser.parse_args()
    print(dumps(run(args.disclosed), sort_keys=True, indent=2, allow_nan=False))
