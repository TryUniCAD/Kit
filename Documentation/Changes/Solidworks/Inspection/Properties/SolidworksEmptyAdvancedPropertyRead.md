# Read empty advanced SOLIDWORKS part property owners

The ordinary SOLIDWORKS 2026 part reader admits the measured schema-one advanced property owner when its document, configuration and cut-list scopes are empty. It preserves the compatible literal summary and XML text projection and continues to report `unsupported` for populated or unknown advanced property state.

Call `open_document` normally and check that `metadata["solidworks.part_text_properties"]["status"]` is `complete` when qualifying literal text. The typed `Contents/CusProps` archive retains the actual ownership and serialized fields. Advanced property generation and populated advanced value projection remain outside this profile.

Six fresh SDK processes re-encoded six disclosed manager streams byte for byte. The source set includes both saves of two independently named designs, the compatible property control and the populated advanced control. The public process regression checks scoped literal text with a generated empty owner and rejects an unknown manager policy. [Field record](../../../../../re/solidworks/records/PartEmptyAdvancedProperties2026.md) [Readback receipt](../../../../../re/solidworks/measurements/2026/SdkPartPropertyManagerRead01.json)
