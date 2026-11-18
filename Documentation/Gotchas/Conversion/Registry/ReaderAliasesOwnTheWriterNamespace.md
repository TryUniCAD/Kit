# Reader aliases also constrain canonical writer identities

An independently registered assembly writer might appear to need canonical format `solidworks.sldasm`. The existing SOLIDWORKS reader already registers that identifier as an alias of canonical `solidworks.sldprt`.

The shared registry owns one namespace for canonical formats and aliases across both directions. `CheckNamespace` rejects a new canonical writer whose format ID is already another format's alias. Separate reader and writer instances do not create separate alias namespaces.

Keep the existing canonical identity, give its writer the admitted assembly alias and destination extension, and dispatch document kinds within that writer. Preserve the reader's wider alias set and validate the writer's direction-specific metadata through `CheckPairInfo`. The default assembly integration follows that route and leaves the reader unchanged.

[Namespace owner](../../../../src/convert/adapters/registry/RegistryState.py) · [Exact registration evidence](../../../../re/solidworks/records/SdkAssemblyPublicRegistration2026.md)
