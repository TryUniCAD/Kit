# A saved child model name can contain its full file path

The `swName` attribute on the `swModel` element of `swXmlContents/Features`
can contain the full shared-folder path after saving a child through the
parent session. Expecting only the document title leaves private metadata
in otherwise prepared fixtures. Both synchronized discovery children used
an absolute path there.

The child preparation allows same-width redaction in that exact XML attribute
only after verifying that it identifies the expected owned child. All other
unclassified fields still fail preparation. This changes research fixture
metadata; it supplies no writer value or output template.
