# Ordinary line-loop solid writer on SOLIDWORKS 2026

The public adapter emits the ten streams below for a millimetre neutral
document with one canonical Front-plane line loop, one forward blind boss,
one driving `D1` and one resulting solid. The minimum contour has three
ordinary lines. The simple closed-loop validation runs before construction.
The implementation selects a model plan and supplies the ordinary
version-19000 recipe through the existing typed archive writers.
[Model admission](../../../src/convert/adapters/solidworks/Core/Preparation/PlanPartWrite.py)
· [Recipe](../../../src/convert/adapters/solidworks/Core/Preparation/MakePartRecipe.py)
· [Stream assembly](../../../src/convert/adapters/solidworks/Archive/Construction/Part/EmitPartStreams.py)

| Stream | Generated owners |
| --- | --- |
| `Header2` | The part locator, build identity, writer creation time and model bounds |
| `Contents/Config-0-ModelHeader` | The active part and independent header graph passed to the configuration map |
| `Contents/Config-0` | The modeled configuration, common system folders and datums, and the part's atom and object owners |
| `Contents/CMgr` | The ordinary manager, its configuration entry and the manager state used by the resolved stream |
| `Contents/CMgrHdr2` | The active configuration directory and its target stream ownership |
| `Contents/Config-0-ResolvedFeatures` | The actual ordered sketch lines, shared endpoints, support, extrusion contour and driving depth on the inherited map |
| `Contents/Definition` | The documented ordinary unit, presentation, style and tessellation settings |
| `_MO_VERSION_19000/Biography` | The empty typed biography of a newly generated document |
| `_MO_VERSION_19000/History` | The generated creation event and version provenance |
| `swXmlContents/KeyWords` | The actual ordered feature names, type tokens and dimension ownership |

The linked codec retains 105 ordinary resolved layouts, including 23
shared part layouts. It uses the actual configuration seed and manager
state with the compressed part flag and `CMgr.f658=0`. The typed reader
binds the real profile and its D1 owner and restores the closed line loop
through the regular SDK path.
[Config-0 graph](OrdinaryPartConfigGraph2026.md)
· [Resolved context](../../../src/convert/adapters/solidworks/Archive/Resolved/MakeResolvedCtx.py)

The scoped source reproduces the exact native-tested 8,094-byte Skew and
8,180-byte Step outputs. Independent guarded processes read back three
and six actual ordered lines and all 19 tree rows. The hash matches
bind the scoped source to the earlier native comparison of the same
bytes. The checks used zero runtime input-file reads. The native run
measured 240 numeric values across six fresh application lifetimes
and passed the two bracket controls.
[Native lifecycle](../measurements/2026/SdkDefaultPartNative01.json)
· [Public API and exact input hashes](../measurements/2026/SdkPublicPartWriter01.json)
