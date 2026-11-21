# Ordinary assembly Definition in the SDK archive codec

The ordinary version-19000 assembly Definition extends the accepted
part Definition codec with the assembly-specific untagged root and tail.
The dependency is the shared archive map and scalar, Base and Embed field
actions in [PR #205](https://github.com/TryUniCAD/Kit/pull/205). The Definition
has independent map base 1. Config, ResolvedFeatures, MatesList and component
placement use separate streams and owners.

## Native authority

The unchanged [assembly field trace](https://github.com/TryUniCAD/Kit/blob/ed0a90a0e8e913b4eb28f9c2dc6c92a814e32472/re/solidworks/records/AssemblyDefinition2026.md)
binds the `uiAssemblyDoc_c::Serialize` entry at `0x3f7aac20` and the inline
52-byte preferences serializer at `0x3f6a4400` to `sldasmu.dll` SHA-256
`05ab90ee7380335088505c47202137c63dbce18d7d516e7fd6703aee31d70390`,
build `34.5.2.0604`. The constructor independently binds the ten preference
slots and their domains. The assembly CLSID resolves the root before reading
its fields. Eight immutable, disclosed assembly sources at
`7d9e15658f5e2d19db2d2f6afe5a995c26ebc54a` corroborate the complete layout.
[Original source inventory](https://github.com/TryUniCAD/Kit/blob/ed0a90a0e8e913b4eb28f9c2dc6c92a814e32472/re/solidworks/measurements/2026/SdkModelDefinitionCorpus01.json)

The saved empty renderer profile is `(1, 0)` with zero objects on these
assemblies. The measured ordinary parts use `(6, 0)`. The current reader
retains the typed existing wrapper. Fresh authoring starts without it.
The construction code takes every save-as-part preference explicitly. It
packs the seven Boolean values into signed 32-bit words, keeps the two
finite doubles and signed long, and derives the `5fd` value by applying the
native `[0, 0.9]` clamp. The outer trailer fields come from the documented
initializer and field order. The read path preserves the parsed scalar
values and refuses an unsupported Boolean, fraction or renderer profile.

## Guarded proof

| Case | Definition bytes | Next map slot | Scope |
| --- | ---: | ---: | --- |
| Two distinct fresh settings | 549 / 548 | 7 | Exact prior independent encoding and independently packed inline preferences |
| Eight disclosed assembly saves | 3,900 each | 60 | Three distinct stream hashes, all typed slots retained and every byte replayed |
| Authored empty renderer | 559 | 7 | Only the inline marker and empty wrapper change |
| Sixteen refusal controls | varies | none | Wrong document kind or version, truncated or extra bytes, noncanonical tag, invalid preferences or renderer words |

Run `python3.14 -I -B re/tooling/sw2026/definition/ProveAssemblyDef.py` from
the checkout with the historical Git objects available. The supervisor
checks the original corpus and stream digests, then passes disclosed bytes
on stdin to guarded fresh readers. It independently packs the inline
preference tail for the two fresh outputs and checks their whole-stream
digests against the [prior independent serializer receipt](https://github.com/TryUniCAD/Kit/blob/ed0a90a0e8e913b4eb28f9c2dc6c92a814e32472/re/solidworks/measurements/2026/SdkModelDefinition01.json).
The fresh authors use only the explicit typed model inputs. Each authored
stream is checked by a separate process. A separate complete authored
stream adds the inline presence byte, signed words `(1, 0)` and native
zero count. Its reader checks the exact 11-byte frame, preserves the
surrounding graph and re-emits the whole stream. The same reader refuses
an ordinary part renderer word and an alternate second word. All 15 guarded
workers report zero runtime external access attempts. The `--generated`
mode is the same seven-process route used by the repository queue.
It requires only the checkout and an empty working directory.
[Exact receipt](../measurements/2026/OrdinaryAssemblyDefinition01.json) ·
[Queue integration](../../../tests/Convert/Solidworks/ArchiveDefinition/AssemblyDefTests.py)

The unchanged part procedure also reran against this checkout. Eight guarded
workers reproduced both fresh and both disclosed saved Definition outputs,
including the measured empty part renderer and twelve refusal paths.
[Accepted part procedure](SdkOrdinaryPartDefinition2026.md)

The installed research CLI decodes pinned SOLIDWORKS parts into neutral
document receipts. The archive-specific assembly Definition comparison
uses the version-pinned process command above. The result qualifies the
scoped stream codec. Native assembly composition, ownership of component
and mate graphs, public writing, and held-out and FCStd credit are tracked
separately in the parent programme.
