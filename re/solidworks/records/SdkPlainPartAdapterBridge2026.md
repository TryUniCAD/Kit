# Internal SDK plain-part preparation bridge

Task `B04-SW2026-CONSTRUCTION`, owner `/root/flag_ownership`, delivery PR #121.
This is the unregistered adapter preparation step above the complete
[SDK rectangular blind-boss composer](SdkBlindPartConstruction2026.md).
It owns new `Core/Preparation` helpers, a dedicated process integration and its
transport. It changes no public adapter, registration, constructor, archive layout,
reader or prior frozen source. Native and held-out admission remain root-owned.

## Actual public boundary

The default SDK uses `convert.api.ApiOpen.OpenDocument` for reads and
`convert.api.ApiWrite.WriteDocument` for saves. `SldprtAdapter` implements
`info`, `probe` and `read`; it has no `supports` or `write` method. Default writer
availability is determined by `GetRegistry().GetWriter` / `GetWriters`, not a
SOLIDWORKS-specific `CanWrite` method. The new bridge is not imported or called by
those public entry points and is not exported as a writer.

[`PreparePart`](../../../src/convert/adapters/solidworks/Core/Preparation/PreparePart.py)
takes the actual `CadDocument`, ordinary SDK destination type, an explicit internal
`PartBuildInput` recipe and optional existing `WriteOptions`. It returns the actual
`PartCandidate` from `MakeBlindPart`. It does not write any path or stream, return
a `WriteResult`, register a writer or assert vendor/application usability.

The neutral document currently has no standard fields for font face, print widths,
localized generated folder names, annotation defaults, target build history and
the other required presentation/provenance inputs. The bridge therefore retains
the typed internal recipe. It does not invent these settings, put a serialized
recipe in public `WriteOptions.values`, read installed preferences, infer them
from a vendor save or introduce a public enable-writer switch. Selecting a future
document-level presentation policy remains a separate admission decision.

## Model and option projection

The bridge calls the existing exact rectangle projector and composer. It admits
only the concrete schema-1.0 neutral document, one active independent configuration,
canonical Front Plane support, unconstrained closed four-line axis-aligned profile,
one driving `D1` and one positive plain forward blind create boss. Assemblies,
drawings, payloads, materials, selections, additional modeled entities, constraints,
unsupported end conditions and feature options continue to reject.

For this initial adapter boundary, diagnostics, extended source attributes,
per-record provenance and supplied body-topology records also reject. They are
not silently treated as projected metadata or cache neutrality. This restriction
does not change existing public reader behavior or classify those source domains
as impossible to support.

| Input / owner                            | Rule                                                                                                                                                                                                                                        |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Geometry, feature name and driving depth | The actual neutral records feed the existing `ProjectPlain` and `MakeBlindPart`. No recipe geometry or recorded payload is available.                                                                                                       |
| Active configuration                     | `WriteOptions.configuration` may be absent or equal the actual sole configuration ID/name. Other selections reject. Native name/local ID and progress remain owned by the shared composer.                                                  |
| Document units                           | Actual neutral `mm/m/in` selects `mmgs/mks/ips`. Explicit recipe angular presentation and decimal precision remain presentation inputs. A stale recipe length/system cannot override the model.                                             |
| Support name                             | The actual neutral canonical support supplies the generated principal z-plane name. Other generated system names remain explicit recipe input.                                                                                              |
| Presentation, target, density and clocks | Retain the typed explicit recipe, with all existing construction validation. No current directory, filesystem stat, source file or vendor preference is consulted.                                                                          |
| Native self identity                     | Replace the recipe path with the selected final target and retain the recipe's explicit save event. The shared self-file factory creates the actual native handles and configuration identity.                                              |
| Format                                   | Only absent/ordinary part IDs and the existing `sldprt` extension spelling are admitted. Assembly/drawing formats reject.                                                                                                                   |
| `overwrite` / `validate`                 | Require actual Boolean values. Preparation performs strict model/admission checks even when general validation is false. Preparation does not mutate a destination; overwrite/transaction policy remains the outer writer's responsibility. |
| Generic policy values                    | Accept only the existing final-destination/overwrite and carrier/self-contained/native-transfer/portable Boolean vocabulary. They are not evidence of native acceptance. Unknown fields and malformed policy types reject.                  |

The returned candidate retains its actual model, configuration, profile, live
dimension, headers and linked map identities. No alias is recovered by decoding
research objects and no saved selection string is involved.

## Destination and staging boundary

The normal registry's `WritePathStaged` places the adapter target inside a temporary
directory and publishes the actual requested path in the existing
`WriteOptions.values["final_destination"]`. The bridge gives that final identity
precedence and verifies that staged and final filenames agree. It never encodes
the temporary directory as the model's native self identity.

Without a staged final path, the destination itself supplies the identity. Binary
memory destinations require an explicit final destination; text destinations and
unnamed binary streams reject. The bridge performs no sink write and no filesystem
existence query. It cannot create, overwrite, resolve or reopen a model file.

The current fresh self-file factory accepts an explicit absolute Windows path.
Ordinary drive and UNC paths are retained as authored text; relative paths,
unmapped POSIX paths, device names, invalid path components and ambiguous relative
segments reject. A POSIX staging path is accepted only when the actual final native
Windows path is explicitly supplied. No host drive mapping is guessed. These are
the selected bridge's admission rules, not a claim that every native saved self
reference must have this form. Standalone relocation and absent old-self behavior
need their own native evidence.

The [destination gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Construction/FinalDestinationOwnsNativeSelfIdentity.md)
records the actual shared staging contract and current limit.

## Process proof and custody

The initial frozen overlay has ten executable paths: six SDK helpers, three
permanent integration modules and one research transport. Its
`SourceManifest01.json` SHA-256 is
`bd69ea174f2e9cfa38d4dd7a453167ff741d0a5e9b302d44d32ea0ad1854a225`.
It separately binds 62 unchanged actual part dependencies from the original
70-path constructor proof. The original receipt is preserved. Subsequent
polygon-only changes to two unused constructor-test helpers are not restored,
treated as bridge dependencies or assigned to this lane.

The first independent replay froze 4,595 source files at base
`62348bee4aa27ca31eec6b77be6262d60f2f2cc0`, source manifest SHA-256
`c6368b7ecb1d315a49ff2919db5e26ba27a5b8eb10e0033196952d7174f02b59`.
All ten initial owned hashes and 62 actual part dependencies match that virgin
snapshot. Public read then reached the lazy `DocumentProvenance` code import
inside the strict guard and the replay rejected before any model input-file read.
No passing process or native acceptance is transferred from this failed replay.

The causal retry changes only the research process's code preloads:
`HasProvenance`, `WalkDocuments`, `GetDocument` and `ToJson` load before
`AUDIT.BeginBuild`. The nine normal SDK/test modules, guard, original part sources
and failed snapshot remain unchanged. `SourceManifest02.json` SHA-256 is
`1f96cee914fea98cb3c73be35eb08aa6e7bc75b03069d113a7776cd403c7d266`;
the revised transport SHA-256 is
`f0a76f6ac56381fc239f82c05b2a130f74f8236abac6dbde37e6e55efab8e652`.
The [code-preload gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Construction/PublicReadNeedsCodePreload.md)
records the reached source chain and why the runtime boundary stays strict.

`TestPartBridge` authors two neutral documents and runs a fresh guarded process
for each. Each worker exercises the complete adapter-to-constructor boundary:

1. A standard `WriteOptions` configuration-ID request and POSIX staging path with
   explicit final native identity produce exactly the direct SDK candidate bytes.
2. Deliberately stale recipe length units, support label and path cannot override
   the actual neutral facts and final target.
3. Configuration-name and direct native path selection, plus binary preparation,
   preserve the same complete bytes and leave caller memory streams unchanged.
4. The actual default public SDK reader recovers the boss, four-line profile and
   driving parameter/value ownership from those generated bytes with B-rep off.
5. Default writer discovery remains unavailable; a real public save attempt rejects
   before altering its caller-owned destination.
6. Twenty-one invalid full requests per design reject, including extra public
   knobs, unsupported profiles/provenance/topology, format/configuration errors,
   invalid paths, unbound streams and malformed policy fields.

The worker performed AST, format, lint, type, steering and path checks only.
It has not executed the integration, used the VM or opened any held-out input.
The corrected independent root snapshot retains the same 4,595-source base with
manifest SHA-256
`06d2c953677debba1c3cd4d6256bb20f417f1ac9501e171098d0e7f0ee4d9260`.
`TestPartBridge` passed on that exact source. The separately retained two-worker
raw proof has SHA-256
`7b915a7319bf6b68005f263952460f5ca188874826094a1a8c8751c685fe3f21`.

Both workers passed the full adapter-to-constructor comparison, default public
readback and intentional public save rejection, with zero runtime input reads or
SDK research implementation imports. All forty-two invalid complete requests
rejected. Container lengths are 8,168 and 8,256 bytes, SHA-256 respectively
`1203710d33e39047fe1a50b90ff150e8066a270fe177cef9b5b062c5e1feb2ce` and
`18c9dd5497720be8fa8367a1837b99a019a988459fa83aac2de30dbb37e73346`.
These are observed process results, not emitted constants. The worker independently
checked all ten owned hashes, 62 actual dependency bindings and the raw
request/stdout/stderr/stream metadata against the root snapshot.

The sanitized [process receipt](../measurements/2026/SdkPlainPartPreparation01.json)
binds those exact sources and observations, retaining the first failed source
closure explicitly. The raw proof does not record the Python version; the receipt
does not infer it. The private recipe and generated fixtures are independently
authored inputs, not native saved content or a runtime fallback. No native or
held-out result is transferred into public writer admission by this process proof.

The CAD stopping conditions remain:

> The first is success under every criterion on this page.
> The second is the end of the available context.

This bridge is a concrete internal preparation component. Public writer admission,
default presentation policy, host-path policy and full CAD acceptance remain work.
