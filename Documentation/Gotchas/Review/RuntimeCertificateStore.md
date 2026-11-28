# The pinned slim runtime has no system CA bundle

The model process reported `account service connection failed` after the pinned container built successfully in [run 46171251547](https://github.com/TryUniCAD/Kit/actions/runs/46171251547).
Successful npm package installation did not establish that the native model client could verify HTTPS certificates.
Node has bundled public authorities; the native client normally uses system roots.

Streaming and digest-verifying all layers of the pinned Linux image confirmed that `/etc/ssl/certs/ca-certificates.crt` is absent.
Export the authorities from the pinned Node binary into that file during the image build.
Set both `CODEX_CA_CERTIFICATE` and `SSL_CERT_FILE` to its absolute path.
Keep certificate verification enabled and preserve the immutable image pin.

The [official authentication guide](https://learn.chatgpt.com/docs/auth#custom-ca-bundles) documents the CA variables for login, HTTPS and secure WebSockets.
The local exporter smoke established verified TLS, not authenticated hosted model acceptance.
