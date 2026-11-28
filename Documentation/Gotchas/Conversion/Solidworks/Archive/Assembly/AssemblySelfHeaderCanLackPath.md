# A native assembly self header can lack its locator

The A20 and A21 originals store a nonempty model name and selected configuration in both self headers, with an explicitly empty Unicode `shared.h18` path. The same document's instance tree carries the actual assembly file path. Consequently the ordinary file-key helper that requires nonempty path text cannot read those original self references as complete file identities.

Bind the model name and active configuration from the actual binary owners, and use the matched instance-tree file row for original external identity. The generated bundle takes its new explicit target locator from the generation request. Keep the original absent header path under source custody. [Hash-bound source and generated comparison](../../../../../../re/solidworks/records/SdkPlanarAssemblyIdentity2026.md)
