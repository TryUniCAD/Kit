# Direction readback needs explicit UTF-8 output

The strict SDK JSON retains the source path. A child process that prints that JSON may use the Windows legacy code page. A parent that expects UTF-8 can then receive invalid bytes or no document.

The P03 archive read reproduced `UnicodeEncodeError` with a Greek omega in its path and a forced cp1252 text stream. Writing the codec output as UTF-8 bytes to the child pipe returned the exact path and native file digest under the same locale setting. The maintained test uses a non-ASCII path and forces cp1252 inside the isolated child. [Direction ownership evidence](../../../../Changes/Research/Readers/Comparison/ConstrainedBossDirectionOwner.md)
