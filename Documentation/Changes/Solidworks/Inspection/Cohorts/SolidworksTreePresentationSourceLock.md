# Independent native tree-presentation sources

## Behavior and usage

`re/tooling/sw2026/TreeSourceSpecs.json` defines two new independent native
sources before the system-folder writer changes. They use different circle
parameters, Front/Top frames, mid-plane/two-direction end conditions and distinct
orthographic poses. Both remain held out from the next writer implementation.

The existing committed `AuthorViewCases.py` author creates each source through
the native API, measures its geometry, recursive feature tree and editable
dimensions, saves it and checks a fresh-process reopening. It also checks view
persistence and healthy controls. The job supplies this new specification path
and digest; it uses the existing `unseen-view-specs.v1` schema because all request
fields and authoring operations are unchanged.

The new evaluation scope is system-folder class, recursive order, captions and
parents. The source observer already records that complete tree inside its
geometry snapshot. Geometry and pose measurements remain controls; these inputs
do not retroactively add body or camera coverage to the completed cohorts.

Native files and detailed API observations must remain sealed until the new
presentation writer is frozen and its predictions pass the remote process
checks. Only the public source lock, hashes and batch health may be inspected
before then. Licensed software and native output remain outside checkouts.

## Verification and limits

The specification and author source were inspected statically. New native source
authoring is pending. No writer implementation, writer output, new feature
coverage, or native acceptance is established. No local tests ran. The production
adapter remains read-only.
