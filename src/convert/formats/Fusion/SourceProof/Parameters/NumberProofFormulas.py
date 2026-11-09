# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.FormulaDeps.FormulaGraph import GetFormulaGraph
from convert.formats.Fusion.FormulaDeps.FormulaOrder import GetProvenLinks
from convert.formats.Fusion.SourceProof.Parameters.NumberProofRow import NumberProofRow
from convert.geometry.Formula.FormulaUnits import GetQuantity


# exact linked names and a verified dependency closure protect against cached formula coincidences
def ReadProvenNums(RowValues: tuple[NumberProofRow, ...]) -> tuple[NumberProofRow, ...]:
    Graph = GetFormulaGraph(tuple(RowValue.Raw for RowValue in RowValues))
    Edges: dict[str, tuple[str, ...]] = {}
    for RowValue in RowValues:
        Expression = RowValue.Actual.expression
        Identity = RowValue.Raw.id
        if Expression is None and GetQuantity(RowValue.Raw.value) is not None:
            Edges[Identity] = ()
        elif Expression is not None and Graph.get(Identity) == Expression.parameter_ids:
            Edges[Identity] = Expression.parameter_ids
    Proven = GetProvenLinks(Edges)
    return tuple(
        RowValue
        for RowValue in RowValues
        if Edges.get(RowValue.Raw.id) == () or RowValue.Raw.id in Proven
    )
