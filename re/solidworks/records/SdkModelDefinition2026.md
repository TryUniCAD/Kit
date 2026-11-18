# Ordinary SDK part and assembly Definition

Task `B04-SW2026-DEFINITION`, owner `/root`, delivery PR #121.
The shared SDK Definition codec covers the measured version-19000 UI document
shapes. The native `Header2`, configuration, features and cached geometry have
separate owners. The affected archive base is one. The UI root is untagged.

## Wire structure and source rules

The constructors use the pinned `slduiu.dll` build and UI object sources
already bound in [the model construction record](ModelConstruction2026.md#definition-construction)
and [the drawing Definition grammar](DrawingDefinitionGrammar2026.md).
The runtime classes use the 2026 serialized class map with the pinned
`uoJournal_c` schema zero. The assembly tail and signed preferences follow
the exact [assembly Definition constructor and serializer](AssemblyDefinition2026.md).
The part's kilograms-per-cubic-metre value follows the `sldprtu` part
constructor, density getter and API unit contract recorded in the model
construction ledger.

| Fields | Fresh classes and data lineage |
| --- | --- |
| `fa58/fa5c/fa60/fa64` | Input: shaded tessellation, derived angular tessellation, wireframe tessellation and optimal tessellation. The default part profile uses the registered factory tuple `26,4,25,true`. |
| `fa74` | Selected ordinary UI format switch, constructor value one. |
| Document CLSID | Derived from the concrete model document kind, `83a33d30` for a part and `83a33d36` for an assembly with the shared GUID tail. |
| `fac0/fac8` | Fresh document has no UI sketch owner and sets the corresponding constructor byte to zero. |
| `fae8/faf0` | Derived ordinary identity transforms. The camera composer computes its separate view transforms from the authored frame. Matrix and perspective bodies follow the transform's mode. |
| `facc/fad0/fad4` | UI constructor state 3, 0, 3. |
| `fad8_0/fad8_1` | Derived from the explicit two-word bit set. The low and high 32-bit values use signed two's-complement encoding. |
| `fba8` | The input drafting-standard class selects a concrete schema-one node. The current standard base contributes no body fields. |
| `f878/f870/faf8` | The fresh writer constructs empty style and environment collections and an empty concrete font manager. Native readback traverses all actual stored children, the ordered style segments, font entries and both per-environment splitter grids. Counts come from the corresponding collections and grid dimensions. |
| `basedoc/fbf0/fb20` | No authored OLE or model presentation objects. The fresh second base-document field and the model data integer are zero. |
| `fb54/fb3c/fb40/fd68/f850/fab8/fb00/fb04/fa6c/fa10/fa98` | Ordinary constructor values from the version-matched UI initializer. The nullable owners start absent. |
| `ffd8` | Notebook constructor, reset and journal initialization supply separate empty lists and distinct state words. Its name is authored. Journal time and state are initialized zero. |
| `f1000/fa90/f1014` | Constructor zero/one for the first and last fields. The native `0x7a` stream-compression preference is an explicit boolean input with registered default false. |
| `expand_keys/expand_vals/f7b8/has_pwmaterial` | Fresh expansion keys and values are empty, the flag word is zero and the fresh renderer owner is absent. Saved streams with a renderer owner carry two signed words and its counted object list before the trailer. |
| `f1138/f1158/f1150/ff40/f1140/ff88/ffb0` | No authored content in these fresh text and collection owners. All lengths and counts follow the actual values. |
| `f1348/f1350/f134c/f1354/fa78/f1358/f1370` | Fresh constructor words and the separate PhotoView options initializer. |
| `f1388/f1390/f7bc/f135c/f13c8/f13d0/f1400/f1408/f13f0/fa7c/fa80/fd78` | Ordinary fresh constructor words and an empty counted options array. |
| `f12e8/f1424/f930/f1304/fd7c/f1368/f3e8/f11a0` | Ordinary fresh constructor pointer, scalar words and empty variation collection. |
| `f1688` | Document material-density preference in kilograms per cubic metre, finite and positive, stored as binary64. Its registered default is 1000. The effective mass calculation has a separate body density. |
| `f1840/f19c8/f1a38/f1a40/f1a48/f19b0/f19b8/f19c0/f1afc` | Assembly constructor fields in the recovered assembly tail. Preserve the ordinary distinct words, empty Strings and native 0.0127 value. |
| `f1b48` | The ten native preferences are authored through their exact slot numbers. The nested constructor owns zero `f08` and derives the bounded `f10` from slot `5fd`. |

No populated saved record is an input to fresh generation. The reader preserves
the typed saved fields for exact stream round trips. Optional non-null classes
outside the registered graph and unfamiliar archive versions fail closed. The
drawing variant shares the matching UI field order and has its own model,
format terminator and tail. Its inline model graph and contextual map remain
under the drawing codec.

## Qualification

[Process and source receipt](../measurements/2026/SdkModelDefinition01.json) ·
[Disclosed native stream inventory](../measurements/2026/SdkModelDefinitionCorpus01.json)

The [factory settings trace](../measurements/2026/SdkPartPreferenceDefaults01.json)
identifies the exact preference constructors and confirms their registered
initial values. The [default part recipe](SdkDefaultPartRecipe2026.md) applies
those values to independent fresh neutral documents.

The independent corpus audit reads committed disclosed files from a pinned
revision. It excludes original holdout slots. The SDK consumes all 84
Definitions, including 64 distinct payloads. Encoded bytes and final map
counts match exactly. The phase uses neither a fresh oracle nor another
recorded stream as a reconstruction source.

Four independent fresh designs vary the drafting standard, document kind,
journal name and two-word flags. They exercise positive part density, both
native assembly threshold clamp endpoints and multi-unit UTF-16 text. Each
fresh encoding matches the independent research schema and survives a second
process reading and rewriting the exact bytes. Nine invalid constructor or
stream requests fail closed. The guarded build and preparation report zero
runtime input reads.

The disclosed D03 part keeps the complete generated container unchanged
through the composer migration. The ordinary part, camera and planar assembly
process regressions pass. The integrated drawing sheet proof reruns all 22
outcomes after the shared layout extraction and keeps the exact comparable
results. This work provides an internal stream serializer and constructor.
Whole-document SDK writing and the production corpus audit remain open.
