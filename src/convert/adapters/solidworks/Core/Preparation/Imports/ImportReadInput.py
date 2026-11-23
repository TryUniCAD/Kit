from dataclasses import replace as ReplaceValue
from typing import TypeVar

from convert.adapters.solidworks.Core.Preparation.Imports.IsImportRead import (
    IsImportRead,
)
from interchange.brep.Curves.BrepCurves import BrepEntity
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource

# each regenerated cell retains its concrete geometry type
CellType = TypeVar("CellType", bound=BrepEntity)


# derived source annotations are verified after generation and never supply kernel fields
def BareReadCells(
    Values: tuple[CellType, ...],
) -> tuple[CellType, ...]:
    return tuple(
        ReplaceValue(Value, provenance=None, attributes=FreezeMapping())
        for Value in Values
    )


# reconstructed carriers and incidence are the only geometry inputs to the local transmit
def BareReadBrep(ModelValue: BrepModel) -> BrepModel:
    return ReplaceValue(
        ModelValue,
        curves=BareReadCells(ModelValue.curves),
        surfaces=BareReadCells(ModelValue.surfaces),
        vertices=BareReadCells(ModelValue.vertices),
        edges=BareReadCells(ModelValue.edges),
        coedges=BareReadCells(ModelValue.coedges),
        loops=BareReadCells(ModelValue.loops),
        faces=BareReadCells(ModelValue.faces),
        face_uses=BareReadCells(ModelValue.face_uses),
        shells=BareReadCells(ModelValue.shells),
        shell_uses=BareReadCells(ModelValue.shell_uses),
        regions=BareReadCells(ModelValue.regions),
        bodies=tuple(
            ReplaceValue(Value, design_body_id="")
            for Value in BareReadCells(ModelValue.bodies)
        ),
    )


# the measured output comparison confirms the complete source regenerated from geometry
def ImportReadInput(DocumentValue: CadDocument) -> CadDocument:
    if not IsImportRead(DocumentValue):
        return DocumentValue
    ModelValue = DocumentValue.brep
    if ModelValue is None or len(DocumentValue.configurations) != 1:
        raise ValueError(
            "local import readback requires one complete solid and configuration"
        )
    (ConfigValue,) = DocumentValue.configurations
    return CadDocument(
        CadSource("kit.neutral", "", ""),
        (Configuration(ConfigValue.id, ConfigValue.name, ConfigValue.active),),
        (),
        (),
        (),
        (),
        (),
        (),
        brep=BareReadBrep(ModelValue),
        units=DocumentValue.units,
        schema_version=DocumentValue.schema_version,
    )
