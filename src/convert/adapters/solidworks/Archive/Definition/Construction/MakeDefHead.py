from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Definition.Construction.DefDisplayWords import (
    DefDisplayWords,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeNotebook import (
    MakeNotebook,
)
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# authored presentation and shared ui constructor state supply the head of a fresh model definition
def MakeDefHead(Settings: ModelDefInput) -> dict[str, object]:
    LowValue, HighValue = DefDisplayWords(Settings.DisplayBits)
    ShadedLevel, AngularLevel, WireLevel, OptimalValue = Settings.Tessellation
    return {
        "fa58": ShadedLevel,
        "fa5c": AngularLevel,
        "fa60": WireLevel,
        "fa64": int(OptimalValue),
        "fa74": 1,
        "fac0": None,
        "fac8": 0,
        "fae8": IdentityXform(),
        "faf0": IdentityXform(),
        "facc": 3,
        "fad0": 0,
        "fad4": 3,
        "fad8_0": LowValue,
        "fad8_1": HighValue,
        "fba8": ArchiveNode(RuntimeClass(Settings.DraftingStandard, 1), {}),
        "f878": {"styles": []},
        "f870": ArchiveNode(RuntimeClass("uiLineFontMgr_c", 1), {"f10": []}),
        "faf8": [],
        "basedoc": {"ole": {"f7f8": []}, "f2a0": 0},
        "fbf0": {"f08": None, "f10": 0},
        "fb20": None,
        "fb54": 0,
        "fb3c": -1,
        "fb40": -1,
        "fd68": 0x12035,
        "f850": 0,
        "fab8": None,
        "fb00": 0,
        "fb04": 0,
        "fa6c": 0,
        "fa10": None,
        "fa98": 0x203,
        "ffd8": MakeNotebook(Settings.JournalName),
        "f1000": 0,
        "fa90": int(Settings.Preference7a),
        "f1014": 1,
        "expand_keys": {"items": []},
        "expand_vals": {"items": []},
        "f7b8": 0,
        "has_pwmaterial": 0,
    }
