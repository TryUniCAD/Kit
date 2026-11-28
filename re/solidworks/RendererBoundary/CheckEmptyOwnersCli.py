from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from subprocess import run
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "re/automation"))
from EncoderRoundTrip.Artifacts import canonical_json


def smoke(args):
    args.output.mkdir()
    fixture = ROOT / "re/solidworks/measurements/2026/EncoderRoundTrip/Requests/ExactSketchWithPresentation.json"
    request = json.loads(fixture.read_bytes())
    request["document"]["configurations"]["$tuple"][0]["name"] = "Default"
    part = args.output / "Part.json"
    part.write_bytes(canonical_json(request))
    appearance = args.output / "Appearance.json"
    appearance.write_bytes(canonical_json({"AppearanceValue": {"ManagerOnWire": True, "NextAppearanceId": 4}}))
    prop = args.property_root / "re/solidworks/PropertyBoundary/Requests/Present.json"
    supplied = [part, appearance, prop]
    original = [path.read_bytes() for path in supplied]
    assert sha256(original[0]).hexdigest() == "cdefa9be027d8257c0f5b08cf722efff746f38960b86e5e73eac2e63bf7d1ac4"
    composer = Path(__file__).with_name("ComposeEmptyOwnersPart.py")
    method = composer.read_bytes()
    command = [sys.executable, "-I", "-B", str(composer),
               "--dependency-root", str(args.dependency_root), "--property-root", str(args.property_root),
               "--part-request", str(part), "--appearance-request", str(appearance),
               "--locator", r"C:\KitEncoderRoundTrip\reconstruction.SLDPRT", "--epoch", "1785626030"]
    output = args.output / "Generated"
    reply = run([*command, "--property-request", str(prop), "--output", str(output)], capture_output=True, timeout=120)
    assert reply.returncode == 0, reply.stderr.decode(errors="replace")
    report = json.loads(reply.stdout)
    assert canonical_json(report) == (output / "Evidence.json").read_bytes()
    archive = (output / "reconstruction.SLDPRT").read_bytes()
    assert sha256(archive).hexdigest() == report["archive"]["sha256"]
    assert len(archive) == report["archive"]["bytes"]
    assert report["sdk_revision"] == "c0a401a607759fb0c2589647c2a22af65ebb7ce1"
    assert report["property_revision"] == "5fb7e7737f0b9af52373da5e3f4556cd83ba8607"
    assert report["requests_sha256"] == dict(zip(("part", "appearance", "property"), (sha256(data).hexdigest() for data in original)))
    assert report["configuration"] == {"id": 0, "name": "Default", "config_xml_owner_verified": True}
    assert report["appearance"]["appearance"] == {"ManagerOnWire": True, "NextAppearanceId": 4}
    assert report["appearance"]["signed_counter_words"] == [4, 0]
    assert report["appearance"]["reference_rows"] == 0
    assert report["property"]["actual_cut_owner"] is True
    assert report["property"]["owner_slots"] == [[2, "moCusPropMgr_c"], [4, "moCusPropContainer_c"], [6, "moFilePropContainer_c"], [8, "moCutListPropContainer_c"]]
    assert report["property"]["exact_reemit"] is True and report["property"]["map_next"] == 9
    assert report["clear_streams"]["Contents/CusProps"] == [138, "9fd3dc57a5b385acbbd4b0f36fffec581481014616bb254a4f417f3537c1f036"]
    assert report["clear_streams"]["Contents/Definition"] == [469, "88bdf38bd957f45e54a95340dfb74a593408b2aa30c51f62f0faf5a3e312378a"]
    assert len(report["clear_streams"]) == 14 and report["changed_base_streams"] == ["Contents/Definition"]
    assert report["added_streams"] == ["Contents/CusProps", "docProps/Config-0-Properties.xml", "docProps/core.xml", "docProps/custom.xml"]
    assert report["geometry"]["depth_m"] == float(0.01431).hex()
    assert report["geometry"]["top"]["id"] == 200 and report["geometry"]["derived_prism"]["topology"] == [6, 12, 8]
    assert report["external_generation_attempts"] == report["native_launches"] == 0
    assert report["readers"]["ordinary_definition"] == {"returned": False, "reason": "SOLIDWORKS part Definition has an alternate renderer profile"}
    for role, operation in (("base", "create"), ("final", "join")):
        read = report["readers"]["public_121"][role]
        assert read["default"] == {"returned": False, "reason": "SLDPRT contains no readable Parasolid payload"}
        assert read["without_brep"] == {"returned": True, "bodies": 1, "boss_operation": operation, "diagnostics": ["sldprt.native_record_unresolved"]}
    rejected = args.output / "IntegerCut.json"
    invalid = json.loads(original[2])
    invalid["empty_cut_owner"] = 1
    rejected.write_bytes(canonical_json(invalid))
    refused = args.output / "Refused"
    negative = run([*command, "--property-request", str(rejected), "--output", str(refused)], capture_output=True, timeout=120)
    assert negative.returncode == 1 and not negative.stdout and not refused.exists()
    assert b"empty cut-owner presence must be a Boolean" in negative.stderr
    assert [path.read_bytes() for path in supplied] == original
    assert (output / "reconstruction.SLDPRT").read_bytes() == archive
    assert composer.read_bytes() == method
    result = {"composer_sha256": sha256(method).hexdigest(), "generated": report["archive"]["sha256"],
              "sdk_revision": report["sdk_revision"], "property_revision": report["property_revision"],
              "refusal_exit": negative.returncode, "ordinary_definition_returned": False,
              "default_public_returned": False, "native_launches": 0}
    (args.output / "Smoke.json").write_bytes(canonical_json(result))
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description="Smoke the real pinned three-request composition command")
    for name in ("dependency-root", "property-root", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    sys.stdout.buffer.write(canonical_json(smoke(parser.parse_args())))
