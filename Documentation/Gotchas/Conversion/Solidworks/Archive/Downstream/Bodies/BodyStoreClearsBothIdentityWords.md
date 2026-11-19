# Body store clears both cached identity words

The ordinary serializer zeroes the qword at `+0x100`, clearing both `f100` and `f104`. With the selected condition and a valid representative face, it refills `f100` from the actual face. A valid corresponding body supplies the atom at `f104`.

Derive each tail value from the actual retained face and body. The backing atom list and the producing feature value at `f108` have separate producers. [Source record](../../../../../../../re/solidworks/records/DownstreamBodyRepresentative2026.md) · [Source receipt](../../../../../../../re/solidworks/measurements/2026/DownstreamBodyRepresentativeSource01.json)
