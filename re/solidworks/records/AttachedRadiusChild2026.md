# Attached radius child readback

Task `B04-SW2026-MATES-CONCENTRIC/attached-radius-child` is owned by the
PR #121 takeover team. The scoped SDK work starts at #239
`8d98c4e347c5ee1cfdbeae52a09eb243517540b7`. Standalone native child
publication and the concentric assembly writer remain separate delivery
gates.

## Evidence boundary

The exact [native assembly observation](https://github.com/TryUniCAD/Kit/blob/67d2ac3ca36d1d714636a2eab14a4b6129647f68/re/solidworks/measurements/2026/ConcentricRadialAssemblyNative01.json)
used SOLIDWORKS `34.5.2.0604` and four distinct processes, including the
passing initial and trailing controls. It resolved the child in the
assembly via `GetModelDoc2`, rebuilt it, edited its blind height and saved
it. The subsequent fresh parent open resolved the saved child. The
standalone radial source observation
`ConcentricRadialSceneNative01.json` concerns a different candidate with
no attached partition. Its open status does not attest these child bytes.

| State | Exact file SHA-256 | Selected and activation marks | Typed active nodes |
| --- | --- | --- | --- |
| Generated child | `699be1addf4b644f1ebdeecc6862f65610155d294e10fa6d7cbcf3d6a224f1cd` | `4, 2` | 72 |
| Saved child after the height edit | `d39693d2617c0900a607fb7e6e5be041b7caea906ebcd0cecc69fb8d767a7416` | `10, 2` | 92 |

The actual `sgSketch` arc, fixed centre and radius driver lead to the
Front datum. The ordinary forward boss owns the active `f818.f18` driver.
The independent `f818.f20` value stays inactive. After saving, the
`f4a8` and `f4c0` cache objects own the two paired cap representatives
and share the live arc mark. They point back to the same producer and
the stored self-file identity in this configuration. Their cached prior
cylinder bounds agree with the inactive length. The two drivers retain
their exact binary64 values independently of rounded keywords.

The complete typed configuration and resolved graph must agree on the
unique visible `moAtom_c`, real output ID and feature. Its physical
ownership resolves through the live world and three-face analytic solid.
The selected and activation marks agree with the rollback frame.
`BODY_MATCH`, `ENT_TIME_STAMP_2001`, `ATOM_ID_2001` and
`LAST_BODY_MODIFYING_FEATURE_ID` link the actual configuration, header
and boss. The unique Unicode `SWIMPLICITBODYNAME_ID_U` gives the body name.
These values originate in the typed input owners when reading. The
identifiers and stamps in the receipt are observations.

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/CheckAttachRadiusRead.py \
  --packet /absolute/disclosed/RadialConcentric01 \
  --output /tmp/UnusedAttachedRadiusRead.json
```

The supervisor binds the two exact child files to the native terminal
result, job identity and independent geometric prediction. Each strict
SDK reader is a fresh process and checks both geometry and design-only
mode. It forbids file, process, network and native library access after
the SDK imports and codec loading. Additional checks re-emit three
typed streams per phase and verify unchanged decoded physical geometry.
The transient typed negative contrasts reject changed atoms, marks,
choices and the inactive partition before the new association is returned.
[Guarded receipt](../measurements/2026/AttachedRadiusChildRead01.json)

The two cases reproduce the original 7.19 mm radius and original and
edited blind heights of 31.37 and approximately 36.79701 mm. Their native
and independently calculated area, volume and centroid agree to six
significant figures. The exact presentation remains partial. The
ordinary SDK timeline has 19 and 27 entries respectively and the native
observed tree lists 25 in each state. This verifies the editable circle,
boss and linked physical solid. It gives zero held-out credit and does
not establish an independently loadable standalone child or full scene
round-trip.

## Model-only generation

The [compiler comparison](../measurements/2026/AttachedRadiusChildBuild01.json)
constructs the same child twice through the exact #239 SDK source and
shared typed `EncodePartXmt` at `8a0043cb85affcf39660007383abcadd38a0b13e`.
The isolated topology producer at
`787a836b6aecdbb726dc86078e79977aafdefc78` computes its 72 active nodes
and rollback from the disclosed neutral request. Both workers prohibit
external accesses after imports and explicit input transfer. The SDK
worker computes the file and configuration state from that plan, the
actual owning feature and atom, its explicit save event and the four
typed authored lights. Whole bytes and all eleven logical stream digests
agree with the earlier construction. Strict SDK readback also agrees
with the neutral input owners and independent analytic body metrics.

```sh
python3.14 -I -B re/tooling/sw2026/VerifyAttachedRadiusBuild.py \
  --intent /absolute/disclosed/IndependentRequest.json \
  --packet /absolute/disclosed/RadialConcentric01 \
  --output /tmp/UnusedAttachedRadiusBuild.json
```

The handoff requires the three explicitly pinned local Git objects and
the disclosed semantic input. The research supervisor exports source
code into temporary directories and validates the control receipt and
locator provenance before worker execution. It opens no saved CAD input.
The runtime compressor observed here was zlib `1.2.12`. Whole file digests
remain platform and locator specific.

The same command with `--trial-locator` and a fresh external
`--candidate-dir` produces a separately pinned standalone discriminator.
The [prospective build receipt](../measurements/2026/AttachedRadiusStandaloneBuild01.json)
records the exact different file. Only `Header2` and
`Contents/Config-0-ModelHeader` differ in logical stream bytes. The
[prospective observation plan](../authoring/AttachedRadiusStandalonePlan01.json)
declares the original recursive tree, the actual radius and depth
drivers and the independent `34.125 mm` blind edit. The identical
geometry and parameter checks apply after fresh native reopen.

## Standalone observation and control failure

The exact 10,863-byte standalone candidate opened, rebuilt, accepted the
34.125 mm blind edit, saved and reopened in independent SOLIDWORKS 2026
SP05.2 processes. The initial and edited trees each had 25 ordered entries.
The one solid retained its three faces, 7.19 mm radius, and two live drivers.
The initial control passed. The trailing control lost its COM interface at
`Parameter` after 20 numerical comparisons. This batch grants zero
native qualification.

The unchanged candidate was queued again with a local copy of the control.
Both retry controls failed during COM activation and the candidate never
launched. A separate, previously healthy ordinary revolve failed during
activation with the same COM error. The qualification remains pending.
[Standalone observation and control receipt](../measurements/2026/AttachedRadiusStandaloneControlBoundary01.json)

The remaining delivery work is the standalone native lifecycle at that
locator and the runtime neutral topology and authored presentation
constructor closure. The measured parent-child route has separate
publication and mate-ownership requirements.
