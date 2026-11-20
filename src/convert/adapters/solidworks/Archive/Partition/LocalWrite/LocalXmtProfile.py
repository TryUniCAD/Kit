from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes

# local synthesis requires the resident planar kinds with proven generated ownership
KLocalShapes = MappingProxyType(
    {
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
            98,
        )
    }
)

# generated records must stay within the bounds of the current local reader
KLocalLimit = 4096

# local body framing carries its own role outside partition and history data
KLocalDescription = b": TRANSMIT FILE created by modeller version 3701250"
