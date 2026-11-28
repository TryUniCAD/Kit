# The oblique cylinder length belongs to its selected limit plane

A blind extrusion normally owns an editable depth parameter. Reusing that assumption for a circular extrusion terminated on a separate plane can bind an inactive distance display instead of the actual source height.

The proposed five-driver lowering keeps the circle on its original local Front plane, uses two angular planes to derive the real selected direction axis and terminates at a height-offset plane. The source vertical height belongs to `D1@HeightLimit`. Radius belongs to the actual circular sketch and each tilt belongs to its own angular plane. `FeatureExtrusion3` still receives a positive distance scalar, but that scalar does not prove an active blind-depth driver when the actual end is selected plane type `4`.

The author observer edits each real driver independently, checks its own feature display binding and measures the whole solid before save/fresh reopen. It records actual selected references and API depth readback without treating that readback as an additional authored length. Selected-end inactive-display presence still needs exact source correlation; a stale blind parameter is not silently accepted as the physical height.

[Source protocol and evidence](../../../../../../re/solidworks/records/FreecadObliqueCylinderAuthoring2026.md). Current verification is host-only preparation. No generated writer, completed native source lock or new native acceptance is claimed.
