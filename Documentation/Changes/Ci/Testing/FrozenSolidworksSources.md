# Hydrate frozen SOLIDWORKS writer sources before testing

Linux shards that replay a frozen SOLIDWORKS writer restore its pinned Git
blobs before starting pytest. They read the same checked inventories as the
existing tests and verify that every required object is available locally.
The setup step uses a read token in its temporary Git environment. The
checkout and test step run with credential persistence disabled.

A historical presentation test failed with HTTP 403 while fetching its
writer from a blobless checkout. The existing byte counts, source hashes
and held-out comparisons continue to govern replay.
