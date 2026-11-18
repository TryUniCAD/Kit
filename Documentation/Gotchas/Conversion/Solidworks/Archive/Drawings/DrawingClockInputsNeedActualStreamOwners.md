# Drawing clock inputs need actual stream owners

The ordinary part constructor emits a configuration-manager header with its own save timestamp. Applying that same clock input shape to every linked drawing invents an owner.

The frozen linked drawing family emits seven streams and has no independent `Contents/CMgrHdr2`. Its self-file and inline/top header clocks are real owners; a separate drawing manager-header save time is not represented by this constructor.

Omit that unused drawing-only experiment input explicitly. Keep the linked child's actual manager-header timestamp separate and preserve its real directory aliases. Do not infer a manager save time from the drawing self save event or silently discard a source value that needs an unsupported owner.

The [experiment record](../../../../../../re/solidworks/records/DrawingSourceEpochExperiment2026.md) preserves the initial proposal and its explicit input-shape correction. This finding does not qualify broader drawing metadata writing.
