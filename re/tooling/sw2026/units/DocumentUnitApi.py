from __future__ import annotations

import json
import os


LIBRARIES = {
    "sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
    "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}",
}
INTERFACES = {
    "IModelDoc2": {"GetUnits", "GetUserUnit", "SetUnits", "GetUnitSystem"},
    "IModelDocExtension": {"GetUserPreferenceInteger", "SetUserPreferenceInteger", "GetWhatsWrongCount"},
    "IUserUnit": {"GetConversionFactor", "GetUnitsString", "GetUserUnit", "SpecificUnitType"},
}
ENUMS = {
    "swUnitSystem_e",
    "swUnitsMassPropMass_e",
    "swUnitsMassPropVolume_e",
    "swUnitsMassPropLength_e",
    "swUserUnitsType_e",
    "swLengthUnit_e",
    "swAngleUnit_e",
    "swUserPreferenceIntegerValue_e",
    "swUserPreferenceOption_e",
}


def select_value(enum, name):
    if enum == "swUserPreferenceIntegerValue_e":
        return name.startswith(("swUnit", "swDual")) or name.endswith("UnitSystem")
    if enum == "swUserPreferenceOption_e":
        return name == "swDetailingNoOptionSpecified"
    return True


def metadata():
    if os.name != "nt":
        raise RuntimeError("registered document unit metadata is measured in the Windows oracle")
    import pythoncom

    pythoncom.CoInitialize()
    try:
        libraries = {
            key: pythoncom.LoadRegTypeLib(identity, 34, 0, 0)
            for key, identity in LIBRARIES.items()
        }
        if any(tuple(library.GetLibAttr()[3:5]) != (34, 0) for library in libraries.values()):
            raise RuntimeError("registered document unit API is outside the exact type library version")
        interfaces = {}
        enums = {}
        for key, library in libraries.items():
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                if key == "sldworks" and name in INTERFACES:
                    methods = []
                    for ordinal in range(info.GetTypeAttr().cFuncs):
                        descriptor = info.GetFuncDesc(ordinal)
                        names = list(info.GetNames(descriptor.memid))
                        if names and names[0] in INTERFACES[name]:
                            methods.append({"names": names, "member_id": descriptor.memid,
                                            "invoke_kind": descriptor.invkind,
                                            "argument_types": repr(descriptor.args),
                                            "return_type": repr(descriptor.rettype)})
                    interfaces[name] = methods
                if key == "swconst" and name in ENUMS:
                    values = {}
                    for ordinal in range(info.GetTypeAttr().cVars):
                        descriptor = info.GetVarDesc(ordinal)
                        value_name = info.GetNames(descriptor.memid)[0]
                        if select_value(name, value_name):
                            if type(descriptor.value) is not int:
                                raise TypeError("document unit API enum contains a noninteger")
                            values[value_name] = descriptor.value
                    enums[name] = values
        extension = {row["names"][0] for row in interfaces["IModelDocExtension"]}
        if not {"GetUserPreferenceInteger", "SetUserPreferenceInteger"} <= extension:
            raise RuntimeError("registered API lacks document preference calls")
        return {
            "schema": "kit.sw2026.document-unit-api-metadata.v1",
            "libraries": {key: {"guid": str(value.GetLibAttr()[0]), "major": value.GetLibAttr()[3],
                                "minor": value.GetLibAttr()[4]} for key, value in libraries.items()},
            "interfaces": interfaces,
            "enums": enums,
            "native_processes_started": 0,
            "passed": True,
        }
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    print(json.dumps(metadata(), sort_keys=True))
