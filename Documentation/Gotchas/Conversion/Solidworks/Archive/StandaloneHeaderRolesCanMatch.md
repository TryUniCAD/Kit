# Standalone header roles can contain identical bytes

The L1 part has equal logical bytes in `Header2` and
`Contents/Config-0-ModelHeader`. A replay of that part can succeed even
if a selector substitutes one stream for the other.

Include a contrast whose role digests differ and check each named
digest independently. The [ConcaveOwned process case](../../../../../tests/Convert/Solidworks/ArchiveHeader/HeaderRoleTests.py)
uses an existing tracked control for that comparison.
