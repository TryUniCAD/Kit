# Cold readback of the named width-depth equation

Task `B04-SW2026-CORPUS/NAMED-EQUATION`, owner `/root/release_path`, integration `/root`, delivery PR #121. This scope is readback of one anchored Front Plane rectangle with a local width-to-depth equation and one forward blind boss. The exit for this step is linked parameter and solid readback of the disclosed model, unchanged canonical D1 results, and refusal of unrelated driver and active end states. Dependencies are the [source projection](FcstdCornerPlan2026.md), the [independent dormant depth](SdkBlindDormantDepth2026.md), and the [ordinary equation reader](../../../Documentation/Changes/Solidworks/Inspection/Relations/SolidworksLocalWidthDepthRead.md). [Guarded receipt](../measurements/2026/SdkNamedWidthDepth01.json)

The verifier reads the exact disclosed C130-P01 FCStd once through the normal strict adapter. It binds `width` and `height` to the actual width and height of the planar rectangle, the native `Length` target to its Pad, and the 10 mm dormant value to the original `Length2` owner. The shared typed constructors build a complete ten-stream, 9,043-byte diagnostic part in memory from that bounded recipe. The complete part SHA-256 is `5c430281a3daec6bb029eb55282b0cf7ac2cc7d02d81fb26a802b0f66e47f3db`. No CAD process is launched.

The reader verifies the enabled relation's exact text, operator and scalar operands, local unit-component refs, and both live annotation handles. The sketch handles own the actual horizontal 40 mm and vertical 20 mm sides. The equation targets the 20 mm `Length` in `moEndSpec_c.f18`. The separate positive D2 has a distinct display, feature handle, dimension and parameter allocated in ResolvedFeatures at `f20`. Its persistent dimension ID is 23 and the active ID is 22. It is reported with its owner and value under `local_width_depth_equation.dormant_depth`. The active neutral feature remains one-direction blind.

Strict default and design-only reads expose the same named live parameter IDs and typed relation evidence. The default read verifies the solid against its linked first body creator. It returns six faces, twelve edges, eight vertices, volume 16,000 mm³, area 4,000 mm² and extent from the origin to (40, 20, 20) mm. Design-only keeps the existing history projection and returns no B-rep. A foreign sketch parameter under D2, a repeated dormant dimension ID, an active second direction, a dormant clone with the same scalar as the active depth, and a relation selecting height each withhold the typed equation. Strict full reading refuses all five. Design-only can still return its existing partial inventory.

Two additional fresh workers reproduce the disclosed canonical D1 request on base `93743aea1` and this reader. Both produce the original 9,157-byte archive, all ten stream hashes and identical complete strict full and design-only neutral documents. The named requests also agree across two fresh workers. The four guarded workers record zero runtime file reads after source intake. Both public writing entry points refuse the intact FCStd source and the named readback before changing the caller's stream or cursor.

The diagnostic archive has no vendor acceptance or corpus credit. The [separate source-owner comparison](SdkC130SourceOwners2026.md) composes the actual body caption and verifies the remaining Pad and lineage boundaries. Complete source transfer still needs the unresolved source semantics, independently locked native edit and reopen measurements, and authenticated public output evidence. There is no named saved-cache or writer scope in this tranche.

## Reproduction

Supply the frozen disclosed census inventory and the canonical disclosed width-depth neutral request. The controller prints a sanitized receipt with tool, source, archive and stream digests.

```sh
python3.14 -I -B re/tooling/sw2026/equations/ProveNamedWidthDepth.py \
  --inventory /path/to/PublicFcstdWriterCensus01/VerifiedInputs01.json \
  --equation /path/to/WidthDepthSameLocator04/Neutral.json
```
