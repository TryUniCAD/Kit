# Fetch frozen Git blobs without commit negotiation

The complete-suite frame test restores pinned historical Python files in a partial checkout. The default Git negotiation failed on the same 232 missing blob IDs in two hosted audits. A fresh blobless clone reproduced the `bad revision` and missing-objects errors.

Set `fetch.negotiationAlgorithm=noop` on the single fetch for those blob IDs. The restore still checks the frozen tree, object types, lengths and SHA-256 digests before executing any source. [Git fetch configuration](https://git-scm.com/docs/git-config#Documentation/git-config.txt-fetchnegotiationAlgorithm)
