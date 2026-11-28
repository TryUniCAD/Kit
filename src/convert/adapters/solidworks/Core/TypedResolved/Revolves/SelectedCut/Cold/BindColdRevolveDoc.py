from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.BindSelectedRevolves import (
    BindSelRevCut,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolveOwners import (
    ColdRevOwners,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# cold ownership records the selected stock without assigning a native result atom before a rebuild
def BindColdRevDoc(Document: CadDocument, Owners: ColdRevOwners) -> CadDocument:
    Stocks = Owners.StockValues
    Cutter = Owners.CutValue
    Selected = Owners.SelectedIndex
    LinkValue = Owners.LinkValue
    Bound = BindSelRevCut(Document, LinkValue, Stocks, Cutter, Selected)
    return ReplaceValue(
        Bound,
        metadata=FreezeMapping(
            {
                **Bound.metadata,
                "solidworks.typed_revolve_cut": {
                    "status": "projected_cold_selection",
                    "stock_feature_ids": tuple(
                        NativeNodeId(Stock.NodeValue) for Stock in Stocks
                    ),
                    "selected_producer_id": NativeNodeId(Stocks[Selected].NodeValue),
                    "consumer_feature_id": NativeNodeId(Cutter.NodeValue),
                    "consumed_atom_id": Owners.AtomIds[Selected],
                    "untouched_atom_id": Owners.AtomIds[1 - Selected],
                    "selector_owner": NativeNodeSpan(LinkValue, Owners.WrapperValue),
                    "public_writer_qualified": False,
                },
            }
        ),
    )
