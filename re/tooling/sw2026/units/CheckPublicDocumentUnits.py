from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def expected(mass, places):
    if mass is None:
        return None
    return {
        "system": "custom",
        "length": "mm",
        "angle": "degree",
        "mass": mass,
        "volume": "mm^3",
        "length_decimal_places": places,
        "angle_decimal_places": places,
        "mass_decimal_places": places,
    }


def read(source, source_format=None):
    from convert import open_document

    model = open_document(source, source_format=source_format, include_tessellation=False)
    model.assert_valid()
    report = model.metadata["solidworks.typed_resolved_semantics"]
    require(report["status"] == "supplemented", "typed model supplement was lost")
    require(model.brep is not None, "strict read lost the solid topology")
    topology = [len(getattr(model.brep, key)) for key in ("vertices", "edges", "faces", "shells", "bodies")]
    require(topology == [8, 12, 6, 1, 1], "strict read changed the rectangular solid topology")
    return {
        "units": report.get("document_units"),
        "topology": topology,
        "tree": [entry.name for entry in model.feature_timeline],
    }


def edited(raw, kind):
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    config = link.ConfigValue
    table = config.RootValue.FieldsValue["f9b8"].FieldsValue["items"]
    units = {row["o"].ClassValue.NameValue: row["o"] for row in table}
    length = units["moLengthUserUnits_c"]
    density = units["moDensityUnits_c"].FieldsValue
    match kind:
        case "other-mass":
            density["fc4"] = 0
        case "other-volume":
            density["fcc"] = 1
        case "alternate-length-format":
            density["fb8"].FieldsValue["f88"] = 2.0
        case "aliased-length-format":
            density["fb8"] = length
        case "other-angle":
            units["moAngleUserUnits_c"].FieldsValue["fb0"] = 3
        case "other-length":
            length.FieldsValue["fb0"] = 2
            density["fb8"].FieldsValue["fb0"] = 2
        case _:
            raise ValueError("unknown custom document units edit")
    config_bytes, context = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    resolved, _ = WriteResolMut(
        link.ResolvedValue.RootsValue,
        link.ResolvedValue.ExtraFields,
        19000,
        context.MapValue,
        link.ResolvedValue.ContextValue,
    )
    streams = archive.streams
    require(config_bytes != streams[link.ConfigName], "custom-unit edit did not change Config-0")
    streams.update({link.ConfigName: config_bytes, link.StreamName: resolved})
    return BuildSldprt(streams, FileId=archive.file_id, FormatVersion=archive.format_version)


def worker(plan_path, index):
    row = json.loads(plan_path.read_text(encoding="utf-8"))["cases"][index]
    relative = Path(row["path"])
    require(not relative.is_absolute() and ".." not in relative.parts, "input path escapes evidence root")
    path = plan_path.parent / relative
    raw = path.read_bytes()
    require(digest(raw) == row["sha256"], "public read input changed")
    result = read(path)
    require(result == read(raw, "solidworks.sldprt"), "normal path and bytes reads differ")
    require(result["units"] == expected(row["mass"], row["places"]), "document units differ")
    checks = {}
    for kind in row.get("edits", []):
        candidate = edited(raw, kind)
        observed = read(candidate, "solidworks.sldprt")
        require(observed == dict(result, units=None), "document unit guard changed the model read")
        checks[kind] = digest(candidate)
    return {"role": row["role"], "sha256": row["sha256"], **result, "omitted_edits": checks}


def main():
    parser = ArgumentParser(description="Verify scoped custom units through strict public SOLIDWORKS reads")
    parser.add_argument("plan", type=Path)
    parser.add_argument("result", type=Path, nargs="?")
    parser.add_argument("--plan-sha256")
    parser.add_argument("--worker", type=int)
    args = parser.parse_args()
    plan = args.plan.resolve(strict=True)
    if args.worker is not None:
        print(json.dumps(worker(plan, args.worker), allow_nan=False))
        return
    raw = plan.read_bytes()
    require(args.result is not None and digest(raw) == args.plan_sha256, "public read plan changed")
    rows = json.loads(raw)["cases"]
    records = []
    for index in range(len(rows)):
        run = subprocess.run(
            [sys.executable, "-I", "-B", str(Path(__file__).resolve()), str(plan), "--worker", str(index)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        require(run.returncode == 0, f"{rows[index]['role']}: {run.stderr.strip()}")
        records.append(json.loads(run.stdout))
    result = {
        "schema": "kit.sw2026.public-document-units-read.v1",
        "plan_sha256": args.plan_sha256,
        "observer_sha256": digest(Path(__file__).read_bytes()),
        "cases": records,
        "passed": True,
    }
    with args.result.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"cases": len(records), "result_sha256": digest(args.result.read_bytes())}))


if __name__ == "__main__":
    main()
