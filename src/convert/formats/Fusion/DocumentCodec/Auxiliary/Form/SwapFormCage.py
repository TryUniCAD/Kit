from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import CageBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import (
    ConvertCage,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ReadShapes import (
    ReadShapes,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SwapStencil import (
    StencilSwap,
    SwapStencil,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.SwapGridCage import (
    IsFormBody,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def ChangeBody(BodyValue: DocumentBody, Context: StencilSwap) -> DocumentBody:
    History = BodyValue.History
    if not isinstance(History, JournalModel) or not IsFormBody(History.Entities):
        return BodyValue
    Entities = tuple(SwapStencil(Entity, Context) for Entity in History.Entities)
    return ReplaceValue(BodyValue, History=ReplaceValue(History, Entities=Entities))


def ChangeSnap(SnapValue: DocumentSnap, Context: StencilSwap) -> DocumentSnap:
    State = SnapValue.Snapshot
    if not isinstance(State, GeometryState) or not IsFormBody(State.Entities):
        return SnapValue
    Entities = tuple(SwapStencil(Entity, Context) for Entity in State.Entities)
    return ReplaceValue(SnapValue, Snapshot=ReplaceValue(State, Entities=Entities))


def EdgeClasses(Surface: TsplineSurface) -> list[str]:
    return [EdgeValue.Convexity for EdgeValue in CageBody(Surface).Edges]


def CheckClasses(Prior: TsplineSurface, Surface: TsplineSurface) -> None:
    if EdgeClasses(Prior) != EdgeClasses(Surface):
        raise ValueError("Fusion Form cage swap would change a crease edge class")


def SwapFormCage(Model: DocumentModel, Surface: TsplineSurface) -> DocumentModel:
    if len(Model.Forms) != 1:
        raise ValueError("Fusion Form cage swap needs exactly one Form")
    Prior, Result = ConvertCage(Model.Forms[0].Surface), ConvertCage(Surface)
    if Prior.LayoutKey != Result.LayoutKey:
        raise ValueError("Fusion Form cage swap needs the same cage layout")
    if Result.LayoutKey in ReadShapes():
        CheckClasses(Model.Forms[0].Surface, Surface)
    if not any(
        isinstance(BodyValue.History, JournalModel)
        and IsFormBody(BodyValue.History.Entities)
        for BodyValue in Model.Bodies
    ):
        raise ValueError("Fusion Form cage swap found no converted Form body")
    Context = StencilSwap(Prior, Result, Surface)
    Bodies = tuple(ChangeBody(BodyValue, Context) for BodyValue in Model.Bodies)
    Snaps = tuple(ChangeSnap(SnapValue, Context) for SnapValue in Model.Snapshots)
    Forms = (ReplaceValue(Model.Forms[0], Surface=Surface),)
    return ReplaceValue(
        Model, Bodies=Bodies, Snapshots=Snaps, Forms=Forms, Graphics=None
    )
