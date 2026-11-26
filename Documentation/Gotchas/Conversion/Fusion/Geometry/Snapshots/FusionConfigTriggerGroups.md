# Fusion configuration triggers keep their part names in the primary record

Each observed configuration serializer trigger stores two typed groups in one primary Design record. The derived trigger group establishes the table or rule role. Its `BlobSerializerTrigger` base group holds `partName`.

Generic constructor single-record drafting splits groups when their class spaces differ. Applying that rule to an independently authored configuration trigger placed `partName` in a continuation. The existing document configuration check rejected the output because it looks for `partName` in the primary trigger record.

The [configuration research generator](../../../../../Changes/Research/Encoder/FusionSavedConfigEnvelope.md) joins the two generated groups before encoding. It checks the exact two groups and their shared owner before using the existing writer. The general writer and reader keep their existing behavior.
