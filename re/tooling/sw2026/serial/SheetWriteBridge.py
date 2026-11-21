from __future__ import annotations

from Core import ArchiveError
from Schema import Op, run_load
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigLayouts import KConfigLayouts
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigSchemas import KConfigSchemas
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Drawing.Definition.Writing.WriteSheetMut import WriteSheetMut
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


class SheetSdkOwn(Op):
    def __init__(self, original, observations, probe):
        self.original = original
        self.observations = observations
        self.probe = probe

    def load(self, ar, scope, owner):
        run_load(self.original, ar, scope, owner)

    def store(self, ar, scope, owner):
        context = BodyContext(ar.version, KConfigLayouts, {}, KConfigSchemas)
        context.FlagsValue["conditions"] = ar.ctx.get("conditions", 0)
        if self.probe == "archive_version":
            context.VersionValue = 18000
        elif self.probe == "archive_conditions":
            context.FlagsValue["conditions"] = 64
        elif self.probe == "runtime_schema":
            owner.ClassValue = RuntimeClass("moDrSheet", 2)
        elif self.probe == "annotation_presence":
            owner.f["has_f450"] = 1
        elif self.probe == "annotation_marker":
            owner.f["f368_marker"] = 0
        elif self.probe == "ink_view":
            owner.f["ink_views"] = [{"o": owner.f["f390"]}]
        elif self.probe == "missing_presence":
            del owner.f["has_f408"]
        writer = BodyWriter(ar._maps, context, WriteBodyMut)
        before = ar.count
        try:
            WriteSheetMut(writer, owner)
        except BodyUnsupported:
            if writer.OutputValue or ar.count != before:
                raise ArchiveError("unsupported sheet mode changed the output or native map")
            raise
        ar.out.extend(writer.OutputValue)
        self.observations.append({"body_bytes": len(writer.OutputValue), "map_before": before,
                                  "map_after": ar.count, "usage": GetBodyReport(context.UsageValue),
                                  "map_identity_preserved": writer.MapValue is ar._maps})


def install_sheet_writer(registry, observations, probe=None):
    original = registry.classes["moDrSheet"]
    if getattr(original[0], "cls", None) != "moModelFeature_c":
        raise ArchiveError("the drawing sheet base serialization boundary changed")
    registry.classes["moDrSheet"] = [original[0], SheetSdkOwn(original[1:], observations, probe)]
