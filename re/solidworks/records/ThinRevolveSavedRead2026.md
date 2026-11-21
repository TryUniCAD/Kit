# Saved thin revolve readback

The normal strict SDK reader projects the editable definition and the physical body for the disclosed SOLIDWORKS 2026 SP05.2 saves of a one-line, partial forward thin boss revolve. The reader checks the active native cache before binding it to the producing feature. A request without geometry verifies the same source owners and omits the B-rep and payloads from the returned document.

## Evidence and acquisition

[Guarded process receipt](../measurements/2026/SdkThinNativeSavedRead01.json) binds the original, edited and cold controls. The [Front wire audit](ThinRevolveWireOwners2026.md) binds the disclosed source lock `f851a26cc549433b5a342b2b7801171f56e356b50866b7f84929353966d6fe25`. The [Top and Right source audit](ThinRevolvePrincipal2026.md) binds the separate lock `7475170f6f524ba33fe826b54976f7d2793c9bd603851d1a31866220d26c6253`. Both source batches were authored and reopened by SOLIDWORKS 2026 SP05.2 `34.5.2.0604`, executable SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`. Their two controls each and all 18 source lifecycle phases passed. The 12 initial and edited part hashes and their two exact typed stream hashes per state are recorded in the guarded receipt.

## Ownership

| Owner | Condition used by the reader |
| --- | --- |
| ModelHeader, Config-0, CMgr and ResolvedFeatures | Complete version-19000 graph. One active configuration, one open profile and one producing thin boss, plus the ordinary system features. The native relation manager has its saved-state flag and no equation rows or external relation owners. |
| `moRevolutionThin_c.f830` and `f8d8.f18` | Actual local component and selected construction line, with the principal frame and saved model-space axis agreeing. One positive partial angular D1. |
| `moThinSpec_c.f08`, `f10` and `f48` | Actual distinct display, handle, dimension and parameter chains. A live positive D3 and, in unequal Two Directions wall mode, a separate positive D4. The saved end thickness remains inactive at `1e-7`. A retained radial display passes only the measured zero D7 shape and never becomes a driver. |
| Feature body choosers and `moPart_c.fd88` | Four distinct mapped face refs from two choosers reuse the same ten surface representations pairwise. Their constituent refs name this feature and the selected configuration. The third chooser is empty. The output atom and one stored atom ID link into the active configuration. |
| `Contents/Config-0-Partition` | Current native active and delta graphs. `ATOM_ID_2001`, `BODY_MATCH` and the last-modifying feature attribute agree with the linked archive domains. The current kernel mark is the feature's `f3d0.f18`. The predecessor is the model's `fe38.f18`. The active kernel body owns its implicit name. |
| Boundary and public body | One complete closed annular sector, whose eight corners, twelve trimmed edges and six plane/cylinder supports agree with the sector derived from the linked live drivers and signed frame. The reader retains the original native B-rep and payloads and assigns the actual design-body identity and native provenance. The topology summary follows the verified sector. |

The measured tail stores current mark 7 on initial saves, 13 on most edited saves and 15 on the independent two-wall edit. All observed predecessor marks are 3. The reader compares the two typed owners to the decoded mark identities. It uses no fixed tables for marks, atom IDs or feature IDs.

## Reproduction and limits

Run from the checkout root. The named capture and generated-packet subdirectories must be the disclosed measurements. Use a new report path.

```sh
python3.14 -B re/tooling/sw2026/revolve/ThinArchive/AuditThinSaved.py \
  --home /absolute/path/to/Oracle121Takeover \
  --report /tmp/SdkThinNativeSavedRead.json
```

The 19 fresh host workers verify both normal strict read modes on each source state. They compare the actual angle and thickness drivers, selected line, retained body and cache, volume and area to six significant figures, and oracle bounds. The native receipts contain center-of-mass and recursive feature-tree observations. The SDK comparison verifies the editable feature and its actual parent, plus identical feature, parameter, sketch and selection projections between its two strict modes. The SDK topology summary exposes volume, area and bounds.

Six cold preparations reproduce all existing native-tested file hashes at the original logical locators and epoch. Their cold reads still use the pre-existing controls and their writers make zero runtime file reads. The five in-memory negative variants refuse both typed semantic and body binding through the normal read path. These variants corrupt an atom tag association, replace a sector with a different principal frame under the same tags, move the archive's current mark, activate the radial display value, or redirect a face representation's producer. The previous generic representation remains available when the typed profile rejects.

The native cache and its lifecycle state are read-side evidence. The accepted neutral writer boundary, unsupported thin cuts, cap ends, bend variants, other rotations, other profile layouts, and whole-source round-trip eligibility have no new qualification. This work consumes only disclosed inputs and adds zero independent held-out results. [Prior writer qualification](ThinRevolvePublic2026.md) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Cache mark rule](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Revolve/ThinCacheUsesTwoMarks.md)
