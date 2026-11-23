from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
import json
from math import inf, nextafter
from pathlib import Path, PureWindowsPath
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ReplayColdMatSdk import check_design, source_model
from ReplayHeldoutMatSdk import PrepMatPart, SldprtAdapter, WriteOptions, guard, require
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Views.RoundViewSeries import RoundViewSeries
from convert.adapters.solidworks.Archive.Construction.Views.ViewMatrix import ViewMatrix
from convert.adapters.solidworks.Archive.Construction.Views.ViewPlans import KViewPlans
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive, SldprtFormatError


LOCATOR = PureWindowsPath(r"C:\KitColdMaterialExample\ProofShape.SLDPRT")
EPOCH = 1794700000
CASE = {"kind": "center", "configuration": "Default", "width_m": 0.032,
        "height_m": 0.017, "depth_m": 0.024}
CATALOG = ("Synthetic Catalog", "Synthetic Material", 1500.0)
CONFIG = "Contents/Config-0"


def build():
    model = source_model(CASE, CATALOG, LOCATOR)
    return PrepMatPart(model, BytesIO(), EPOCH, WriteOptions(values={"final_destination": str(LOCATOR)}))


def trial_view(candidate):
    index = next(index for index, (name, _) in enumerate(KViewPlans) if name == "*Left")
    _, ((_, angle),) = KViewPlans[index]
    half = angle * -0.5
    sine, cosine = RoundViewSeries(half, 1), RoundViewSeries(half, 0)
    row = candidate.ConfigValue.RootValue.FieldsValue["f9f8"][index]["o"]
    frame = row.FieldsValue["f368"]
    original = frame["f08"]
    nearby = [
        ViewMatrix((0.0 * value, value, 0.0 * value, cosine))
        for value in (sine, nextafter(sine, -inf), nextafter(sine, inf))
    ]
    matrix = next(value for value in nearby if value != original)
    unrelated = {**original, "m0": original["m0"] + 0.125}
    payloads = []
    try:
        for variant in (matrix, unrelated):
            row.FieldsValue["f368"] = {**frame, "f08": variant}
            config, _ = WriteConfigMut(candidate.ConfigValue.RootValue, 19000,
                                       candidate.ConfigValue.HeaderValue)
            streams = dict(candidate.StreamsValue) | {CONFIG: config}
            payloads.append(BuildSldprt(streams, FormatVersion=4))
    finally:
        row.FieldsValue["f368"] = frame
    return tuple(payloads)


def observe(incoming):
    blocked = guard()
    candidate = build()
    alternate, unrelated = trial_view(candidate)
    choices = (candidate.BytesValue, alternate, *((incoming,) if incoming else ()))
    reader = SldprtAdapter()
    for payload in choices:
        archive = SldprtArchive.FromBytes(payload)
        deviations = {name for name, data in archive.streams.items()
                      if data != candidate.StreamsValue.get(name)}
        require(archive.streams.keys() == candidate.StreamsValue.keys()
                and deviations <= {CONFIG}, "only the standard view may vary across platforms")
        document = reader.read(BytesIO(payload), ReadOptions(strict=True, include_brep=True))
        check_design(document, CASE, CATALOG, True)
    try:
        reader.read(BytesIO(unrelated), ReadOptions(strict=True, include_brep=True))
    except SldprtFormatError as error:
        require("standard rotation" in str(error), "unknown presentation failed outside its typed owner")
    else:
        raise ValueError("strict cold reading accepted unrelated camera state")
    extra = BuildSldprt(dict(candidate.StreamsValue) | {
        "docProps/core.xml": b'<?xml version="1.0"?><coreProperties/>',
    }, FormatVersion=4)
    try:
        reader.read(BytesIO(extra), ReadOptions(strict=True, include_brep=False))
    except SldprtFormatError as error:
        require("stream inventory" in str(error), "extra stream failed outside its typed profile")
    else:
        raise ValueError("strict cold reading ignored an extra document property stream")
    require(not blocked, "cold material view probe accessed external runtime data")
    return {
        "passed": True,
        "strict_full_reads": len(choices),
        "unrelated_camera_refusals": 1,
        "unrepresented_stream_refusals": 1,
        "runtime_reads": len(blocked),
        "native_processes_started": 0,
        "cross_platform_sha256": sha256(incoming).hexdigest() if incoming else None,
        "expected_sha256": sha256(candidate.BytesValue).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    arguments = parser.add_mutually_exclusive_group()
    arguments.add_argument("--cross-input", type=Path)
    arguments.add_argument("--emit", type=Path)
    options = parser.parse_args()
    if options.emit is not None:
        payload = build().BytesValue
        with options.emit.open("xb") as output:
            require(output.write(payload) == len(payload), "short synthetic fixture output")
        print(json.dumps({"generated_sha256": sha256(payload).hexdigest(), "native_processes_started": 0}))
    else:
        incoming = options.cross_input.read_bytes() if options.cross_input is not None else None
        print(json.dumps(observe(incoming), sort_keys=True, allow_nan=False))
