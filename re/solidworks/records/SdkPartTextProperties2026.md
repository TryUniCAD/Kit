# Generate ordinary SOLIDWORKS part text properties

Task B04-SW2026-PARTPROPS, owner `/root`, PR #121.

The [native property field measurement](PartPropertySources2026.md) binds
the separate summary, document and configuration owners to SOLIDWORKS
2026 SP05.2. The internal SDK part composer accepts optional typed
`PartTextInput` settings and emits the compatible one-configuration
text profile. Summary, document custom text and configuration custom text
each have an independently generated stream.

| Field | Owner and construction |
| --- | --- |
| Title, subject, author, keywords, comment | The supplied summary fields generate the corresponding `dc` elements in `docProps/core.xml`. |
| Document text and evaluated value | Each supplied literal generates one independent value row and its equivalent evaluated text in `docProps/custom.xml`. |
| Active configuration text | The supplied active-configuration properties generate `docProps/Config-0-Properties.xml`, including their ordinary literal values and lookup dictionary. |
| Names and lengths | Each emitted bag derives fresh property IDs from order beginning at 3. Its name dictionary sorts the actual input keys and preserves the assigned IDs. |
| Container and XML framing | The shared archive writer derives counts and stream locations. The XML defines the literal native namespace prefixes and reserved dictionary keys. |

The two disclosed neutral cases exercise a triangle and a translated analytic
circle. Both contain a property name that independently exists at document
and configuration scope. The isolated composer produces 9,646 and 10,050
bytes, each with thirteen streams. Four original guarded builds and two
subsequent frozen-source builds reproduce the exact candidates from the
neutral requests with zero runtime input reads.

The [native lifecycle](../measurements/2026/SdkPartPropertyNative01.json)
verifies that both scopes open with their intended editable text and that a
document edit leaves the configuration value unchanged. It then edits the
configuration value and checks the document value again. Both cases save
and reopen with all edits, the authored summary, the actual feature tree and
the same geometry. Six distinct processes pass, including both controls.
The trial contains 76 numerical comparisons and checks both saved XML scopes
against the observed edited values.

The original native-tested source snapshot contained 5,025 files.
Its manifest SHA-256 is
`8b01c85de2917cda2cc886522d38f669b8af71d91755ec3029388d7fead6633e`.
The [promotion replay](../measurements/2026/SdkPartPropertyPromotion01.json)
calls the SDK part factories in four more isolated processes and matches
the independent prototype and native-tested bytes exactly. Eight invalid
requests reject per process. Empty property inputs preserve the original
ten-stream files byte for byte.

The measured scope is ordinary literal text. Other variants, configuration
sets, populated advanced property generation and source-specific
provenance remain open. The current public writer admission remains within
its qualified ordinary part profile.
