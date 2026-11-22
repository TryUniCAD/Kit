# Reader and writer format registration

One format can register a writer for a subset of its reader's extensions,
aliases, and capabilities. The catalog keeps the full reader metadata.
An output request must resolve to a name advertised by the writer.

When reading and writing use different names, the JSON format listing
includes `write_extensions` and `write_aliases`. The terminal listing
shows the writable extensions in a separate column in the same case.

The API check writes and reads an authored JSON document across both
registration orders. It also verifies that the read-only alias refuses
publication and that replacing either adapter preserves its peer's names.
