# Origin owner lookup and sketch pose validation have different outcomes

## Expectation

An unrecognized origin reference should leave the sketch owner unknown and allow the existing support fallback.

## Actual behavior

The origin lookup and sketch reader call the same structural pose parser.
An exception from a sketch-only rule inside that parser can stop origin lookup before it can return an unknown owner.
The [review finding](https://github.com/TryUniCAD/Kit/pull/270#discussion_r4673570950) identified this path for rotated origin tangents.

## Required handling

Run the canonical basis check after the sketch reader establishes its local ownership and parses its pose.
Keep the origin lookup's existing identity pose check. A mismatch leaves the owner unknown.
The [process check](../../../../../re/solidworks/FeatureLadderRecovery/CheckPlacement.py) supplies a synthetic rotated pose to the origin parser.
Both public read modes must return a sketch with the existing stream-order support.
The input archive remains byte-identical. This check provides no vendor-saved rotated-origin file evidence.
The [principal-plane placement change](../../../../Changes/Solidworks/Inspection/Parts/SolidworksPlanePlacement.md) describes the reader boundary.
