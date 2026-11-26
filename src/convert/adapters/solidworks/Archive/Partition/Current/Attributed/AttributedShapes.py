from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.MakeXmtShape import MakeXmtShape

# the attributed solid boundary uses two carrier classes outside the shared grammar
KAttributedShapes = MappingProxyType(
    {
        **{
            KindValue: KKernelShapes[KindValue]
            for KindValue in (
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                29,
                30,
                50,
                70,
                74,
                79,
                80,
                81,
                82,
                83,
                98,
                101,
            )
        },
        133: MakeXmtShape(
            "TRIMMED_CURVE",
            "node_id:d attributes_features:p1019 owner:p1010 next:p1008 previous:p1008 geometric_owner:p141 sense:c basis_curve:p1008 point_1:v point_2:v parm_1:f parm_2:f",
        ),
        141: MakeXmtShape(
            "GEOMETRIC_OWNER",
            "owner:p1003 next:p141 previous:p141 shared_geometry:p1003",
        ),
    }
)


# abstract pointer classes admit only targets witnessed in the attributed boundary
KAttributedTargets = MappingProxyType(
    {
        1001: frozenset((81,)),
        1003: frozenset((30, 133)),
        1006: frozenset((50,)),
        1007: frozenset((14,)),
        1008: frozenset((30, 133)),
        1010: frozenset((12, 16)),
        1011: frozenset((18,)),
        1012: frozenset((74,)),
        1013: frozenset((12,)),
        1015: frozenset((12, 14, 15, 16, 18)),
        1018: frozenset((82, 83, 98)),
        1019: frozenset((81,)),
        1029: frozenset((12,)),
        1040: frozenset((101,)),
    }
)
