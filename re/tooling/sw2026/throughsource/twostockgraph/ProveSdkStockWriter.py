from argparse import ArgumentParser
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose, pi
from pathlib import Path
from subprocess import check_output, run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
SHAPE = HERE.parent.parent / "twostockshape"
PART = "GeneratedTwoStockGraph01"
STAMP = 1765500071
HISTORICAL_HASH = "6eca4bed5c698744cb3f33f39b1f15aebb69bedfef658060ef7c1d3a8603a508"
FAULTS = {
    "source-metadata": "authored part name",
    "feature-extension": "active unextended features",
    "foreign-body-pick": "historical Front stock",
    "authored-body-label": "ordered producers and implicit labels",
    "driver-conflict": "actual forward blind millimetre D1",
    "attached-support": "fixed canonical Front and Right supports",
    "invalid-configuration": "ordinary active Default configuration",
    "reserved-name": "distinct authored owner names",
    "touching-circle": "one proper exterior side notch",
    "wrong-destination": "exact authored basename",
    "missing-destination": "explicit final destination",
}
SHARED = (
    "Archive/Construction/BodyScope/BindStockMut.py",
    "Archive/Construction/Extrusion/BindExtrusionMut.py",
    "Core/TypedResolved/Cuts/BuildCircularCut.py",
    "Core/TypedResolved/Cuts/MultiStock/Cold/BuildColdCut.py",
    "Core/TypedResolved/Cuts/MultiStock/Cold/BuildColdGeom.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def armed_guard():
    access = []

    def deny(event, _):
        if event in {
            "open", "os.listdir", "os.scandir", "os.system", "os.exec",
            "os.fork", "os.posix_spawn", "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            access.append(event)
            raise PermissionError("two-stock SDK process tried " + event)

    sys.addaudithook(deny)
    return access


def authored(mode):
    from ProofModels import AUTHORED, FRONT, RIGHT, authored_document

    dimensions = AUTHORED["disclosed-initial"]
    feature_names = ("SteadyStock", "MovingStock", "ThroughFeature")
    profile_names = ("SteadyProfile", "MovingProfile", "ThroughProfile")
    part_name = PART
    if mode == "independent":
        dimensions = {
            "stocks": (
                (FRONT, (-9, -15, 19, -1), 13.625, False),
                (RIGHT, (-20, 8, -6, 19), 31.875, False),
            ),
            "circle": (5, -7, 2.375),
            "selected": 0,
        }
        part_name = "LongerIndependentInboardCut"
        feature_names = (
            "Forward prism with an off-center bore",
            "Separate right-side stock with a different height",
            "Interior through cut chosen by feature",
        )
        profile_names = (
            "Front rectangle profile",
            "Right rectangle profile",
            "Free closed circle",
        )
    document = authored_document(dimensions)
    timeline = tuple(
        replace(row, name=name)
        for row, name in zip(document.feature_timeline, feature_names, strict=True)
    )
    labels = {row.id: row.name for row in timeline}
    return replace(
        document,
        metadata={"name": part_name},
        feature_timeline=timeline,
        sketches=tuple(
            replace(row, name=name)
            for row, name in zip(document.sketches, profile_names, strict=True)
        ),
        bodies=tuple(
            replace(row, name=labels[row.final_feature_id]) for row in document.bodies
        ),
        selections=(
            (replace(document.selections[0], name=f"{timeline[0].name} body"),)
            if mode == "independent" else document.selections
        ),
    )


def damage(document, mode):
    from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
    from interchange.geometry.Models.Selection import SelectPathElem
    from interchange.geometry.Models.VectorPlane import PlaneVector

    front, right, cut = document.feature_timeline
    if mode == "source-metadata":
        return replace(document, metadata={**document.metadata, "native_extra": True})
    if mode == "feature-extension":
        return replace(
            document,
            feature_timeline=(front, replace(right, attributes={"extra": 1}), cut),
        )
    if mode == "foreign-body-pick":
        choice = replace(
            document.selections[0], path=(SelectPathElem("feature", right.id, "body"),)
        )
        return replace(document, selections=(choice,))
    if mode == "authored-body-label":
        first, second = document.bodies
        return replace(document, bodies=(first, replace(second, name="Only this body")))
    if mode == "driver-conflict":
        first, second = document.parameters
        return replace(
            document,
            parameters=(first, replace(second, value=replace(second.value, value=9.875))),
        )
    if mode == "attached-support":
        first, second = document.support_planes
        return replace(
            document, support_planes=(first, replace(second, attributes={"native": 7}))
        )
    if mode == "invalid-configuration":
        return replace(
            document, configurations=(replace(document.configurations[0], name="Other"),)
        )
    if mode == "reserved-name":
        return replace(
            document,
            feature_timeline=(replace(front, name="history"), right, cut),
        )
    if mode == "touching-circle":
        first, second, profile = document.sketches
        circle, point = profile.entities
        center = PlaneVector(21, 0)
        entities = (
            replace(circle, geometry=CircleGeometry(center, 4)),
            replace(point, geometry=PointGeometry(center)),
        )
        return replace(document, sketches=(first, second, replace(profile, entities=entities)))
    return document


def fingerprint(streams, raw):
    return {
        "bytes": len(raw),
        "sha256": sha256(raw).hexdigest(),
        "streams": {
            key: {"bytes": len(value), "sha256": sha256(value).hexdigest()}
            for key, value in sorted(streams.items())
        },
    }


def generated(document, mode):
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import (
        PrepareStockPart,
    )
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    target = BytesIO()
    name = "OtherName" if mode == "wrong-destination" else document.metadata["name"]
    options = WriteOptions(
        values=(
            {} if mode == "missing-destination"
            else {"final_destination": rf"C:\KitSdkCandidates\{name}.SLDPRT"}
        )
    )
    if mode in FAULTS:
        try:
            PrepareStockPart(document, target, STAMP, options)
        except ValueError as error:
            require(FAULTS[mode] in str(error), f"{mode} reached the wrong boundary: {error}")
            require(not target.getvalue(), "refused preparation modified its destination")
            return {"refusal": str(error)}
        raise ValueError(f"{mode} unexpectedly reached generation")
    require(not SldprtWriter().supports(document, target), "public eligibility opened")
    candidate = PrepareStockPart(document, target, STAMP, options)
    require(not target.getvalue(), "pure preparation wrote to its caller destination")
    return {
        **fingerprint(candidate.StreamsValue, candidate.BytesValue),
        "strict_readback": read_generated(candidate.BytesValue, document),
        "public_writer_eligible": False,
    }


def read_generated(raw, authored):
    from convert import open_document
    from ProvePublicColdStocks import inspect_cold, inspect_document

    document = open_document(
        raw, source_format="solidworks.sldprt", strict=True, configuration="Default",
        include_brep=True, include_tessellation=False,
    )
    report = inspect_document(document)
    inspect_cold(document, report)
    operations = {
        row.name: row for row in document.feature_timeline
        if row.operation in ("create", "cut")
    }
    for expected in authored.feature_timeline:
        actual = operations[expected.name]
        require(actual.operation == expected.operation, "authored feature operation changed")
        if expected.parameter_ids:
            actual_driver = next(p for p in document.parameters if p.owner_id == actual.id)
            expected_driver = next(p for p in authored.parameters if p.owner_id == expected.id)
            require(
                actual_driver.name == expected_driver.name
                and isclose(actual_driver.value.value, expected_driver.value.value, rel_tol=1e-12),
                "authored D1 changed",
            )
    require(
        [body.name for body in document.bodies] == [body.name for body in authored.bodies]
        and {value.name for value in authored.sketches} <= {value.name for value in document.sketches}
        and {value.name for value in authored.support_planes}
        <= {value.name for value in document.support_planes},
        "strict readback changed authored labels or body ordering",
    )
    return report


def worker(mode):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(SHAPE)]
    imports = [
        "ProofModels",
        "convert",
        "convert.adapters.solidworks.Core.Adapter",
        "convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart",
        "convert.adapters.solidworks.Core.Writing.SldprtWriter",
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "ProvePublicColdStocks",
        "ProveRebuiltColdStocks",
    ]
    if mode == "historical":
        imports.extend(("BuildTwoStockGraph", "LinkTwoStockGraph"))
    for name in imports:
        import_module(name)
    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(encoding)
    attempts = armed_guard()
    document = damage(authored(mode), mode)
    if mode == "historical":
        from BuildTwoStockGraph import build_owner_graph
        from LinkTwoStockGraph import link_graph

        control = link_graph(build_owner_graph(document, STAMP))
        result = fingerprint(control.streams, control.payload)
    else:
        result = generated(document, mode)
    require(not attempts, f"{mode} attempted external access: {attempts}")
    return {**result, "runtime_access_attempts": len(attempts)}


def launch(mode):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode),
        input=b"", capture_output=True, timeout=90,
    )
    require(child.returncode == 0, f"{mode} failed: {child.stderr.decode()}")
    return json.loads(child.stdout)


def check_independent(bodies):
    moving, fixed = tuple(bodies.values())
    bore_area = pi * 2.375**2
    remainder = 28 * 14 - bore_area
    expect = (
        (
            6, 14 * 11 * 31.875, 2 * (14 * 11 + (14 + 11) * 31.875),
            (31.875 / 2, 13.5, 13),
        ),
        (
            7, remainder * 13.625,
            2 * (28 * 14 + (28 + 14) * 13.625) + 2 * pi * 2.375 * 13.625 - 2 * bore_area,
            (5, (28 * 14 * -8 + bore_area * 7) / remainder, 13.625 / 2),
        ),
    )
    for actual, (faces, volume, area, centre) in zip((moving, fixed), expect, strict=True):
        require(
            actual["faces"] == faces
            and isclose(actual["volume_mm3"], volume, rel_tol=1e-12)
            and isclose(actual["area_mm2"], area, rel_tol=1e-12)
            and all(isclose(left, right, rel_tol=1e-12) for left, right in zip(
                actual["centre_mm"], centre, strict=True
            )),
            "independent closed geometry disagrees with the analytic prediction",
        )


def prove():
    modes = ("historical", "disclosed", "independent", *FAULTS)
    results = {mode: launch(mode) for mode in modes}
    old, new, other = (results[mode] for mode in modes[:3])
    require(
        old["sha256"] == new["sha256"] == HISTORICAL_HASH
        and old["bytes"] == new["bytes"] == 8574
        and old["streams"] == new["streams"]
        and len(new["streams"]) == len(other["streams"]) == 10,
        "disclosed SDK output differs from the historical neutral composer",
    )
    require(
        any(new["streams"][key]["bytes"] != other["streams"][key]["bytes"] for key in
            ("Contents/Config-0", "Contents/ResolvedFeatures", "swXmlContents/KeyWords")),
        "independent authored inputs did not vary measured stream lengths",
    )
    check_independent(other["strict_readback"]["bodies"])
    source = ROOT / "src/convert/adapters/solidworks"
    paths = (
        HERE,
        *(source / name for name in SHARED),
        *sorted((source / "Core/Preparation/TwoStock").glob("*.py")),
    )
    return {
        "schema": "kit.sw2026.sdk-neutral-two-stock-writer.v1",
        "base_revision": check_output(("git", "rev-parse", "HEAD"), cwd=ROOT).decode().strip(),
        "source_sha256": {
            str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in paths
        },
        "fresh_processes": len(results),
        "results": results,
        "earlier_disclosed_native_packet": "TwoStockColdNative01",
        "new_native_runs": 0,
        "held_out_sources_read": 0,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=("historical", "disclosed", "independent", *FAULTS))
    args = parser.parse_args()
    print(json.dumps(worker(args.worker) if args.worker else prove(), indent=2))


if __name__ == "__main__":
    main()
