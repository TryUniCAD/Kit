from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import (
    ReadKernelName,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwAtom import (
    ReadSwAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwAttrs import (
    CheckSwFaceIds,
    ReadSwReals,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwRims import (
    ReadSwRims,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwShell import (
    ReadSwShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwTrim import (
    CheckSwTrims,
    ReadSwTrim,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.CheckSwTorus import (
    CheckSwTorus,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwFrames import (
    ReadSwFrames,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwBrep import (
    ReadSwBrep,
)
from interchange.brep.Topology.BrepModel import BrepModel


# only an independently linked resident solid can supply saved sweep geometry and identity
@DataClass(frozen=True, slots=True)
class SwSavedBody:
    AtomValue: ArchiveNode
    NameValue: str
    ModelValue: BrepModel | None
    ColorValue: tuple[float, ...]
    Translucency: float


# analytic surfaces and actual result ownership must agree before either public read can proceed
def ReadSwResult(
    Archive: SldprtArchive, GraphValue: SwReadGraph, *, IncludeBrep: bool = True
) -> SwSavedBody:
    Active, Deltas = ReadSwFrames(Archive)
    NodesValue = ReadActiveNodes(Active)
    _ = ReadHistMarks(Deltas, NodesValue)
    BodyValue, FacesValue = ReadSwShell(NodesValue)
    FeatureId = NativeNodeId(GraphValue.FeatureValue)
    CreatedAt = DatumTime(GraphValue.LinkValue.ConfigValue.HeaderValue, FeatureId)
    CheckSwFaceIds(NodesValue, FacesValue, FeatureId, CreatedAt)
    Attributes = ReadBodyAttrs(NodesValue, BodyValue)
    AtomValue = ReadSwAtom(GraphValue, NodesValue, Attributes)
    NameValue, ExplicitValue = ReadKernelName(NodesValue, Attributes)
    (Density,) = ReadSwReals(NodesValue, Attributes, "SDL/TYSA_DENSITY", 1)
    ColorValue = ReadSwReals(NodesValue, Attributes, "SDL/TYSA_COLOUR_2", 3)
    (Translucency,) = ReadSwReals(NodesValue, Attributes, "SDL/TYSA_TRANSLUCENCY_2", 1)
    if (
        ExplicitValue is not None
        or AtomValue.FieldsValue.get("f18") is not None
        or AtomValue.FieldsValue.get("f18c") != 1
        or Density <= 0.0
        or Density != RequireScalar(GraphValue.DensityValue.FieldsValue.get("f58"))
        or not all(0.0 <= Value <= 1.0 for Value in (*ColorValue, Translucency))
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep body has a foreign name or physical density owner"
        )
    TorusValue, FirstRim, SecondRim = ReadSwRims(NodesValue, BodyValue, FacesValue)
    CheckSwTorus(GraphValue, TorusValue)
    FirstTrim, SecondTrim = ReadSwTrim(TorusValue, FirstRim), ReadSwTrim(
        TorusValue, SecondRim
    )
    CheckSwTrims(FirstTrim, SecondTrim)
    ModelValue = (
        ReadSwBrep(Active, BodyValue, FacesValue, FirstTrim, SecondTrim)
        if IncludeBrep
        else None
    )
    return SwSavedBody(
        AtomValue,
        NameValue,
        ModelValue,
        ColorValue,
        Translucency,
    )
