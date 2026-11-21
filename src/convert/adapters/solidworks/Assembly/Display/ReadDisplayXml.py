from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Assembly.Display.DisplayMember import DisplayMember
from convert.adapters.solidworks.Assembly.Display.DisplayOwner import DisplayOwner

# the measured display profile binds roles in the native assembly namespace
KDisplayNs = {"sw": "http://www.solidworks.com/sw2003/schema"}


# visibility actions require an explicit persistent occurrence identity and positive polarity
def ReadDispMember(NodeValue: Element) -> DisplayMember:
    Values = NodeValue.attrib
    if Values["swHidden"] != "NO" or Values["swSuppressed"] != "NO":
        raise ValueError("assembly display visibility conflicts with occurrence state")
    RefNumber = int(Values["swReferenceNumber"])
    FeatureId = int(Values["swID"])
    if (
        RefNumber < 1
        or FeatureId < 1
        or str(RefNumber) != Values["swReferenceNumber"]
        or str(FeatureId) != Values["swID"]
        or not Values["swName"]
    ):
        raise ValueError("assembly display reference has an ambiguous identity")
    return DisplayMember(
        int(Values["id"]), FeatureId, f'{Values["swName"]}-{RefNumber}', True
    )


# ordered display actions need a complete config list and one measured leaf owner
def ReadDisplayXml(RootValue: Element) -> DisplayOwner:
    if (
        RootValue.tag != f'{{{KDisplayNs["sw"]}}}swSolidWorks'
        or RootValue.get("swVersion") != "19000"
    ):
        raise ValueError("assembly display state is outside the measured XML version")
    (ConfigList,) = RootValue.findall("sw:swConfigurationList", KDisplayNs)
    (ConfigValue,) = tuple(ConfigList)
    (ModelList,) = RootValue.findall("sw:swModelList", KDisplayNs)
    (ModelValue,) = (
        RowValue
        for RowValue in ModelList
        if RowValue.get("id") == ConfigValue.get("swModelRef")
    )
    (HeaderValue,) = RootValue.findall("sw:swHeader", KDisplayNs)
    (FileValue,) = (
        RowValue
        for RowValue in HeaderValue.findall("sw:swFile", KDisplayNs)
        if RowValue.get("id") == ModelValue.get("swFileRef")
    )
    (ListValue,) = ConfigValue.findall("sw:swDisplayStateList", KDisplayNs)
    (StateValue,) = tuple(ListValue)
    RefValues = tuple(ModelValue.findall("sw:swReference", KDisplayNs))
    Roles = {
        "swConfiguration": (ConfigValue,),
        "swDisplayStateList": (ListValue,),
        "swDisplayState": (StateValue,),
        "swReference": RefValues,
    }
    for RoleName, NodesValue in Roles.items():
        if (
            tuple(
                RowValue
                for RowValue in RootValue.iter()
                if RowValue.tag.rsplit("}", 1)[-1] == RoleName
            )
            != NodesValue
        ):
            raise ValueError(
                "assembly display state has detached or ambiguous XML owners"
            )
    Identifiers = sorted(
        (
            RowValue.attrib["id"]
            for RowValue in RootValue.iter()
            if "id" in RowValue.attrib
        ),
        key=int,
    )
    if (
        str(len(Identifiers)) != RootValue.attrib["swObjCount"]
        or any(
            IdValue != str(Position) for Position, IdValue in enumerate(Identifiers, 1)
        )
        or (int(ListValue.attrib["id"]), int(StateValue.attrib["id"]))
        != (len(Identifiers) - 1, len(Identifiers))
    ):
        raise ValueError("assembly display state has inconsistent XML-local identities")
    if (
        ConfigValue.tag != f'{{{KDisplayNs["sw"]}}}swConfiguration'
        or ModelValue.tag != f'{{{KDisplayNs["sw"]}}}swModel'
        or StateValue.tag != f'{{{KDisplayNs["sw"]}}}swDisplayState'
        or FileValue.get("swDocType") != "ASSEMBLY"
        or ConfigList.get("swObjCount") != "1"
        or ModelList.get("swObjCount") != str(len(ModelList))
        or ConfigValue.get("swMostRecentConfiguration") != "YES"
        or ConfigValue.get("swID") != "0"
        or not ConfigValue.get("swName")
        or not ConfigValue.get("swReference")
        or set(ListValue.attrib) != {"id", "swCompNameList"}
        or set(StateValue.attrib) != {"id", "swDisplayStateName", "swShowState"}
        or len(StateValue)
        or not StateValue.attrib["swDisplayStateName"]
        or len(RefValues) not in (1, 2, 3)
    ):
        raise ValueError("assembly display state has an unqualified ordinary owner")
    MembersValue = tuple(ReadDispMember(RowValue) for RowValue in RefValues)
    if (
        len({RowValue.FeatureId for RowValue in MembersValue}) != len(MembersValue)
        or ListValue.attrib["swCompNameList"]
        != "".join(f"{RowValue.FeatureId}," for RowValue in MembersValue)
        or StateValue.attrib["swShowState"] != "Yes," * len(MembersValue)
    ):
        raise ValueError(
            "assembly display state cannot bind the measured ordered visibility"
        )
    return DisplayOwner(
        int(ConfigValue.attrib["id"]),
        int(ConfigValue.attrib["swID"]),
        ConfigValue.attrib["swName"],
        int(ModelValue.attrib["id"]),
        ConfigValue.attrib["swReference"],
        int(ListValue.attrib["id"]),
        int(StateValue.attrib["id"]),
        StateValue.attrib["swDisplayStateName"],
        MembersValue,
    )
