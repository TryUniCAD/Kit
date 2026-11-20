# An ElementTree can serialize invalid XML characters

The element model accepts NUL and other characters outside XML
1.0's character range. Serialization alone can return invalid
bytes or invalid character references. Reparse the generated
keyword XML with the hardened parser before publishing the stream.
Validate both native framing modes after lexical rewriting. A
carriage return in a tag can behave as whitespace before rewriting
and become an invalid character reference afterward.
[XML 1.0 character production](https://www.w3.org/TR/xml/#charsets)
[Reproduced issue](https://github.com/TryUniCAD/Kit/pull/181#discussion_r4640968791)
