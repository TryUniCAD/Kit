# Archive depth counts open object bodies

At the maximum graph depth, a null or backreference can still terminate
the deepest body. Counting every tag visit as another body used to reject
those terminal tags.

Apply the limit to tags that open an object body and track the lifetime
of its body callback. The [depth process](../../../../../tests/Convert/Solidworks/ArchiveGraph/GraphDepthTests.py)
exercises both terminal reference kinds and the 129th-body rejection.
