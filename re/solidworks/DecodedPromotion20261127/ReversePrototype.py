from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys


def run(root, output):
    sys.path[:0] = [str(root / "src"), str(root)]
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
    from convert.adapters.solidworks.Container.Container import BuildSldprt
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc

    for name in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    for name in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(name)
    import_module("xml.parsers.expat")
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if revision != "91a73de348894a5791a51b977cd6fe0fe677a617":
        raise ValueError("research prototype requires the pinned production revision")
    output.mkdir(parents=True, exist_ok=False)
    active = False
    denied = []

    def audit(event, arguments):
        if active and (event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.startfile", "os.fork", "os.forkpty"} or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))):
            denied.append(event)
            raise PermissionError("external access forbidden during generated construction: " + event)

    sys.addaudithook(audit)
    cases = (
        ("discoveryTriangle", ((-11.25, -3.5), (17.125, -1.25), (2.75, 20.5)), 7.625),
        ("holdoutStep", ((-8.5, -6.25), (26.75, -6.25), (26.75, 18.125), (7.375, 18.125), (7.375, 2.5), (-8.5, 2.5)), 13.375),
        ("holdoutQuad", ((-17.25, 3.125), (2.625, -8.75), (19.5, 7.25), (0.375, 25.5)), 23.125),
    )
    rows = []
    for label, corners, depth in cases:
        cross = tuple(a[0] * b[1] - b[0] * a[1] for a, b in zip(corners, corners[1:] + corners[:1], strict=True))
        area = sum(cross) / 2
        centroid = tuple(sum((a[index] + b[index]) * weight for a, b, weight in zip(corners, corners[1:] + corners[:1], cross, strict=True)) / (6 * area) for index in (0, 1))
        for reverse in (False, True):
            name = label + ("Reverse" if reverse else "Forward")
            model = MakePlainDoc(name, corners, depth)
            active = True
            try:
                candidate = PrepareNative(model, BytesIO(), 1795737600, WriteOptions(values={"final_destination": rf"C:\KitReverseResearch\{name}.SLDPRT"}))
                end = candidate.BossValue.EndValue
                if end.ClassValue.NameValue != "moEndSpec_c" or end.FieldsValue["f140"].FieldsValue["t"] != 0:
                    raise ValueError("constructor did not supply the loader-proven blind sketch-plane start")
                end.FieldsValue["f8c"] = int(reverse)
                recipe = MakePartRecipe(candidate.PlanValue, 1795737600)
                streams, _, _ = EmitPartStreams(candidate.SystemValue, (*candidate.SystemValue.FeatureValues, candidate.ProfileValue.ProfileValue, candidate.BossValue.FeatureValue), (candidate.HeaderValue, candidate.TopHeader, candidate.ManagerHeader), candidate.DefinitionValue, recipe, candidate.PlanValue)
                data = BuildSldprt(streams, FormatVersion=4)
            finally:
                active = False
            path = output / (name + ".SLDPRT")
            path.write_bytes(data)
            row = {"case": name, "cohort": "discovery" if label.startswith("discovery") else "predeclared_parameter_contrast", "semantic_input": {"polygon_mm": corners, "depth_mm": depth, "reversed": reverse}, "sha256": sha256(data).hexdigest(), "bytes": len(data), "expected_geometry": {"volume_mm3": abs(area) * depth, "centroid_mm": [*centroid, depth / 2 * (-1 if reverse else 1)]}, "derived_members": {"moEndSpec_c.f8c": int(reverse), "moFromEndSpec_c.t": 0}, "stream_hashes": {key: sha256(value).hexdigest() for key, value in streams.items()}}
            try:
                doc = open_document(BytesIO(data), source_format="solidworks.sldprt", strict=True)
                features = [feature for feature in doc.feature_timeline if feature.name == "Boss-Extrude1"]
                feature, = features
                row["strict_read"] = {"status": "returned", "reversed": feature.definition.reversed, "depth_mm": feature.definition.length.value, "topology": repr(doc.bodies[0].topology), "body_attributes": repr(doc.bodies[0].attributes), "diagnostics": [repr(value) for value in doc.diagnostics]}
                row["semantic_direction_depth_match"] = feature.definition.reversed == reverse and abs(feature.definition.length.value - depth) < 1e-10
                measured_centroid = doc.bodies[0].attributes.get("solidworks.body_centroid_mm")
                row["strict_centroid_match"] = measured_centroid is not None and all(abs(a - b) < 1e-10 for a, b in zip(measured_centroid, row["expected_geometry"]["centroid_mm"], strict=True))
            except Exception as error:
                row["strict_read"] = {"status": "failed", "exception": type(error).__name__, "message": str(error)}
                row["semantic_direction_depth_match"] = False
                try:
                    partial = open_document(BytesIO(data), source_format="solidworks.sldprt", strict=False, include_brep=False)
                    row["explicit_geometry_omission_read"] = {"status": "returned", "topology": repr(partial.bodies[0].topology), "definitions": [repr(value.definition) for value in partial.feature_timeline if value.name == "Boss-Extrude1"], "diagnostics": [repr(value) for value in partial.diagnostics]}
                except Exception as partial_error:
                    row["explicit_geometry_omission_read"] = {"status": "failed", "exception": type(partial_error).__name__, "message": str(partial_error)}
            rows.append(row)
    report = {"source_revision": revision, "prototype_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "models": "disabled", "native_acceptance": "not_run_api_unavailable", "zero_external_access_during_construction": not denied, "denied_events": denied, "cases": rows, "unresolved": ["native edit/restore/rebuild/save/fresh-process reopen", "modern saved cap-field provenance including reverse CapEnd[1]", "typed forward-only reader rejection and complete reversed cold prism if refused", "native confirmation of regenerated display/configuration defaults"]}
    (output / "Report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"cases": len(rows), "semantic_direction_depth_matches": sum(row["semantic_direction_depth_match"] for row in rows), "zero_external_access": not denied, "native_acceptance": report["native_acceptance"]}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.root.resolve(), args.output.resolve())
