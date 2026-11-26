# Archive class descriptors require nonempty names

A zero-length ASCII name is decodable as text. It is an invalid class
descriptor under the legacy archive reader. A nested object can bypass
the enclosing stream's root class check.

Reject a zero name length in the [descriptor reader](../../../../../src/convert/adapters/solidworks/Archive/Reading/ReadTypeDescMut.py)
before allocating the class slot. The [nested descriptor control](../../../../../tests/Convert/Solidworks/ArchiveGraph/GraphRejectTests.py)
keeps the linked stream's root descriptor valid.
