from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose, tau
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(repo), str(repo / "src")]

from convert import open_document
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
from interchange.Features.FeatureAngleRev import AngularRevolve


def digest(raw):
    return sha256(raw).hexdigest()


def coords(value):
    return (value.x, value.y, value.z)


def read_geometry(payload, predicted):
    doc = open_document(payload, source_format="solidworks.sldprt")
    assert not doc.validate() and doc.brep is not None and not doc.brep_payloads
    assert doc.metadata["solidworks.typed_revolve_semantics"]["status"] == "projected"
    (body,) = doc.bodies
    (feature,) = tuple(row for row in doc.feature_timeline if isinstance(row.definition, AngularRevolve))
    assert len(feature.parameter_ids) == 1 and len(feature.selection_ids) == 1
    (angle,) = tuple(row for row in doc.parameters if row.id == feature.parameter_ids[0])
    assert angle.owner_id == feature.id and angle.value.value == predicted["angle_radians"]
    assert feature.attributes["native_reverse_direction"] == predicted["reversed"]
    assert body.final_feature_id == feature.id and not doc.brep.validate(frozenset((body.id,)))
    topology = body.topology
    assert topology.valid and topology.solid_count == topology.shell_count == 1
    assert topology.face_count == (4 if angle.value.value == tau else 6)
    assert isclose(topology.volume, predicted["actual"]["volume_m3"] * 1e9, rel_tol=1e-6)
    assert isclose(topology.surface_area, predicted["actual"]["area_m2"] * 1e6, rel_tol=1e-6)
    box = topology.bounding_box
    assert box is not None
    return {"faces":topology.face_count, "volume_mm3":topology.volume, "area_mm2":topology.surface_area,
            "bounds_mm":[coords(box.minimum),coords(box.maximum)],"revolved_feature":feature.id,
            "live_angle_radians":angle.value.value,"native_direction_reversed":predicted["reversed"]}


def malformed(raw, problem):
    archive = SldprtArchive.from_bytes(raw)
    streams = dict(archive.streams)
    if problem == "unexpected-stream":
        streams["Contents/UnqualifiedGeometry"] = b"unqualified"
        return BuildSldprt(streams, FormatVersion=4)
    link = ReadNativeLink(archive, 0)
    (owner,) = ReadRevOwners(link)
    if problem == "axis-removed":
        owner.NodeValue.FieldsValue["f830"] = None
    elif problem == "alternate-direction":
        owner.NodeValue.FieldsValue["f824"] = 2
    elif problem == "selected-body-flag":
        owner.NodeValue.FieldsValue["f544"] = 1
    elif problem == "invalid-angle":
        owner.AngleValue.ParameterValue.FieldsValue["f58"] = tau + 0.01
    else:
        raise ValueError(problem)
    streams[link.StreamName], _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                                19000, link.ConfigValue.MapValue, link.ResolvedValue.ContextValue)
    modified = BuildSldprt(streams, FormatVersion=4)
    assert SldprtArchive.from_bytes(modified).require(link.StreamName) != archive.require(link.StreamName)
    return modified


def main():
    parser = ArgumentParser(description="Qualify normal cache-free revolve readback against native measurements")
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    native_raw = (args.sources / "LifecycleAdjudication01.json").read_bytes()
    assert digest(native_raw) == "25af072fc6d1122a593c12474c532a35f0b1b3987f519af39bedc3e91f5c27f9"
    native = json.loads(native_raw)
    rows = []
    for case in native["cases"]:
        path = args.sources / "Inputs" / (case["case"] + ".SLDPRT")
        raw = path.read_bytes()
        assert digest(raw) == case["input_sha256"]
        wanted = case["candidate_states"][0]
        from_path = read_geometry(path, wanted)
        assert from_path == read_geometry(raw, wanted)
        no_geometry = open_document(raw, source_format="solidworks.sldprt", include_brep=False,
                                    include_tessellation=False)
        assert no_geometry.brep is None and not no_geometry.brep_payloads
        assert no_geometry.metadata["solidworks.typed_revolve_semantics"]["status"] == "projected"
        saved = (args.sources / "Inspection/Edited" / path.name).read_bytes()
        assert digest(saved) == case["saved_sha256"]
        cached = open_document(saved, source_format="solidworks.sldprt", include_tessellation=False)
        assert cached.brep is not None and len(cached.brep_payloads) == 2 and not cached.validate()
        assert cached.metadata["solidworks.typed_revolve_semantics"]["status"] == "projected"
        assert all(row.code != "sldprt.brep_reconstructed" for row in cached.diagnostics)
        rows.append(dict(from_path, case=case["case"], input_sha256=digest(raw),
                         source_and_bytes_equal=True, cached_control_sha256=digest(saved)))
    by_name = {row["case"]: row for row in rows}
    forward = by_name["SdkRevolveForwardBeta"]["bounds_mm"]
    reverse = by_name["SdkRevolveReverseBeta"]["bounds_mm"]
    assert forward[0][2] < 0.0 == forward[1][2]
    assert reverse[0][2] == 0.0 < reverse[1][2]
    assert isclose(forward[0][2], -reverse[1][2], rel_tol=1e-10)
    (sample,) = tuple(row for row in native["cases"] if row["case"] == "SdkRevolveForwardBeta")
    raw = (args.sources / "Inputs/SdkRevolveForwardBeta.SLDPRT").read_bytes()
    assert digest(raw) == sample["input_sha256"]
    faults = []
    for problem in ("unexpected-stream", "axis-removed", "alternate-direction", "selected-body-flag", "invalid-angle"):
        payload = malformed(raw, problem)
        try:
            open_document(payload, source_format="solidworks.sldprt", include_tessellation=False)
        except ValueError as error:
            assert "contains no readable Parasolid payload" in str(error)
            faults.append({"fault":problem,"artifact_sha256":digest(payload),"diagnostic":str(error)})
        else:
            raise ValueError("unqualified revolve entered cache-free geometry: " + problem)
    result = {"schema":"kit.sw2026.public-cache-free-revolve-geometry.v1","passed":True,
              "root_native_lifecycle_sha256":digest(native_raw),"case_count":len(rows),
              "method_sha256":digest(Path(__file__).read_bytes()),
              "geometry_reads":2*len(rows),"semantic_only_reads":len(rows),"native_cache_controls":len(rows),
              "cases":rows,"physical_faults_rejected":faults,"signed_sweep_pair":True,"heldout_inputs_read":0}
    capture = (json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    with args.output.open("xb") as file:
        file.write(capture)
    print(json.dumps({"passed":True,"geometry_reads":result["geometry_reads"],
                      "rejected":len(faults),"result_sha256":digest(capture)}))


if __name__ == "__main__":
    main()
