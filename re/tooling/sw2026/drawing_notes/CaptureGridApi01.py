import json
import pythoncom
from pathlib import Path

names = {
    "IModelDoc2": {"GetGridSettings", "SetGridSettings", "GetDisplayWhenAdded", "SetDisplayWhenAdded"},
    "IModelDocExtension": {"GetUserPreferenceToggle", "SetUserPreferenceToggle", "ViewZoomToSheet"},
    "IAnnotation": {"Visible", "GetDisplayData"},
    "INote": {"GetExtent"},
    "IView": {"GetVisible"},
}

def main():
    pythoncom.CoInitialize()
    try:
        rows, enums = {}, {}
        for dll, guid in (
            ("sldworks", "{83A33D31-27C5-11CE-BFD4-00400513BB57}"),
            ("swconst", "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}"),
        ):
            lib=pythoncom.LoadRegTypeLib(guid,34,0,0)
            assert tuple(lib.GetLibAttr()[3:5])==(34,0)
            for index in range(lib.GetTypeInfoCount()):
                info=lib.GetTypeInfo(index)
                name=info.GetDocumentation(-1)[0]
                if dll=="sldworks" and name in names:
                    rows[name]={}
                    for ordinal in range(info.GetTypeAttr().cFuncs):
                        desc=info.GetFuncDesc(ordinal)
                        method=info.GetNames(desc.memid)[0]
                        if method in names[name]:
                            rows[name].setdefault(method,[]).append({
                                "member_id":desc.memid,"arguments":repr(desc.args),"return":repr(desc.rettype),
                                "invoke_kind":desc.invkind,"vt_offset":desc.oVft,
                            })
                if dll=="swconst" and name in {"swUserPreferenceToggle_e","swUserPreferenceOption_e"}:
                    enums[name]={}
                    for ordinal in range(info.GetTypeAttr().cVars):
                        desc=info.GetVarDesc(ordinal)
                        member=info.GetNames(desc.memid)[0]
                        lower=member.lower()
                        if member=="swDetailingNoOptionSpecified" or "grid" in lower or "annotation" in lower:
                            enums[name][member]=desc.value
        result={"interfaces":rows,"enums":enums,"version":[34,0],"cad_processes_started":0}
        with Path(__file__).with_name("GridApi01.json").open("x",encoding="utf-8") as f:
            json.dump(result,f,sort_keys=True,indent=2)
        print(json.dumps({"interfaces":len(rows),"enum_members":sum(len(v) for v in enums.values()),"cad_processes_started":0}))
    finally:
        pythoncom.CoUninitialize()

if __name__=="__main__":
    main()
