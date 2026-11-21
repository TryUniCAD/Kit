# Direct dependency enumeration for a SOLIDWORKS 2026 single-stock pattern

Both files in the first strict native trial failed the direct-parent comparison on SOLIDWORKS 2026 SP05.2, 34.5.2.0604. They opened and rebuilt with zero errors and warnings, had the independently predicted one solid and 21 or 26 faces, and passed 33 checks per case before the comparison. The exact differing parent was the base plate. The initial result digest is `b20cc4286fb26d034b17bf241ea4289e4327031dbadf7fc7cfc1a8c8a3010a41`. Both bracketing controls passed. The [scope receipt](../measurements/2026/LocalLinearPatternParentScope01.json) binds the failed result and both case records with the actual parent names.

## Native branches

The official feature API exposes a direct parent collection. The installed build's `sldapiu.dll` imports `moFeature_c::getParents`, which calls feature virtual slots `+0x13b0` and `+0x13b8`. The concrete `moLPattern_c` vtable binds the first to `0x4bfd42c0`. That implementation calls the inherited `0x4c053080` routine, then enumerates the actual direction wrapper `f1288` at `0x4bfd42ee`. The second virtual method at `0x4c0571a0` also uses the actual retained seed list in the ordinary feature-seed mode. [SOLIDWORKS 2026 IFeature API](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeature_members.html)

The first inherited routine selects feature-seed mode when `f948=0` and then tests bit 0 of `f9f0` at `0x4c05320c`. If clear, it walks the current body-scope references in `f548` and adds their local features. The observed ordinary pattern does not use fallback `f550`. If the bit is set, the function skips that additional body-scope enumeration and still adds the actual seed. The separate selected direction is still enumerated by the derived class. Four disclosed SOLIDWORKS-saved oblique cases have `f9f0=1`, one actual seed, and an actual scoped body and local datum.

The exact `moCompSolidBody_c` callback enters `0x4b7f9030` by slot `+0xa8`. With no face reference, it can resolve `f18` against the local atom manager, call `moAtom_c::getBaseAtom` and append that atom's producing feature at `0x4b7f91f7`. The stored base feature ID `f108` supplies a distinct fallback only if the list is still empty. Removing that ID would not remove the primary atom-derived plate dependency. The safe correction retains the scope wrapper, local seed result, ordered atom lineage and base producer and changes the enumeration decision.

## Input-derived correction

[MakeLocalPattern.py](../../tooling/sw2026/linear_pattern/MakeLocalPattern.py) sets the scope bit after the shared lineage builder verifies that the pattern consumes the sole current seed result and that the seed's prior plate has already been retired. It publishes the new live result with the actual seed and base identities. This derives already-valid single-stock scope before native dependency enumeration. The cold appearance field `f1054` stays at its separate constructor state. The guard also refuses a cleared bit in this specific serialized scope.

The generated initial and corrected files use identical neutral models, locators, analytic physical predictions, stream lengths and object maps. There is exactly one changed byte in each decompressed ResolvedFeatures stream, at 18382 in case A and 18390 in case B. Each change is from zero to one at the typed pattern field. Every other container payload is exact, including Config-0 and both headers. The original data and result stay immutable. The corrected archive and typed negative contrasts pass host proof. Corrected native verification is pending.

The corrected manifest SHA is `b04e279af46524b69a3198c50e2ba06a89702327be1885eb5e2283d82f2d84a3`. Rebuild the corrected files with the [original guarded construction command](LocalLinearPatternContainer2026.md#reproduction-and-boundaries), giving the output receipt the name `LocalLinearPatternContainer02.json`. To bind the old native result and compare the exact typed streams, run the audit on the two frozen directories.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/AuditLocalPatternParentScope.py \
  --initial /tmp/KitLocalPattern.K7SC5C \
  --corrected /tmp/KitScopedPattern.GQelH9 \
  --native-result /Users/odin/Documents/UniCAD/Oracle121Takeover/GeneratedLocalPatternNative01/NativeResult \
  --binaries /Users/odin/Documents/UniCAD/Sw2026Research01a1dc84/bin \
  --output /tmp/<unused-directory>/LocalLinearPatternParentScope01.json
```

A controlled repeat must verify exactly the actual seed and direction as direct parents before the D3 edit, after rebuild and in a fresh reopen. The existing native acceptance checks and healthy controls remain required. No protected input contributed to the correction.
