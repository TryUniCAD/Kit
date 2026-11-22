from collections import Counter
from io import BytesIO
from os import O_APPEND, O_CREAT, O_RDWR, O_TRUNC, O_WRONLY
from pathlib import Path
import sys

from convert import open_document
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedLayouts import KResolvedLayouts
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.Sweeps.UseSavedSwMut import UseSavedSwMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import BuildSweepPart
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.CheckSwTorus import CheckSwTorus
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwBrep import DecodeBrep, ReadSwBrep
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwFrames import ReadSwFrames
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwTrim import CheckSwTrims
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector

from AuditSavedSweepMain import demand


class LegacyLayoutAccess:
    def __init__(self):
        from convert.adapters.solidworks.Config import RootLayout

        self.path = str(Path(RootLayout.__file__).with_name("RootLayout.json"))
        self.enabled = False
        self.opens = 0

    def allow_open(self, args):
        path, _, flags = args
        if not self.enabled or path != self.path or flags & (O_APPEND | O_CREAT | O_RDWR | O_TRUNC | O_WRONLY):
            return False
        self.opens += 1
        return True

    def read(self, raw):
        self.enabled = True
        try:
            return read(raw, strict=False)
        finally:
            self.enabled = False


def read(raw, full=True, strict=True):
    return open_document(
        BytesIO(raw), source_format=KPartFormatId, strict=strict, include_brep=full,
    )


def read_calls(raw, full):
    codes = {function.__code__: function.__name__ for function in (
        ReadSwFrames, CheckSwTorus, CheckSwTrims, ReadSwBrep, DecodeBrep,
    )}
    counts = Counter()

    def observe(frame, event, arg):
        if event == "call" and frame.f_code in codes:
            counts[codes[frame.f_code]] += 1

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        document = read(raw, full)
    finally:
        sys.setprofile(previous)
    expected = {name: int(full or name not in ("ReadSwBrep", "DecodeBrep"))
                for name in codes.values()}
    observed = {name: counts[name] for name in expected}
    demand(observed == expected and (document.brep is not None) is full,
           f"saved read mode performed unexpected work: {observed}")
    return observed


def malformed_properties(raw, access):
    archive = SldprtArchive.from_bytes(raw)
    result = {}
    for stream in ("docProps/core.xml", "docProps/custom.xml", "docProps/Config-0-Properties.xml"):
        change = BuildSldprt({**archive.streams, stream: b"<properties>"}, FormatVersion=4)
        try:
            read(change)
        except SldprtFormatError as error:
            demand(isinstance(error.__cause__, SyntaxError)
                   and "unsupported SOLIDWORKS saved sweep" in str(error),
                   f"{stream} escaped the saved XML refusal")
        else:
            raise ValueError(f"{stream} reached strict projection")
        previous = access.opens
        partial = access.read(change)
        demand(len(partial.feature_timeline) == 27 and len(partial.bodies) == 1
               and "saved_sweep_result" not in partial.source.attributes,
               f"{stream} changed permissive legacy inventory")
        demand(access.opens == previous + 1, "legacy package layout guard did not exercise the fallback once")
        result[stream] = {"strict_refused": True, "permissive_feature_rows": 27, "permissive_bodies": 1,
                          "legacy_layout_reads": access.opens - previous}
    return result


def context(link, saved=False):
    return MakeResolvedCtx(
        19000, link.ConfigValue.MapValue, MakeLinkContext(link.ConfigValue, link.ManagerValue),
        None, SavedSweep=saved,
    )


def saved_scope(raw):
    from math import pi

    minor, major = 0.008763, 0.052141
    intent = SweepIntent(
        "SweepReviewContext", CircleGeometry(PlaneVector(0.0, 0.0), minor),
        ArcGeometry(PlaneVector(0.0, major), major, -pi / 2, 0.0),
        1019.0, RequirePartPath(r"C:\KitSweepReview\SweepReviewContext.SLDPRT", 1794100000),
    )
    cold = SldprtArchive.from_bytes(BuildSweepPart(intent).BytesValue)
    ordinary = ReadNativeLink(cold, 0, ReadSweeps=True)
    saved = ReadNativeLink(SldprtArchive.from_bytes(raw), 0, SavedSweep=True)
    first = context(ordinary)
    current = context(saved, True)
    UseSavedSwMut(current)
    after = context(ordinary)
    new = ("moFaceRef_c", "moFR_c", "moSketchChain_c", "moPerBodyChooserData_c")
    subjects = ("moAtomFeature_c", "moEndSpec_c", "moFeatureDim_c.FUN_4c833f00", "moProfileData.FUN_4bb2d5c0")
    demand(first.LayoutsValue is after.LayoutsValue is KResolvedLayouts
           and first.SchemasValue is after.SchemasValue
           and first.VirtualValue is after.VirtualValue
           and all(name not in first.LayoutsValue and name in current.LayoutsValue
                   and name not in first.SchemasValue and name in current.SchemasValue for name in new)
           and all(first.LayoutsValue[name] != current.LayoutsValue[name] for name in subjects),
           "saved resolver leaked grammar into an unrelated reader")
    return {"isolated_new_classes": len(new), "isolated_alternate_layouts": len(subjects),
            "ordinary_resolved_map": ordinary.ResolvedValue.MapValue.CounterValue,
            "saved_resolved_map": saved.ResolvedValue.MapValue.CounterValue}


def review_boundaries(raw, access):
    return {
        "geometry_call_counts": {"full": read_calls(raw, True), "design": read_calls(raw, False)},
        "malformed_optional_xml": malformed_properties(raw, access),
        "saved_grammar_scope": saved_scope(raw),
    }
