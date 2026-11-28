from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigFieldSets import (
    KConfigArrays,
    KConfigZeroes,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import (
    ConfigSpec,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.MakeMassProps import (
    MakeMassProps,
)


# configuration values must come from authored intent or the documented fresh constructor and preserve independent native collection owners
def MakeCfgSeeds(InputValue: ConfigSpec, VersionValue: int) -> dict[str, object]:
    FieldsValue: dict[str, object] = dict.fromkeys(KConfigZeroes, 0)
    for NameValue in KConfigArrays:
        FieldsValue[NameValue] = []
        FieldsValue[f"n{NameValue[1:]}"] = 0
    FieldsValue.update(
        {
            "f4a8": InputValue.Description,
            "f4b0": -1,
            "f4c4": 0x100,
            "f498": "",
            "f860": 101,
            "f668": MakeMassProps(),
            "f678": InputValue.UpdatedAt,
            "f6a0": None,
            "f6a8": {"n": 0, "items": []},
            "f528": {"n": 0, "items": []},
            "f9a8": VersionValue,
            "f96c": 1,
            "f660": None,
            "fa98": {"n": 0, "items": []},
            "faf0": 0,
            "faf4": 1,
            "f788": 1,
            "f78c": -1.0,
            "f790": -1.0,
            "fb30": 1,
            "f844": 1,
            "f750": -1,
            "fbd4": 1,
            "f600": {"n": 0, "items": []},
            "fb68": {"n": 0, "items": []},
            "fb80": None,
            "fbd8": None,
        }
    )
    return FieldsValue
