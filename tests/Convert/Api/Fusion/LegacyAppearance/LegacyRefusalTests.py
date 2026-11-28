from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.LegacyAppearance.LegacyCase import LegacyCase
from tests.Convert.Api.Fusion.LegacyAppearance.RefuseLegacy import RefuseLegacy


# exact missing extra and invalid typed states must refuse across the process boundary
def TestLegacyBad(TmpPath: FilePath) -> None:
    Request = LegacyCase(TmpPath / "Request")
    Original = Request.read_bytes()
    Output = TmpPath / "Groups"
    Output.mkdir()
    Cases = LoadJson(
        FilePath(__file__).with_name("RefusalCases.json").read_text(encoding="utf-8")
    )
    for CaseValue in Cases:
        Values = LoadJson(Original)
        Target = Values[CaseValue["group"]]
        if CaseValue.get("remove"):
            del Target[CaseValue["key"]]
        else:
            Target[CaseValue["key"]] = CaseValue["value"]
        _ = Request.write_text(DumpJson(Values, allow_nan=False), encoding="utf-8")
        RefuseLegacy(Request, Output, CaseValue["reason"])
