# A mate wrapper needs an explicit reference-kind guard

An ordinary planar mate wrapper requires `moCompRefPlane_c` at `f58`.
Declaring that type in `NativeField("Node", "f58", "moCompRefPlane_c")`
does not validate the reached object's runtime class.

The shared Node reader and writer follow the archive object tag. Their
type argument records the intended owner; scalar operations use that
argument for wire decoding. A Node operation can therefore reach another
otherwise admitted class unless its containing grammar checks the kind.
The native general wrapper also has a sketch-handle branch, which the
ordinary plane-only codec does not admit.

The mate grammar checks the actual `f58` class immediately after reading
the object and before continuing the plane-only fields. The same guard
runs when writing. A process negative supplies the inherited assembly as
the wrapper reference and verifies rejection, while the six disclosed
planar streams retain exact bytes and actual occurrence aliases.
[Codec and process evidence](../../../../../../re/solidworks/records/SdkMatesListCodec2026.md)
[Shared Node operation](../../../../../../src/convert/adapters/solidworks/Archive/Bodies/Reading/ReadValueMut.py)
