# Strict generated blank drawing profile

The strict reader supports one canonical SDK-generated blank drawing with archive version 19000. It reconstructs complete typed drawing options, UI settings, header/history provenance and self-file identity, then requires exact equality for all seven streams and the whole container.

The normal SDK call is `open_document(source, source_format="solidworks.slddrw", strict=True)`. A successful document retains its reconstructed native semantic input under `source.attributes["solidworks.blank.intent"]`; all source attributes survive document JSON round-trip. Physical sheet dimensions come from the typed sheet owner, while XML-derived dimensions are checked independently.

The profile is one unformatted ANSI A landscape sheet, integral positive scale terms and the existing fresh standard-1 style constructor. There are no model links, views, geometry, annotations, extra properties, populated telemetry or arbitrary native saved state. Unsupported content refuses. `strict=False` keeps the existing partial-reader warning and behavior.

Source presentation and chronology must not be stripped to pass writer admission. The existing public writer deliberately refuses the preserved native attributes. Public rewrite integration, general native author/saved sources and new target-application qualification are separate remaining work. [Implementation and evidence](../../../../../re/solidworks/records/SdkGeneratedBlankStrictReader2026.md)
