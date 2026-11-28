from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import (
    CheckCutWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import (
    ReadStockAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockOps import (
    ReadStockOps,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import (
    ReadStockRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import (
    ReadCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.CheckColdAtom import (
    CheckColdAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


@dataclass(frozen=True, slots=True)
class ColdStockOwners:
    LinkValue: NativeLink
    OwnerValues: tuple[ExtrudeOwner, ExtrudeOwner, ExtrudeOwner]
    ProfileFrames: tuple[Transform, Transform, Transform]
    SelectedIndex: int
    SelectedAtomId: int
    StockAtoms: tuple[ArchiveNode, ArchiveNode]
    WrapperValue: ArchiveNode


def check_unrealized(owners):
    for index, owner in enumerate(owners):
        fields = owner.NodeValue.FieldsValue
        absent = ("f4a8", "f4b0", "f4c0", "f530")
        if index == 2:
            absent += ("f528",)
        if (
            any(fields.get("has_" + key) != 0 or fields.get(key) is not None for key in absent)
            or fields.get("f538") is not None
            or owner.EndValue.FieldsValue.get("f158") != 0
        ):
            raise ValueError("pre-rebuild solid has a result, consumed atom or chooser owner")
    cut = owners[2].NodeValue.FieldsValue
    if cut.get("n494") != 0 or NativeRows(cut.get("f498")):
        raise ValueError("pre-rebuild cut has a result identity")


def read_managed_stocks(link, stocks):
    atoms = tuple(ReadStockAtom(owner.NodeValue, False) for owner in stocks)
    if len(set(atoms)) != 2 or set(atoms) != ReadCutAtoms(link):
        raise ValueError("provisional stocks must be the two actual manager atoms")
    manager = NativeRecord(link.ConfigValue.RootValue.FieldsValue.get("fd88"))
    assigned = tuple(row.get("o") for row in NativeRows(manager.get("atoms")))
    ids = tuple(
        ReadCutAtomId(atom, owner.NodeValue)
        for atom, owner in zip(atoms, stocks, strict=True)
    )
    if (
        assigned != atoms or manager.get("fa8") != 0
        or ids[1] != ids[0] + 1 or manager.get("f260") != ids[1]
    ):
        raise ValueError("provisional stock atoms disagree with their manager allocation")
    for atom in atoms:
        CheckColdAtom(atom, ImplicitName=True)
    return atoms, ids


def read_selection(link, owners, ids):
    first, second, cut = owners
    root = link.ConfigValue.RootValue
    fields = cut.NodeValue.FieldsValue
    if fields.get("f544") != 1 or fields.get("has_f548") != 1:
        raise ValueError("pre-rebuild through cut requires one explicit stock selection")
    wrapper = ReadSingleNode(fields.get("f548"), "moCompSolidBody_c")
    producer_id = wrapper.FieldsValue.get("f108")
    matches = tuple(
        index for index, stock in enumerate((first, second))
        if type(producer_id) is int and producer_id == NativeNodeId(stock.NodeValue)
    )
    if len(matches) != 1:
        raise ValueError("cut selector does not identify an actual earlier stock producer")
    (index,) = matches
    CheckCutWrapper(root, owners[index].NodeValue, cut.NodeValue, ids[index], IsCold=True)
    component = RequireNative(wrapper.FieldsValue.get("f58"), "moUnitComponent_c")
    CheckTreeAlias(link, (wrapper, component))
    return index, wrapper


def check_depth(link, owner):
    depth = owner.RequireDepth()
    dimension, parameter, value = ReadPrismParam(depth.DisplayValue, False)
    if (
        depth.DepthValue.name != "D1"
        or owner.EndValue.FieldsValue.get("f18") is not depth.DisplayValue
        or depth.DisplayValue.FieldsValue.get("n850") != 1
        or (dimension, parameter, value)
        != (depth.Dimension, depth.Parameter, depth.DepthValue.native_value)
    ):
        raise ValueError("blind stock lacks its actual typed D1")
    name = RequireNative(parameter.FieldsValue.get("f18"), "moNodeName_c")
    CheckTreeAlias(link, (depth.DisplayValue, depth.HandleValue, dimension, parameter, name))


def read_support(link, owner, features):
    profile = owner.ProfileValue
    frame = ReadPrismFrame(profile, link.ConfigValue.RootValue, features, FrontOnly=False)
    reference = RequireNative(profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
    target_id = NativeRecord(reference.FieldsValue.get("ff0"))["f00"]
    datum = RequireNative(features[target_id], "moRefPlane_c")
    component = RequireNative(reference.FieldsValue.get("f58"), "moUnitComponent_c")
    sketch = RequireNative(profile.FieldsValue.get("pd_f80"), "sgSketch")
    CheckTreeAlias(link, (reference, datum, component, sketch))
    return frame, datum


def read_frames(link, owners, features, selected):
    frames, datums = zip(
        *(read_support(link, owner, features) for owner in owners), strict=True
    )
    zero = SpaceVector(0.0, 0.0, 0.0)
    x_axis = SpaceVector(1.0, 0.0, 0.0)
    y_axis = SpaceVector(0.0, 1.0, 0.0)
    z_axis = SpaceVector(0.0, 0.0, 1.0)
    expected = (
        Transform(zero, x_axis, y_axis, z_axis),
        Transform(zero, SpaceVector(0.0, 0.0, -1.0), y_axis, x_axis),
    )
    if frames[:2] != expected or datums[2] is not datums[selected] or frames[2] != frames[selected]:
        raise ValueError("cut and selected stock do not share their exact signed datum")
    return frames


def decode_cold_stock_owners(link: NativeLink) -> ColdStockOwners:
    if link.ResolvedValue.ExtraFields is not None:
        raise ValueError("provisional two-stock ownership excludes a resolved body map")
    root = RequireNative(link.ConfigValue.RootValue, "moPart_c")
    features = ReadStockRoots(link)
    owners = ReadStockOps(link, features)
    check_unrealized(owners)
    atoms, ids = read_managed_stocks(link, owners[:2])
    selected, wrapper = read_selection(link, owners, ids)
    for stock in owners[:2]:
        check_depth(link, stock)
    frames = read_frames(link, owners, features, selected)
    CheckTreeAlias(link, (
        root, *atoms, *(owner.NodeValue for owner in owners),
        *(owner.ProfileValue for owner in owners), *(owner.EndValue for owner in owners),
    ))
    return ColdStockOwners(link, owners, frames, selected, ids[selected], atoms, wrapper)


def read_cold_stock_owners(archive: SldprtArchive) -> ColdStockOwners:
    if any("Partition" in name or "LocalBodies" in name for name in archive.streams):
        raise ValueError("provisional two-stock ownership excludes stored body caches")
    return decode_cold_stock_owners(ReadNativeLink(archive, 0))
