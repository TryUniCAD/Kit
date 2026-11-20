from json import loads as LoadJson
from math import degrees as Degrees
from os import environ as ProcessEnvironment, pathsep as PathSeparator
from subprocess import run as RunProcess


# independently applied reader patches must preserve exact native scalar provenance through the public cli
def VerifyReplay(TmpPath, Command, Checkout, RootPath, Target, Native, Stream, Offset):
    After = TmpPath / "after.json"
    RunProcess(
        [*Command, str(After)],
        cwd=Checkout,
        check=True,
        timeout=180,
        env={
            **ProcessEnvironment,
            "PYTHONPATH": PathSeparator.join(
                map(str, (Checkout / "src", RootPath / "Cli"))
            ),
        },
    )
    (Parameter,) = [
        Record
        for Record in LoadJson(After.read_bytes())["document"]["parameters"]["$tuple"]
        if Record["id"] == Target
    ]
    assert Parameter["value"]["value"] == Degrees(Native)
    assert Parameter["attributes"]["native_value"] == Native
    (SpanValue,) = Parameter["provenance"]["spans"]["$tuple"]
    assert (
        SpanValue["stream"],
        SpanValue["offset"],
        SpanValue["length"],
        SpanValue["record_kind"],
    ) == (
        Stream,
        Offset,
        8,
        "dimension-scalar",
    )
