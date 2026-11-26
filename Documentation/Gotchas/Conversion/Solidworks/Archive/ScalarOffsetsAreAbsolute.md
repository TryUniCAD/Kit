# Scalar offsets are absolute

Python's `struct.unpack_from` interprets a negative offset relative to the
buffer end. The archive reader returns the next offset from the buffer
start. Passing `-4` into an i32 read used to read the last four bytes and
return zero as the next position.

Pass an absolute byte offset from the start of the buffer. The
[scalar reader](../../../../../src/convert/adapters/solidworks/Archive/Scalars/ReadScalar.py)
rejects a negative offset before decoding the field.
