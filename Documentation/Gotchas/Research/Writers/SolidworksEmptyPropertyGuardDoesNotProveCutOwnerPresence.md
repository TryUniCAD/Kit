# Empty property policy does not prove cut-owner presence

Passing the existing `CheckEmptyProps` guard does not imply that a concrete cut-list owner exists. Even `RequireCutOwner=True` returns early for the compatible empty root with no keyed rows. Other empty profiles retain a concrete file owner with either a null cut pointer or a concrete empty cut-list object. [Pinned guard](https://github.com/TryUniCAD/Kit/blob/c0a401a607759fb0c2589647c2a22af65ebb7ce1/src/convert/adapters/solidworks/Archive/Properties/CheckEmptyProps.py)

The source-preserving property consumer must check the actual root policy, one key-zero container, file owner and cut-pointer presence. It then checks complete fields, empty lists and object/map identities. A compatible 33-byte root cannot silently stand in for the source's 138-byte advanced owner merely because both have no text values.

The [measured producer/consumer](../../../../re/solidworks/records/EmptyCutPropertyOwner.md) retains the 102-byte file-only golden and generates the distinct 138-byte owner from explicit JSON. Populated or wrong-class owners remain outside the existing empty policy. Native preservation and complete source conversion still require separate evidence.
