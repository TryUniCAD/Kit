# Principal-plane boss revolve source lock

Five fresh SOLIDWORKS 2026 SP05.2 parts passed native authoring, rebuild
and fresh reopen. The two independent Top and Right inputs also passed
driving-angle edits and remain sealed with their authored specifications.
Both controls passed across twelve distinct SOLIDWORKS processes. The
lock predates the SDK Top and Right preparation extension and contains zero writer
outputs. [Source lock](../v2026/heldout/PrincipalRevolveSourceLock01.json)

| Item | Boundary |
| --- | --- |
| Task | B04-SW2026-REVOLVE-PRINCIPAL |
| Owner and native oracle custodian | PR #121 takeover |
| Delivery | [PR #121](https://github.com/TryUniCAD/Kit/pull/121) |
| Authoring revision | `954e5773df5088df4995701ea684f98ecb1dcac1` |
| Production source tree at lock | `f6830bfd53fc99747c91ca4a3cd7eead3915d6ee` |
| Oracle | SOLIDWORKS 2026 SP05.2, `34.5.2.0604`, COM `SldWorks.Application.34` |
| Lock SHA-256 | `ac1a3c15db459409ab3a7aacf1281feba1c714bae8e6c8b8d7ae5d04930ab722` |
| Exit | Preserve the actual selected axis, support, direction, driving angle, tree and geometry through saved native rebuild and fresh reopen |

The disclosed controls comprise a Front full turn and a Top
partial-turn direction pair. The sealed inputs change the radius,
axial range, selected axis placement and angular end independently
on Top and Right. The guest-native specification file remains
under the private job directory. Only its digest, the source file
hashes and the phase receipt digests were carried back. The pinned
older Front full-turn control brackets the authoring and reopen
phases. [Existing native author](../../tooling/sw2026/AuthorRevolveSources.py)

The present SDK admission binds `RevolvePlan.AxisValue` and the
profile to Front. It checks the selected axis in the Front model
frame and writes its world-origin and direction cache in
`moLineRef_w.fc8/fe0`. Measure those owners on the disclosed
Top pair and at least one independent disclosed Right control
before extending the shared frame transform. Freeze implementation
and the comparisons before releasing either sealed case.
[Axis cache evidence](../../../Documentation/Gotchas/Conversion/Solidworks/Model/RevolveAxisCacheUsesModelCoordinates.md)

The preparation helper must run in the same Windows guest as the
native author. Set the tool paths to the pinned copies on the Mac
share and choose an unused private guest directory. The preparation
prints the exact native job locator and digests.

```sh
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$guest_prepare" \
  --workspace "$private_workspace" --checkout "$guest_checkout" \
  --control "$guest_control" --source-revision "$source_revision"
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$guest_author" "$guest_job"
```

The first capture used job SHA-256
`2a5528e57cbf9f65cfa4aea68626fe0a6bb2052f28c154867230b571d663056c`
and private specification SHA-256
`13be8abb8186c7a876637ea27e93c0b35083c0ea34cbf4b052d3b8988a81e457`.
[Preparation tool](../../tooling/sw2026/revolve/LockedEvaluation/PreparePrincipalRevolveLock.py)
