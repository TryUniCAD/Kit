from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Integration.Fusion.RimFillet.Policy.RimPolicyCase import (
    RimPolicyCase,
)


# all source groups must retain exact archive hashes alongside their actual native parameter observations
def ReadPolicyCases() -> tuple[RimPolicyCase, ...]:
    RootPath = FilePath(__file__).resolve().parents[6]
    Campaign = RootPath / "re/Fusion/RimFilletPack"
    Result: list[RimPolicyCase] = []
    for Value in LoadJson((Campaign / "Qualification/Cases.json").read_text()):
        CaseName = str(Value["id"])
        Source = Campaign / (
            "Sources/" + CaseName.removeprefix("source-") + "/Native.f3d"
            if CaseName.startswith("source-")
            else "Qualification/Archives/" + CaseName + "/Native.f3d"
        )
        Parameters = tuple(
            (
                str(Entry["name"]),
                float(Entry["value"]),
                str(Entry["unit"]),
                str(Entry["expression"]),
            )
            for Entry in Value["measurements"]["initial"]["parameters"]
        )
        Result.append(
            RimPolicyCase(CaseName, Source, str(Value["source_sha256"]), Parameters)
        )
    return tuple(Result)
