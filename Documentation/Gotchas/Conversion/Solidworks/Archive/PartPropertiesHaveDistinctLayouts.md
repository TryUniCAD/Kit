# Part text properties can use distinct archive layouts

The native API can report the same text type from two property archive
layouts. An advanced-property save emits populated `Contents/CusProps`
lists beside the XML. A compatible save can preserve the document and
configuration text with an empty native manager and TypeID 0 XML rows.
Both layouts return API type 30 after native reopen.

Use the native manager and the XML owner together when admitting a
property layout. A missing configuration `FPVals` can still be valid for
ordinary literal text in the compatible layout. Follow its actual
document/configuration scope and compare the resolved value through a
native edit and fresh reopen when testing generated properties.

[Disclosed native evidence and bounds](../../../../../re/solidworks/records/PartPropertySources2026.md)
