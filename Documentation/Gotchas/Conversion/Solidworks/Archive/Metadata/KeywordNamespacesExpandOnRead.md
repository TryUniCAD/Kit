# Keyword namespace names expand on read

A literal `xml:lang` or declared prefixed attribute reads back
with its namespace URI and local name. A lexical `xmlns` declaration
becomes a namespace binding outside the parsed attribute map.

Check authored name token boundaries before serialization. Check the
final XML for validity after framing. Preserve literal namespace
declarations and prefixed names inside the ordinary native root.
[Paired framing cases](../../../../../../tests/Convert/Solidworks/KeywordFrames/KeywordNamespaceTests.py)
