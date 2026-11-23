# Authenticated measured perpendicular assembly bundles

Task `B04-SW2026-MATES-PERPENDICULAR-REGISTRY` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
The qualified shape contains two direct rigid occurrences of one owned
dimensioned rectangular part and one initially satisfied perpendicular
mate. The selected principal planes, fixed occurrence and child
dimensions are resolved from the neutral graph.

The [disclosed native lifecycle](../measurements/2026/SdkPerpendicularRegistryNative01.json)
includes four fresh SOLIDWORKS 2026 SP05.2 processes, 190 checks and two
passing controls. [Normalization](../../tooling/sw2026/BindPerpendicularMeasure.py)
checks the recorded packet and result hashes, original neutral source,
both frozen input archives and the successful transport intervals
before constructing the public measurement envelope. [Disclosed measurement](../measurements/2026/MeasuredPerpendicularPair/MeasuredOutput.json)

| Native tested file | Bytes | SHA-256 |
| --- | ---: | --- |
| `NeutralPerpPair.SLDASM` | 10,021 | `0a740c7a632ad769174c3d145710ca68502c33d07f575ac02ccb583363293187` |
| `NeutralPerpPrism.SLDPRT` | 8,694 | `86b6987dd8cd647e8c07067433ad41d08a7d7d0a257f2fc8956f4a747d4ed7e6` |

The disclosed recipe computes the projection of each selected plane
by ordered floating-point addition. The three products come from
the actual endpoint frame. Applying that formula on the current
compiler reproduces its tested parent. The earlier default arithmetic
on Python 3.14 yielded a one-ULP difference in the MatesList. The
sealed route keeps its original projection arithmetic. Each receipt
still requires an exact whole-bundle identity match. [Runtime arithmetic observations](PerpendicularRegistryAccepted2026.md)

For either sealed pair, the authenticated [registration receipt](../measurements/2026/SdkPerpendicularRegistryHeldout01.json)
already binds both complete generated files and 12 fresh native
processes with four healthy controls and 484 comparisons. The neutral
caller provides the actual epoch and locator. Both generated members
must match one slot. Their complete hashes bind the serialized native
locators. The writer checks the actual final filesystem location
independently before it reports native usability.

The current guarded host proof exercises both staged interfaces and
strict cold reads. It matches all 44 expected logical streams and
preserves the two selected occurrences and three child drivers.
Seven negative cases preserve the target directory, including
disclosed input submitted against a different authentic sealed
receipt. All nine processes have zero runtime input reads and zero
CAD launches. The public evidence uses deferred destinations. Fresh
same-locator delivery and combined-tree builds of the sealed inputs
remain unverified. No additional native, held-out or FCStd result
counts are claimed. [Guarded process results](../measurements/2026/MeasuredPerpendicularPair/HostPublication01.json)
