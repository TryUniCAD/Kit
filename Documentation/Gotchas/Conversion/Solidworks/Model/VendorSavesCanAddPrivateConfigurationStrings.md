# Vendor saves can add private configuration strings

The generated circle boss inputs contain authored public metadata. Saving those parts in the licensed application can add private short Unicode CStrings inside `Contents/CMgr` and `Contents/Config-0-ResolvedFeatures`, beyond the header/definition/biography streams admitted by the earlier discovery fixture preparer.

The first saved-circle preparation at source `1284bd4ed` stopped on CMgr before creating its destination. The next at `8895ffd8f` admitted CMgr and then stopped on resolved features. No original file changed and no archive schemas or tests executed. These preparation failures do not imply a CAD load or body failure.

Later preparation also found the `SW-Folder Name` property in `docProps/ISolidWorksInformation.xml` and the `swPath` attribute on the namespaced `swFile` element in `swXmlContents/Features`. The latter stream is XML despite having no `.xml` extension. Other streams below `swXmlContents/` must not be assumed to be XML from the directory name alone.

The shared framed-string redactor now has an optional `additional_metadata_streams` argument with an empty default. The separate saved-circle preparer explicitly admits those two streams for privacy-only, equal-width transformations. It records every changed span and hash, preserves stream lengths and still rejects private data outside supported CString/XML frames. Those two exact XML metadata contexts receive separately explicit rules, with equal-width raw UTF-8 text/attribute framing and recorded offsets/hashes. Unknown private attributes, unsupported escaping, XML entities and unread private contexts fail before output creation. Existing discovery membership and its default allowlist remain unchanged.

This preparation policy does not establish exact native field ownership or native acceptance for the modified fixture. Check complete archives and neutral geometry/parameter semantics independently in remote CI. Treat all prepared saved copies as vendor-derived reader inputs, never as generated writer outputs or runtime templates.

Saving also adds `SW-Folder Name` in `docProps/ISolidWorksInformation.xml`. It records the source directory as an XML `lpstr` property. The saved-copy preparer admits this exact stream/property pair through an optional metadata-property argument; the generic XML default remains unchanged. Private property names in diagnostic errors are represented by hashes. Qualified CAD dimension names still require the existing whole-frame exception and never suppress account/home-path matching.
