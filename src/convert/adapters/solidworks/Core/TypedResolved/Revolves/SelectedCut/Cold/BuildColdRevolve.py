from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdSolid import (
    ColdSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockBody import (
    ColdStockBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.JoinColdGeom import (
    JoinColdGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.BuildRevBodyGeom import (
    BuildRevBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.AnnularNotch import (
    BuildRingNotch,
    StockCentre,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolveOwners import (
    ColdRevOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolvePart import (
    ColdRevolvePart,
)
from interchange.Core.Common import FreezeMapping


# the verified selector changes only its chosen stock and leaves the other full annulus intact
def BuildColdRev(Owners: ColdRevOwners) -> ColdRevolvePart:
    Selected = Owners.SelectedIndex
    Other = Owners.StockValues[1 - Selected]
    OtherId = NativeNodeId(Other.NodeValue)
    Cutter = Owners.CutValue
    CutId = NativeNodeId(Cutter.NodeValue)
    FullStock = BuildRevBody(Other, f"sldprt:body:{OtherId}")
    Volume = FullStock.TopologyValue.volume
    StockArea = FullStock.TopologyValue.surface_area
    Bounds = FullStock.TopologyValue.bounding_box
    if Volume is None or StockArea is None or Bounds is None:
        raise ValueError("untouched revolve stock lacks its complete analytic geometry")
    Untouched = ColdSolid(
        FullStock.BrepValue, Volume, StockArea, Bounds, StockCentre(Other)
    )
    Result = BuildRingNotch(
        Owners.StockValues[Selected], Cutter, f"sldprt:body:{CutId}", Selected
    )
    OtherBody = ColdStockBody(Other.NodeValue, Untouched)
    Bodies = (
        ReplaceValue(
            OtherBody,
            attributes=FreezeMapping(
                {**OtherBody.attributes, "native_atom_id": Owners.AtomIds[1 - Selected]}
            ),
        ),
        ColdStockBody(Cutter.NodeValue, Result),
    )
    Geometry = JoinColdGeom(Untouched, Result, frozenset(Value.id for Value in Bodies))
    Geometry = ReplaceValue(
        Geometry,
        EvidenceValue={
            "method": "typed_parametric_selected_revolve_cut",
            "physical_cache": "absent",
        },
    )
    return ColdRevolvePart(Owners, Geometry, Bodies)
