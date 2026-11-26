# Deep Git alternate stores block a shared sparse checkout

A new shared clone can point to the object store of a prior dependent clone. Each earlier clone can refer to another store. When this chain grew too deep, Git reported `ignoring alternate object stores, nesting too deep` and refused to read the pinned base tree.

Read the existing alternate paths and verify each object directory. For the new isolated checkout only, list the same verified stores directly in `.git/objects/info/alternates`. Put the original store first, then each dependent store in order. Separate entries with LF. CRLF made Git read a carriage return as part of the Windows path and refuse it.

Run `git cat-file -e` against the pinned tree before switching to the new sparse branch. In the P03 native-plan checkout, this resolved the complete base tree and hydrated the requested paths. The original object stores and branches stayed intact.
