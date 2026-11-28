# Public full-ellipse blind boss readback

This evidence covers the normal SOLIDWORKS part reader for the two disclosed cache-free SOLIDWORKS 2026 SP05.2 full-ellipse bosses. Both candidates are byte-identical to the guarded SDK output in [SdkColdEllipsePublic01](../measurements/2026/SdkColdEllipsePublic01.json). The prior native build was `34.5.2.0604`. Its terminal and eight phase receipts are pinned in the [reader receipt](../measurements/2026/SdkColdEllipseRead01.json).

## Linked source ownership

The ordinary typed reader reports `sgEllipseHandle` schema 1 as unsupported. This diagnostic selects a second, stricter read using the existing ellipse grammar. The alternate read must prove a complete linked Config-0, CMgr and ResolvedFeatures archive with one ordinary Default configuration, the exact compressed part context and no equations, body cache, auxiliary atoms or unsupported feature roots. The actual profile, its sketch, sole ellipse handle and forward blind boss retain their typed map aliases. The profile references the selected canonical Front support. The positive D1 comes from the ordinary live extrusion parameter, dimension, handle and display owners.

The ellipse row points to five conic axes and a distinct seam point. `fc8_s` and `fcc_s` refer to the same seam point, which has its own permanent identity and lies at the major station of this cold profile. The two semiaxes are orthogonal, positively oriented and retain their opposite stations. The reader checks six distinct point identities, requires the mapped ellipse handle on the actual seam only, and checks the ordinary free and unstyled geometry and solver fields. The sketch becomes one closed editable `EllipseGeometry`. The original support, live D1, boss and one final design body remain linked. No sketch parameter or relation is inferred where the source has none.

## Neutral solid and checks

The default read constructs an exact swept ellipse with two planar caps and one tensor-product rational surface. The lateral section uses four rational quadratic quarters. Their signed control pairs are the axis stations and the intersections of consecutive station tangents. The diagonal tangent intersections have weight `sqrt(1/2)`. The linear sweep uses the actual D1 depth. Both cap trims are exact rational curves in their own oriented plane frames. The same axial seam has two line trims at opposite sides of the lateral parameter interval. Kit assigns this neutral topology and does not recover native kernel edge identifiers from the cache-free source.

The public reader and neutral JSON round trip were exercised with and without B-rep through two guarded processes. In each case, 201 independently evaluated curve-to-trim and interior surface points verify the conic and its sewing. The exact mass-property formulas and independent perimeter integration agree. Seventeen values per model agree to six significant figures with actual prior cold native observations, including volume, surface area, the implied uniform centroid, signed bounds and rim seam points. The native receipt also reports one body and three faces for each case. Ordinary saved circle and rectangle controls keep their existing read behavior.

Fresh contrast processes check the unqualified paths. Different segment endpoints, crossed axis roles, a changed mapped handle, changed point style and a reversed boss do not publish a typed closed ellipse or reconstructed solid. Raw B-rep extraction still requires a stored native payload. Saved/rebuilt seam variants, editable ellipse constraints, other supports and other extrusion modes are outside this scope. This is a reader verification against already disclosed files. Independent native writer qualification remains in [EllipseColdSealedNative01](../measurements/2026/EllipseColdSealedNative01.json).

## Reproduction

With the disclosed `EllipseColdPrototype02` directory at `$disclosed`, run from the Kit repository with a fresh output name.

```sh
python -I -B re/tooling/sw2026/ellipse_source/ProvePublicEllipseRead.py \
  --trial "$disclosed/Packet/Trial.json" \
  --native "$disclosed/DisclosedResult.json" \
  --output /tmp/KitPublicEllipseRead.json
```

The supervisor verifies the original terminal, every component phase, both candidate files and the two controls. The guarded positive processes receive only their candidate and disclosed expectations before the runtime guard starts. The malformed contrasts exercise the existing generic refusal path separately. The receipt records each new or changed SDK file and both proof scripts by SHA-256.
