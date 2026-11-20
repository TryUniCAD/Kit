# SOLIDWORKS 2026 KeyWords framing

| Delivery item | Scope |
| --- | --- |
| Task | `B03-SW2026-KEYWORDS-FRAME` |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-keyword-framing` |
| Prerequisite | [Accepted main](https://github.com/TryUniCAD/Kit/commit/e86bb3722f68e96cb5898aa1df06709e13e6a250) and the existing container and XML readers |
| Exit | Fresh-process authored framing, validation refusals, exact replay of disclosed controls, current-revision review and CI |

## Source pin

The original `FrameKeywords.py` matches the
[aggregate source](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/src/convert/adapters/solidworks/Archive/Construction/Metadata/FrameKeywords.py)
and the [88-file audit source](https://github.com/TryUniCAD/Kit/blob/5554733fde548afabdc6db221f387163d15e9497/src/convert/adapters/solidworks/Archive/Construction/Metadata/FrameKeywords.py)
byte for byte. Its source SHA-256 is
`8a487d9c9f5a18eb09438ebc26c9bd31ef40a12e95e44e642032b94a878634f0`.
Its one-file manifest SHA-256 is
`0fc16240b0a5be45846576ed7681c0f979ce2e8e3bb8579f4ea1472d059e45aa`.
The delivered framing file
[`FrameKeywords.py`](../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/FrameKeywords.py)
adds the carriage-return rule and guards the outer document boundary. Its source SHA-256 is
`62d04af2ee71dfa7671b01fe795b105c2d97e32e391e2bf348102fc69fa39523`.
The [named-tree serializer](../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/EmitKeywordXml.py)
has SHA-256 `8773e31df6072e6bdb2b671180f034f0f8a52dadfc71c5f130dabc9e1a27d370`.
The [name boundary](../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/CheckXmlNames.py)
has SHA-256 `754d19d4612a8163beaaf991d212ef94f3d1af3e1ef09d844035899882f5e3ef`.
The [tree comparison](../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/CheckXmlTree.py)
has SHA-256 `e25dd6b95c04b15edaa35e95c81fe9554c5dd2c94e8c6ab92994dbb32154f1d6`.
The [namespace expansion](../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/ExpandXmlName.py)
has SHA-256 `ffbb86416a2f1c662bcf29adabd54a5ba5608020578a37267911a25410e0adb8`.
The [parsed namespace scopes](../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/ReadXmlScopes.py)
has SHA-256 `6b7667ed58807d1f1f19b5157b0474ad8a7c6645b11624690005fe0fc2436c61`.
The [attribute comparison](../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/MatchXmlAttrs.py)
has SHA-256 `6ca4d48dc8b69ae24933ef542e627490750a5bbac4eba356b4b3e434d41b964d`.
The path-sorted seven-file manifest SHA-256 is
`8b4e01bdfbead601017799b34858644d8b05e22dc4d33ced1c5f1d4421e877e5`.
Each manifest hashes the repository-relative path followed by a NUL,
the lowercase file SHA-256 and a newline. The serializer uses the
standard-library `tostring` exposed by the repository's locked
`defusedxml` version, now declared as a runtime dependency. The final
payload passes the hardened XML parser after lexical rewriting. The
name boundary rejects delimiter characters and comment or processing
instruction starters in authored name tokens. The final tree is checked
against the authored tree with actual scoped namespace declarations.
Literal namespaces retain their lexical form. A generated prefix
collision that changes the parsed namespace fails before publication.

## Framing and serialization

The ordinary current model archive uses stream
`swXmlContents/KeyWords` in container format 4 and archive version
19000. The stream starts with byte `0x86`, the XML 1.0 declaration
with encoding `UTF-8` and CRLF. Its root is `Keywords` and the outer
stream closes with CRLF. The encoder emits UTF-8 without a BOM. The native outer CRLF owns the document boundary, and a nonempty root tail refuses before serialization.
The formatting argument selects either compact `/>` or spaced
` />` empty elements.

The [88-file comparison](https://github.com/TryUniCAD/Kit/blob/889fb6dffcad5ed3b0a065e07c21a53979a17be7/re/solidworks/records/KeywordCorpusFraming2026.md)
binds the exact-build research to 80 tracked parts and eight
assemblies. All 88 matched the compact lexical form, with two
CRLF pairs and no bare LF in the source streams under the original
framer. The
[numeric receipt](https://github.com/TryUniCAD/Kit/blob/889fb6dffcad5ed3b0a065e07c21a53979a17be7/re/solidworks/measurements/2026/KeywordCorpusFraming01.json)
has SHA-256
`3d364bb0779efc1076d4c1d89a472e0aac5835a628a0ca505cc6ea80e0cd1ce4`.
Its comparisons establish stream framing and XML reassembly.
Native field authority and feature-specific generation require
their own evidence.

In the installed CPython 3.14.7 source, `ElementTree._serialize_xml`
uses `_escape_attrib` for ordinary attribute values and
`_escape_cdata` for element text and tails. Both escape `>` as
`&gt;`. A literal ` />` in those values therefore becomes
` /&gt;` before the compact empty tag substitution. The local
stdlib module SHA-256 is
`9623c9e6c2f45c906fae8d4b221648a7efb8ac81bd4f6cd79c5eb2698fb015ef`.
Comment and processing-instruction text use separate branches and
are refused before serialization. The process cases exercise both node types in each framing mode. A separate case verifies byte identity for equivalent qualified name objects and expanded-name strings.
The generated XML also rejects NUL, other forbidden controls and
unpaired surrogates in attributes, text and child tails before either
mode publishes bytes.
[Namespace gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Metadata/KeywordNamespacesExpandOnRead.md)
[Empty tag gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Metadata/KeywordEmptyTagsFollowProfile.md)

XML 1.0 normalizes literal CR and CRLF before parsing. The framer
replaces each literal CR in the serialized payload with `&#13;`
before adding the outer CRLF pairs. For CRLF in ordinary text or
a child tail, the numeric reference precedes the original LF.
ElementTree already represents attribute CR and LF as `&#13;`
and `&#10;`, respectively. Those references survive the payload
substitution. [XML 1.0 end-of-line handling](https://www.w3.org/TR/xml/#sec-line-ends)
[Carriage-return gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Metadata/KeywordTextPreservesCarriageReturns.md)

## Disclosed controls and process exit

The existing disclosures have distinct logical stream hashes and
the following observed empty tag styles. Both have the exact
marker and declaration, two outer CRLF pairs, and zero literal
carriage returns inside the XML payload.

| Source | Origin | Source SHA-256 | Stream SHA-256 | Bytes | Empty tags |
| --- | --- | --- | --- | ---: | --- |
| [L1](../v2026/corpus/ladder/L1_boss.SLDPRT) | Native-authored part | `55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6` | `507f9c7c1b6c4a70ea1ab7fe4c3e66b4cbab6f46168dc5e1338c5710499a69ef` | 1,739 | 25 compact |
| [ConcaveOwned](../v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT) | Generated part with native observations | `fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33` | `067f823ee629cb6477d074d1177f65d5b8ca93843bb13c979b0a11ba02e55b28` | 1,306 | 19 spaced |

The [process worker](../../tooling/sw2026/CheckKeywordFraming.py)
uses the existing container reader and `Core.Native.ParseXml`
for disclosed replay. The [disclosed cases](../../../tests/Convert/Solidworks/KeywordFrames/KeywordSourceTests.py)
require exact bytes after reassembly with each observed style.
The [independent authored case](../../../tests/Convert/Solidworks/KeywordFrames/KeywordModelTests.py)
uses Unicode, XML special characters and the literal empty
delimiter spelling in an attribute, text and a tail. It also
authors a standalone CR and a CRLF sequence in each of those values.
Separate read and write processes check both lexical forms and
the recovered authored values. The
[refusal cases](../../../tests/Convert/Solidworks/KeywordFrames/KeywordRejectTests.py)
require that an incorrect root or non-boolean mode fails before
publishing bytes.

The two disclosed inputs were fingerprinted with a read-only
container inventory. Process execution on the extracted framer
awaits remote CI. Native document construction, rebuild and edit
acceptance have separate exits.

Scoped Black, Ruff, Mypy, Pyright and steering checks passed. The
donor scan found no recorded payloads across 3,270 production
sources. The fresh-process declarations were parsed as source.

The first merge candidate failed strict Pyright on its runtime tag
guard and dlint on the XML writer imports. The guard checks the
runtime tag as an object because the element type annotation does not
cover comments and processing instructions. The focused serializer
uses the approved XML package interface and introduces no scanner
suppression.
Scoped Pyright and dlint pass on the repair.
[Pyright run](https://github.com/TryUniCAD/Kit/actions/runs/44710841579)
[Scan job](https://github.com/TryUniCAD/Kit/actions/runs/44710841788/job/136201809268)
[XML serialization gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Metadata/KeywordXmlScannerDistinguishesWriter.md)
