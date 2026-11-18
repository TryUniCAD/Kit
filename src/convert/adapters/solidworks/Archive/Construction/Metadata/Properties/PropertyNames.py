# native ordinary part document property roots use separate xml namespaces for their distinct owners
KModelPropertyNamespace = (
    "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
)

# the active configuration property dom uses its own vocabulary even with identical text fields
KConfigPropertyNamespace = "http://www.solidworks.com/config-properties"

# the document summary section uses the published standard property set identity
KSummaryPropertyFormat = "{D5CDD502-2E9C-101B-9397-08002B2CF9AE}"

# native core property editing requires the declared file summary vocabulary
KSummaryNamespaces = {
    "xmlns:cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "xmlns:dc": "http://purl.org/dc/elements/1.1/",
    "xmlns:dcterms": "http://purl.org/dc/terms/",
    "xmlns:dcmitype": "http://purl.org/dc/dcmitype/",
    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

# file summary fields use the native element names and authoring order
KSummaryTags = {
    "title": "title",
    "subject": "subject",
    "author": "creator",
    "keywords": "keywords",
    "comments": "description",
}
