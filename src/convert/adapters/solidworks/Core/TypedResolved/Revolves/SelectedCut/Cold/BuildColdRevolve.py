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
    BuildAnnularNotch,
    StockCentre,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolveOwners import (
    ColdRevolveOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolvePart import (
    ColdRevolvePart,
)
from interchange.Core.Common import FreezeMapping


# the verified selector changes only its chosen stock and leaves the other full annulus intact
def BuildColdRevolve(Owners: ColdRevolveOwners) -> ColdRevolvePart:
    Selected = Owners.SelectedIndex
    Other = Owners.StockValues[1 - Selected]
    OtherId = NativeNodeId(Other.NodeValue)
    Cut = Owners.CutValue
    CutId = NativeNodeId(Cut.NodeValue)
    Full = BuildRevBody(Other, f"sldprt:body:{OtherId}")
    Volume = Full.TopologyValue.volume
    Area = Full.TopologyValue.surface_area
    Bounds = Full.TopologyValue.bounding_box
    if Volume is None or Area is None or Bounds is None:
        raise ValueError("untouched revolve stock lacks its complete analytic geometry")
    Untouched = ColdSolid(Full.BrepValue, Volume, Area, Bounds, StockCentre(Other))
    Result = BuildAnnularNotch(
        Owners.StockValues[Selected], Cut, f"sldprt:body:{CutId}", Selected
    )
    Body = ColdStockBody(Other.NodeValue, Untouched)
    Bodies = (
        ReplaceValue(
            Body,
            attributes=FreezeMapping(
                {**Body.attributes, "native_atom_id": Owners.AtomIds[1 - Selected]}
            ),
        ),
        ColdStockBody(Cut.NodeValue, Result),
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
