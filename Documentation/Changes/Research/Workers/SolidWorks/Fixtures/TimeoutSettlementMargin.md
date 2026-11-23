# Preserve controller time for Windows timeout fixtures

The Windows readback timeout fixture gives the controller four more seconds to accept the worker result.
The fixture increases its total deadline and shutdown grace by the same amount.
This keeps the worker and application request deadlines at their existing offsets.

The hosted cancellation fixture reported that the worker finished while the controller held no result.
The scenario now requires an accepted finish before reading the stored result and checking the application hold.
