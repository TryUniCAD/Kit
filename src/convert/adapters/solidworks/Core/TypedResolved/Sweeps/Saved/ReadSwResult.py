from dataclasses import dataclass as DataClass

from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import (
    decode_brep_model as DecodeBrep,
)
from convert.adapters.solidworks.Core.Partition.CircularPartition import ReadShellAtom
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import (
    ReadKernelName,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.BindSwTrims import (
    BindSwTrims,
    SwNativeId,
)
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
from interchange.brep.Topology.BrepModel import BrepModel


# only an independently linked resident solid can supply saved sweep geometry and identity
@DataClass(frozen=True, slots=True)
class SwSavedBody:
    AtomValue: ArchiveNode
    NameValue: str
    ModelValue: BrepModel
    ColorValue: tuple[float, ...]
    Translucency: float


# active and delta frames must completely occupy the actual configuration partition stream
def ReadSwFrames(Archive: SldprtArchive) -> tuple[bytes, bytes]:
    RawValue = Archive.require(KPartitionStream)
    Active, Deltas = DecodePartData(RawValue, KPartitionStream)
    if (
        Active.wrapper_offset != 0
        or Deltas.wrapper_offset != Active.stored_size
        or Active.stored_size + Deltas.stored_size != len(RawValue)
    ):
        raise ValueError("SOLIDWORKS saved sweep has alternate result framing")
    return Active.data, Deltas.data


# stored surface values must be the exact current metre drivers in their signed principal placement
def CheckSwTorus(GraphValue: SwReadGraph, TorusValue: XmtNode) -> None:
    MajorValue, MinorValue = (
        GraphValue.PathValue.CurveValue.Radius,
        GraphValue.SectionValue.CurveValue.Radius,
    )
    if (
        not 0.0 < MinorValue < MajorValue
        or TorusValue.FieldsValue["major_radius"] != MajorValue
        or TorusValue.FieldsValue["minor_radius"] != MinorValue
        or TorusValue.String("sense") != "+"
        or ReadXmtVector(TorusValue, "centre") != (0.0, MajorValue, 0.0)
        or ReadXmtVector(TorusValue, "axis") != (0.0, 0.0, 1.0)
        or ReadXmtVector(TorusValue, "x_axis") != (1.0, 0.0, 0.0)
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep torus disagrees with its actual live drivers"
        )


# analytic surfaces and actual result ownership must agree before either public read can proceed
def ReadSwResult(Archive: SldprtArchive, GraphValue: SwReadGraph) -> SwSavedBody:
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
    ModelValue = DecodeBrep(Active)
    if ModelValue is None:
        raise ValueError("SOLIDWORKS saved sweep lacks its complete analytic result")
    CheckSwModel(Active, ModelValue, BodyValue, FacesValue)
    return SwSavedBody(
        AtomValue,
        NameValue,
        BindSwTrims(ModelValue, FirstTrim, SecondTrim),
        ColorValue,
        Translucency,
    )


# shared analytic decoding must return exactly the solid and faces verified in the physical graph
def CheckSwModel(
    Active: bytes,
    ModelValue: BrepModel,
    BodyValue: XmtNode,
    FacesValue: tuple[XmtNode, ...],
) -> None:
    OwnerValue = ReadShellAtom(Active, ModelValue)
    if (
        len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 1
        or len(ModelValue.shells) != 1
        or len(ModelValue.vertices) != 2
        or not ModelValue.regions[0].solid
        or not ModelValue.shells[0].closed
        or OwnerValue.get("native_owner") != BodyValue.IndexValue + 1
        or OwnerValue.get("native_shell") != BodyValue.Integer("shell") + 1
        or tuple(Value.id for Value in ModelValue.faces)
        != tuple(SwNativeId("face", Value) for Value in FacesValue)
        or ModelValue.validate()
    ):
        raise ValueError("SOLIDWORKS saved sweep analytic result has foreign topology")
