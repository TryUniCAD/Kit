# Public typed assembly anchor preservation

Task B04-SW2026-MATES, owner `/root/assembly_occurrence`, delivery PR #121.
This bounded read change preserves the actual fixed occurrence for completely
admitted ordinary typed planar-mate graphs. It depends on the existing linked
Config/Resolved/MatesList reader and selected child configurations. It adds no
write registration, part preparation or CAD runtime dependency.

The [native ordered lifecycle](../measurements/2026/SdkOrderedAssemblyNative01.json)
proves one fixed first occurrence and one floating second occurrence, before
and after a rotated live distance edit and fresh reopen. The initial normal
public reads recovered both configurations, child D1, all three ordered mates,
six plane endpoints and placements, but returned `fixed=False` for both
instances. `Core/Adapter.py::AsmInstances` supplied that literal legacy default.
The original input and native-saved sibling both show the mismatch.

The native field rule is independently established in
[PlanarMateWrapperWriteState2026.md](PlanarMateWrapperWriteState2026.md#fixed-occurrence):
`moReference_c.f408` is the serialized Boolean fixed flag. `f400` is separate
solver state. The loader normalizes the fixed word to a Boolean. Neither solver
status nor mate participation supplies the authored anchor state.

[ReadFixedFlags.py](../../../src/convert/adapters/solidworks/Core/TypedMates/ReadFixedFlags.py)
reads that flag from the actual linked model's complete direct reference list.
Feature IDs must be unique and match the actual native occurrence index, names
must match the actual occurrence and reference number, and
[IsAnchorFixed.py](../../../src/convert/adapters/solidworks/Core/TypedMates/IsAnchorFixed.py)
checks the actual external-feature backlink and its persistent ID. A decoded
lightweight reference need not retain the constructor's runtime `owner` pointer;
body membership and serialized backlink establish this wire relationship.
[Runtime-owner distinction](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/FeatureOwnersAreNotMateWireFields.md)

The complete typed mate report retains the derived flags and native feature
IDs. [WithTypedFixed.py](../../../src/convert/adapters/solidworks/Core/TypedMates/WithTypedFixed.py)
replaces only the corresponding instance's `fixed` property after full typed
admission. Missing or ambiguous IDs and non-Boolean flags fail closed. Deferred
and unsupported typed reads retain their original instances and legacy behavior.
The shared adapter delta is one import and one call after `WithTypedMates`.

## Verification and limits

[ReadSdkOrderedNative.py](../../tooling/sw2026/ReadSdkOrderedNative.py) performs
ordinary `open_document` reads in separate isolated processes. It checks the
original frozen parent and its actual native-saved sibling against the prior
independent prediction, validates each returned document and requires an empty
COM import set. Both read back the actual shared child, active configuration
names, 18.625 mm child D1, exact occurrence names and fixed flags `[true, false]`,
full typed three-mate graph, six ordered child plane identities and independent
rotated placements. The distance changes from 47.35 to 63.21 mm. Every input
hash remains unchanged.

The [public receipt](../measurements/2026/SdkOrderedAssemblyPublicReadback01.json)
pins the actual reader source snapshot, helper and two worker outputs. The
earlier flags mismatch and the intermediate ownership-check rejection remain
private discovery records rather than passing read evidence.

The permanent [process integration](../../../tests/Convert/Solidworks/Research/Assembly/TypedMates/FixedFlagTests.py)
constructs two unrelated generated ordered pairs with opposite authored anchors,
writes actual files and reads them through the normal public SDK in fresh
processes. Both preserve the requested flags, all three mates and six entities.
Deferred component resolution retains its existing strict rejection. The
integration passes with six worker invocations. Black, Ruff, strict Mypy,
Pyright and steering checks pass for the six new or directly changed focused
source/test files. The
[known formatter exclusion](../../../Documentation/Gotchas/Ci/Commands/BlackExcludesFeaturePaths.md)
also matches `Core/`; verification explicitly includes those owned files.

This qualifies the stated public read projection and disclosed SDK lifecycle.
Original native held-out mate conversion and public assembly writing remain
separate acceptance gates. No hidden source or observation informed this fix.
