# Neutral two-stock through-cut geometry

This research slice advances `B04-SW2026-EXTRUDE-THROUGHALL` in PR #121 from baseline `41a1fa2fa0d303a2cd0c923a8eef7f54670b82fa`. It generates a closed neutral B-rep for two independent rectangular blind stocks and one circular through cut with an explicit historical selection. The solution preserves each user's stock, cut, selection and design-body identities. [Saved physical lineage](ThroughAllMultiStockHistory2026.md) · [Native disclosed experiment](ThroughAllMultiStockScope2026.md)

## Input and construction

The input is a neutral `CadDocument` with two ordered independent creates, one exact owned `D1` for each stock, one subsequent cut and two final design-body references. A single portable body selection resolves the cut's prior stock. The cut uses that stock's actual support and a signed world direction covering its blind extent. Both support transforms have right-handed signed cardinal frames, with one Front normal and one Right normal. A stable positive separation between the original stock boxes defines the admitted two-solid case. The input carries one active configuration, direct plane supports, ordinary rectangular axis relations and one free circle. The geometry boundary checks the absence of cached B-rep, native payloads and tessellation.

The unchanged stock uses `BuildPrism`. A strictly enclosed tool uses the existing `BuildCircleCut`. For a proper exterior side notch, solve the two circle/line intersections at the selected side. The two retained line fragments and the intervening inward arc join the three untouched edges into a simple analytic trim. Extrude the resulting ring through the actual signed D1 extent with `BuildTrimPrism`. The chord half-length is `sqrt((r-d)(r+d))`, and the arc span is `2 acos(d/r)`, where `d` is the distance from the external tool centre to the clipped side. Both intersections must lie strictly within that side and the cut must clear the other three sides. Closed shells, body-qualified topology IDs and the shared independent-model combinator preserve the two distinct final solids.

For the notch the removed area is the circular segment area. Its first moment from the circle centre has inward magnitude `2 h³ / 3`, where `h` is the chord half-length. Subtract that segment's area and planar moment from the original rectangle, then place the centroid at the stock's axial midpoint in the signed support frame. The model supplies volume, area, bounds and uniform-density centre of mass. Absolute mass requires material density. A separate cap integrator measures the constructed B-rep using the actual oriented line and circular coedges. It verifies the area, centre of mass, opposing uses on every edge and the Euler characteristic, including the inner loops for the enclosed tunnel.

## Guarded results

| Disclosed neutral state | Selected cut solid | Untouched solid | Untouched stock intersects the cutter ray |
| --- | --- | --- | --- |
| Moving D1 at 10 mm | 1,256.306035734 mm³, 868.169391592 mm², centre (21, −8.886027482, 6) mm | 1,120 mm³, 664 mm², centre (5, 8, 9) mm | No |
| Moving D1 at 29 mm | Identical B-rep and physical measures | 3,248 mm³, 1,500 mm², centre (14.5, 8, 9) mm | Yes |

The notch has 8 faces, 18 edges and 12 vertices. The uncut box has 6 faces, 12 edges and 8 vertices. Both are genus zero. Three additional independently modeled cases cover translated negative Front and Right frames with metre input, selecting the second reversed Right stock with the result first in body order, and a full enclosed tunnel with genus one. The largest independent integration residuals across the modeled cuts are `5.55e-11 mm³`, `1.48e-11 mm²` and `8.66e-12 mm` for volume, area and centre.

Eighteen fresh stdin-only processes cover five positive cases, eleven explicit refusals, one deterministic rebuild and one separate archived comparison. The archived save is read only after all neutral-generation processes finish. Its current mark 21 matches the generated body boxes and cut result. The derived prior stock body matches the actual physical states at marks 18 and 16, and both earlier activation states are body-free. The existing native disclosure separately agrees in volume, area, centre and bounds before and after the actual moving D1 edit. All workers record zero guarded external access attempts after imports. The receipt SHA-256 is `0d3cf94760cc8c363dc1fa8de91ff5a4c8dea264ca3599347d29f942c8f5f00d`. The measurement covers the neutral geometry and disclosed comparisons. [Pinned process receipt](../measurements/2026/TwoStockColdGeometry01.json) · [Prior native measurements](../measurements/2026/ThroughAllMultiStockScopeObserved01.json)

```sh
python3.14 -I -B re/tooling/sw2026/throughsource/twostockshape/ProveTwoStockShape.py \
  --selected /path/to/ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT
```

The next prerequisite is a fresh native model graph for two blind producers and the actual selected pointer chain. The ordinary one-stock preparation still consumes one stock and two feature operations. Its cold reconstruction admits an enclosed circle. This two-stock geometry is available to a separate neutral composer and controlled cache-omission experiment. Native cache omission, persistent face-role allocation, native open/edit acceptance and held-out coverage remain open. [Current one-stock preparation](../../../src/convert/adapters/solidworks/Archive/Construction/ThroughAll/ProjectThroughPart.py#L51) · [Two-stock native owner ledger](ThroughAllMultiStockArchive2026.md)
