# Fusion legacy appearance resources can sit outside the package resource tree

The M068 control has two enabled legacy appearance connections. Both resolve to a bitmap asset, even though its package has no Resources tree. It retains the scalar and colour fields next to the connections. A missing resource folder cannot establish an untextured appearance.

The legacy descriptor also lists separate user-interface and renderer implementation resources. The observed paths have no matching file in either ZIP archive in the 25 studied Fusion files. Their native resolver and requiredness still need evidence. The SDK's schema selection uses the presence of the UI declaration, while its typed loader can read the stored property values without opening that resource.

The [legacy property streams producer](../../../../Changes/Research/Encoder/FusionLegacyPropertyStreams.md) accepts explicit absent connections and leaves those resource and catalog bindings outside its scope.
