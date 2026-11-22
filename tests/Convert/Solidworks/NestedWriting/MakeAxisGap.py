from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a complete binary sketch with missing axes must keep its actual two distance owners
def MakeAxisGap(Payload: bytes) -> bytes:
    Archive = SldprtArchive.from_bytes(Payload)
    LinkValue = ReadNativeLink(Archive, 0, RectangleDims=True)
    (Profile,) = (
        Feature
        for Feature in IndexFeatures(LinkValue).values()
        if Feature.ClassValue.NameValue == "moProfileFeature_c"
    )
    SketchValue = RequireNative(Profile.FieldsValue["pd_f80"], "sgSketch")
    FieldsValue = SketchValue.FieldsValue
    DimsValue = NativeRecord(FieldsValue["dims"])
    assert DimsValue["ng2"] == 2 and DimsValue["nlog1"] == 4
    FieldsValue["dims"] = {**DimsValue, "nlog1": 0, "log_g1": ()}
    FieldsValue["lines"] = tuple(
        {**RowValue, "line": {**NativeRecord(RowValue["line"]), "f20": 0}}
        for RowValue in NativeRows(FieldsValue["lines"])
    )
    GraphValue = LinkValue.ResolvedValue
    Resolved, _ = WriteResolMut(
        GraphValue.RootsValue,
        GraphValue.ExtraFields,
        GraphValue.VersionValue,
        LinkValue.ConfigValue.MapValue,
        GraphValue.ContextValue,
        RectangleDims=True,
    )
    return BuildSldprt(dict(Archive.streams) | {LinkValue.StreamName: Resolved})
