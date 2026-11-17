from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateSelection import (
    MateSelection,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CheckChildRoots import (
    CheckChildRoots,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    ReadNodeName,
    RequireNode,
    RequireRecord,
)


# child selections must agree by actual ownership file definition configuration and current model epoch
def CheckMateChild(Selection: MateSelection) -> int:
    Child = Selection.ChildValue
    Model = RequireNode(Child.ModelValue, "moPart_c")
    Header = RequireNode(Child.HeaderValue, "moHeader_c")
    Configuration = RequireNode(Child.ConfigValue, "moPartConfiguration_c")
    Datum = RequireNode(Selection.DatumValue, "moRefPlane_c")
    CheckChildRoots((Model, Header, Configuration, Datum))
    if (
        Datum.FieldsValue.get("owner") is not Model
        or not any(Value is Datum for Value in Child.FeaturesValue)
        or Configuration.FieldsValue.get("owner") is not Model
    ):
        raise ValueError(
            "mate datum and configuration must belong to the actual child part"
        )
    Occurrence = RequireNode(Selection.OccurrenceValue, "moReference_c")
    External = RequireNode(Occurrence.FieldsValue.get("f3b0"), "moExtObject_c")
    ChildFile = RequireNode(Header.FieldsValue.get("f38"), "moExtObject_c")
    if (
        ReadFileKey(External) != ReadFileKey(ChildFile)
        or ReadFileKey(ChildFile)[2] != 2
    ):
        raise ValueError("mate occurrence targets a different child file definition")
    Selected = RequireRecord(Occurrence.FieldsValue.get("f3c0"))
    ConfigId = FieldInt(Configuration.FieldsValue, "f08")
    if (
        FieldInt(Selected, "f10") != ConfigId
        or FieldText(Selected, "f08") != ReadNodeName(Configuration)
        or FieldInt(Occurrence.FieldsValue, "f3e0")
        != FieldInt(Header.FieldsValue, "f40")
    ):
        raise ValueError("mate occurrence child configuration or update differs")
    if (
        FieldInt(Datum.FieldsValue, "f08") < 0
        or FieldInt(Datum.FieldsValue, "f34c") != 0
    ):
        raise ValueError(
            "mate construction requires a registered ordinary principal datum"
        )
    return ConfigId
