from hashlib import sha256
from pathlib import Path

from ReferencePacket import EvidenceFailure, digest, require


LIBRARIES = {"sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
             "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}"}
MEMBERS = {
    "IModelDocExtension": ("GetPersistReference3", "GetObjectByPersistReference3", "IsSamePersistentID", "SaveAs3"),
    "ISldWorks": ("IsSame", "ActiveDoc"), "IEntity": ("Select4",), "ISelectData": ("Mark",),
    "ISelectionMgr": ("CreateSelectData", "GetSelectedObject6", "GetSelectedObjectCount2", "GetSelectedObjectType3"),
    "IPartDoc": ("GetBodies2",), "IBody2": ("GetFaces", "GetEdges", "GetVertices"),
    "IFeature": ("GetFaces", "GetTypeName2"), "IFace2": ("GetBody", "GetFeature", "GetSurface", "GetEdges"),
    "IEdge": ("GetStartVertex", "GetEndVertex", "GetTwoAdjacentFaces2", "GetCurve"),
    "IVertex": ("GetPoint", "GetAdjacentFaces"), "ICurve": ("IsLine",), "ISurface": ("IsPlane",),
    "IDimension": ("SetSystemValue3",),
}
ENUMS = {
    "swObjectEquality": ("swObjectSame", "swObjectNotSame", "swObjectUnsupported"),
    "swPersistReferencedObjectStates_e": ("swPersistReferencedObject_Ok", "swPersistReferencedObject_Invalid",
                                          "swPersistReferencedObject_Deleted", "swPersistReferencedObject_Suppressed"),
    "swSelectType_e": ("swSelFACES", "swSelEDGES", "swSelVERTICES"),
    "swBodyType_e": ("swSolidBody", "swSheetBody"),
    "swSetValueInConfiguration_e": ("swSetValue_InThisConfiguration",),
    "swSetValueReturnStatus_e": ("swSetValue_Successful",),
}
MEMBER_KEYS = ("member_id", "invoke_kind", "arguments", "return_type")
MAX_REFERENCE_BYTES = 4096


def normalized(value):
    if isinstance(value, (tuple, list)):
        return [normalized(item) for item in value]
    require(value is None or isinstance(value, (int, str)), "unrecognized registered COM signature field")
    return value


def registered(sw, previous):
    com = sw.pythoncom
    com.CoInitialize()
    try:
        wrapper = sw.wc.gencache.GetModuleForTypelib(com.MakeIID(LIBRARIES["sldworks"]), 0, 34, 0)
        wrapper_sha = digest(Path(wrapper.__file__))
        require(wrapper_sha == previous["wrapper_sha256"], "registered generated SOLIDWORKS wrapper changed")
        proof = {"wrapper_sha256": wrapper_sha, "libraries": {}, "members": {}, "enums": {}}
        for name, guid in LIBRARIES.items():
            library = com.LoadRegTypeLib(guid, 34, 0, 0)
            metadata = library.GetLibAttr()
            require(str(metadata[0]).casefold() == guid.casefold() and metadata[3:5] == (34, 0),
                    "expected the registered SOLIDWORKS 2026 type libraries")
            proof["libraries"][name] = {"guid": str(metadata[0]), "major": metadata[3], "minor": metadata[4], "locale": metadata[1]}
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                owner = info.GetDocumentation(-1)[0]
                if name == "sldworks" and owner in MEMBERS:
                    fields = proof["members"][owner] = {}
                    for ordinal in range(info.GetTypeAttr().cFuncs):
                        item = info.GetFuncDesc(ordinal)
                        names = info.GetNames(item.memid)
                        if names and names[0] in MEMBERS[owner]:
                            sig = (item.memid, item.invkind, normalized(item.args), normalized(item.rettype))
                            fields.setdefault(names[0], []).append(dict(zip(MEMBER_KEYS, sig, strict=True)))
                    require(set(fields) == set(MEMBERS[owner]), "a required native reference member is unregistered: " + owner)
                if name == "swconst" and owner in ENUMS:
                    fields = proof["enums"][owner] = {}
                    for ordinal in range(info.GetTypeAttr().cVars):
                        item = info.GetVarDesc(ordinal)
                        member = info.GetNames(item.memid)[0]
                        if member in ENUMS[owner]:
                            require(type(item.value) is int, "unexpected native reference enum type")
                            fields[member] = item.value
                    require(set(fields) == set(ENUMS[owner]), "a required native reference enum is incomplete: " + owner)
        validate_registration(proof, previous)
        return proof
    finally:
        com.CoUninitialize()


def validate_registration(proof, previous):
    require(proof["members"].keys() == MEMBERS.keys() and proof["enums"].keys() == ENUMS.keys(),
            "the exact registered reference inventory is incomplete")
    for owner, fields in proof["members"].items():
        for member, observed in fields.items():
            prior = [{key: item[key] for key in MEMBER_KEYS} for item in previous["interfaces"].get(owner, {}).get("members", ())
                     if item["names"][0] == member]
            require(not prior or observed == prior, "registered COM signature changed: " + owner + "." + member)
    persistent_compare, = proof["members"]["IModelDocExtension"]["IsSamePersistentID"]
    require(persistent_compare["invoke_kind"] == 1 and persistent_compare["arguments"] == [[12, 1, None]] * 2
            and persistent_compare["return_type"] == [3, 0, None], "unexpected IsSamePersistentID VARIANT input or integer result")
    require(proof["enums"]["swObjectEquality"] == previous["enums"]["swObjectEquality"]
            and proof["enums"]["swPersistReferencedObjectStates_e"]["swPersistReferencedObject_Ok"] == 0,
            "registered reference status meanings changed")


def safe_error(error):
    result = {"exception_type": type(error).__name__}
    if isinstance(error, EvidenceFailure):
        result["reason"] = str(error)
    hresult = getattr(error, "hresult", None)
    if type(hresult) is int:
        result["hresult"] = hresult
    return result


def bounded_reference(raw, row):
    shape = row["reference_transport"] = {"python_type": type(raw).__name__}
    require(raw is not None, "GetPersistReference3 returned null")
    if isinstance(raw, (tuple, list)):
        shape["elements"] = len(raw)
        require(0 < len(raw) <= MAX_REFERENCE_BYTES, "native reference octet count is empty or exceeds the probe bound")
        require(all(type(value) is int and 0 <= value <= 255 for value in raw), "native reference sequence contains non-octets")
        return bytes(raw)
    require(isinstance(raw, (bytes, bytearray, memoryview)), "native reference lacks a supported byte-array transport")
    with memoryview(raw) as view:
        shape.update(bytes=view.nbytes, dimensions=view.ndim, item_size=view.itemsize, format=view.format,
                     c_contiguous=view.c_contiguous)
        require(view.ndim == view.itemsize == 1 and view.c_contiguous and view.format == "B",
                "native reference transport is not a contiguous unsigned-octet vector")
        require(0 < view.nbytes <= MAX_REFERENCE_BYTES, "native reference byte count is empty or exceeds the probe bound")
        return view.tobytes()


class References:
    def __init__(self, author, extension, enums):
        self.sw = author.sw
        self.extension = extension
        self.same = enums["swObjectEquality"]["swObjectSame"]
        self.ok = enums["swPersistReferencedObjectStates_e"]["swPersistReferencedObject_Ok"]

    def encoded(self, token):
        return self.sw.VARIANT(self.sw.pythoncom.VT_ARRAY | self.sw.pythoncom.VT_UI1, list(token))

    def capture(self, selected, row):
        row["stage"] = "capture_reference"
        raw = self.sw.invoke(self.extension, "GetPersistReference3", selected)
        row["stage"] = "decode_reference_transport"
        token = bounded_reference(raw, row)
        row["reference"] = {"bytes": len(token), "sha256": sha256(token).hexdigest()}
        return token

    def native_object(self, original, row):
        row["stage"] = "resolve_baseline_reference"
        row["baseline_reference_sha256"] = sha256(original).hexdigest()
        status = self.sw.byref_long()
        status.value = -(2**31)
        actual = self.sw.invoke(self.extension, "GetObjectByPersistReference3", self.encoded(original), status)
        row["resolver_status"] = int(status.value)
        row["resolver_returned_object"] = actual is not None
        require(row["resolver_status"] == self.ok and actual is not None, "the baseline reference did not resolve cleanly")
        return actual

    def resolve(self, original, current, expected, topology, role, row):
        actual = self.native_object(original, row)
        row["stage"] = "bind_resolved_owner"
        row["resolved_role"] = topology.resolved_role(actual, role[0])
        row["resolved_object_equality"] = topology.compare(actual, expected, role[0])
        row["stage"] = "compare_persistent_ids"
        row["persistent_id_equality"] = self.compare(original, current)
        require(row["resolved_role"] == role[1] and row["resolved_object_equality"] == self.same and
                row["persistent_id_equality"] == self.same, "native reference equality or linked role changed")

    def compare(self, first, second):
        return int(self.sw.invoke(self.extension, "IsSamePersistentID", self.encoded(first), self.encoded(second)))
