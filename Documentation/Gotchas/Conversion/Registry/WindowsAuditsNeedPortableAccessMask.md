# Windows file-open audits need a portable access mask

Windows CPython exposes `os.O_WRONLY` and `os.O_RDWR`. Its `os` module
lacks `O_ACCMODE`. An audit hook that assumes the POSIX name raises
`AttributeError` on the first file-open event, including ordinary
staged output creation.

Use `os.O_WRONLY | os.O_RDWR` as the fallback mask. It preserves the
read-versus-write check on the exact Windows interpreter and leaves
the SDK process separate from the CAD oracle.

[Windows process results](../../../../re/solidworks/measurements/2026/SdkDefaultAssemblyPublication01.json)
