# Keyword namespace names expand on read

A literal `xml:lang` or declared prefixed attribute reads back
with its namespace URI and local name. A lexical `xmlns` declaration
becomes a namespace binding outside the parsed attribute map.

Check authored name token boundaries before serialization. Check the
final XML for validity after framing. Compare each parsed name to its
authored namespace, using the declarations in scope at that node. An
explicit descendant declaration can shadow an automatically emitted
prefix, including `ns0`. A typed QName attribute value is serialized as
a prefix and local name. Expand that value using the parser's namespace
events at the actual attribute location. Ordinary string values retain their
exact text. A changed namespace stops publication.
[Literal namespaces](../../../../../../tests/Convert/Solidworks/KeywordFrames/KeywordNamespaceTests.py)
[Shadowed declaration](../../../../../../tests/Convert/Solidworks/KeywordFrames/KeywordShadowTests.py)
[Qualified attribute values](../../../../../../tests/Convert/Solidworks/KeywordFrames/KeywordAttrTest.py)
