# Compose two empty native owners in a generated part

Task `A12b-EmptyOwnersPartComposition` covers an offline archive made from three explicit research inputs. It combines the exact straight-line blind-boss presentation, the appearance allocator and the keyed empty cut-list property owner. The three inputs come from separate research contracts. They describe the scope of this generated archive and make no claim to all state in a single original source.

## Reproduce the combined archive

Use CPython 3.14.6 AMD64 with zlib-ng 1.3.1 to reproduce the recorded byte digests. Set `$reader121` to an unmodified checkout of `c0a401a607759fb0c2589647c2a22af65ebb7ce1` and `$propertyRoot` to an unmodified checkout of `5fb7e7737f0b9af52373da5e3f4556cd83ba8607`. Keep outputs outside the checkout.

- Set `$partRequest` to the canonical captured-name request with active `Default` and plane visibility on, SHA-256 `cdefa9be027d8257c0f5b08cf722efff746f38960b86e5e73eac2e63bf7d1ac4`. [Exact sketch and presentation](VendorBlindBossExactSketchPresentation.md#replay-the-captured-configuration-name)
- Set `$appearanceRequest` to the canonical `AppearanceValue` with present manager and next ID 4, SHA-256 `02da48e4745fc60dbe2d6f23146ab185e981703a5a66a78c8e4f277ff82c1f30`. [Allocator extraction and replay](ResavedRendererRead.md#replay-the-empty-allocator-in-a-fresh-definition)
- Set `$propertyRequest` to `re/solidworks/PropertyBoundary/Requests/Present.json` in the property checkout, SHA-256 `45ba35ff0c0e7c501ad6f9620920c7491a14eb7157e3d2fe2e487f248c9d63a9`. [Empty property-owner guide](https://github.com/TryUniCAD/Kit/blob/5fb7e7737f0b9af52373da5e3f4556cd83ba8607/re/solidworks/records/EmptyCutPropertyOwner.md)

```powershell
python -I -B re/solidworks/RendererBoundary/ComposeEmptyOwnersPart.py --dependency-root $reader121 --property-root $propertyRoot --part-request $partRequest --appearance-request $appearanceRequest --property-request $propertyRequest --locator 'C:\KitEncoderRoundTrip\reconstruction.SLDPRT' --epoch 1785626030 --output $unusedOutput
```

The constructor reuses the exact SI validation and Top writer. `FinishBlindMut` supplies the in-memory part graph and its generated streams. The existing typed appearance maker fills the fresh Definition owner before that graph is serialized for the final archive. The property constructor independently supplies its binary manager and three XML members. `BuildSldprt` emits the final container from the resulting clear streams. Generation receives only the three JSON requests, locator and epoch, with zero observed external access attempts inside construction. Native source files and previous archive outputs remain outside its inputs.

## Measured boundaries

The fresh ten-stream base reproduced SHA-256 `2d027288f37b8bffe90dc289842913b9c4ca807942fe6b32ad1eb7fea5acea29`. Both combined runs reproduced the 10,932-byte SHA-256 `e5b83d46bb2db35e171c10bc5988b717eee0751f373c3edcc5986c794ad901cd`. Nine base streams stayed byte-identical. Definition changed to 469 bytes with signed allocator words `(4, 0)`, zero references and map endpoint 7. The 138-byte binary property manager has key 0 and object slots 2, 4, 6 and 8 for manager, container, file owner and cut owner, ending at slot 9. The XML scopes are empty. The singleton configuration directory, CMgr aliases, keyword row and physical Config-0 agree on ID 0 and `Default`. The binary property manager's key 0 belongs to its own map.

Typed readback retained the eight exact metre coordinates with closed endpoint aliases, linked depth `0x1.d4e8fb00bcbe6p-7`, signed Top frame, construction-plane bit and MMGS/MKS table codes. The regenerated prism from the linked parameters and checked profile has six faces, twelve edges, eight vertices and 7,584.3 mm³. Its configuration and resolved maps retain shared owners at the same boundaries as the base.

Repeat with `AppearanceValue` set to absent/1 and with the property checkout's `Absent.json` to isolate the two owners. The absent-cut request retains a present binary manager and keyed file owner, with a null cut pointer and endpoint 7. Removing only appearance changed Definition. Removing only the cut owner changed CusProps. Removing both changed those two streams. The remaining streams and linked CAD checks agreed. Four actual processes rejected absent/4, an extra appearance field, an integer cut toggle and a mismatched Top configuration before output. [Exact archive, per-stream and refusal evidence](../measurements/2026/EmptyOwnersPartComposition.json)

A separate verification run emitted the same archive, reproduced the four refusals, and verified the two owners in a separate pinned read process. It measured equality of the regenerated structural B-rep across the exact base and composition, including bounds, surface area and volume. The report retains the independent method and result digests. [Independent process summary](../measurements/2026/EmptyOwnersPartComposition.json)

#121 ordinary Definition refuses allocator 4. With default strict public read options, #121 refuses both the unchanged base and composition for lack of a readable Parasolid payload. With B-rep disabled, #121 returns both and projects the boss as `create` in the base and `join` in the composition. Frozen #316 returns both at default strict with `create`, the same D1 and the same topology, but reports its unsupported text-property-manager diagnostic for the composition. These reader outcomes limit production admission. Native load, edit, save and the remaining source appearance, property and provenance are unqualified. [Distinct strict-reader checks](../../../Documentation/Gotchas/Research/Writers/SolidworksStrictGeometryDependsOnPropertyStreamRoster.md)
