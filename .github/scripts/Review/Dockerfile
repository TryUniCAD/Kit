FROM node:22-bookworm-slim@sha256:be979e5523c76fa4d5ca4ebd3099078f220aa47ec39c48ad5b5df9314debd6eb
COPY Runtime/WriteTrust.cjs /opt/kit-review/WriteTrust.cjs
RUN node /opt/kit-review/WriteTrust.cjs /etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt CODEX_CA_CERTIFICATE=/etc/ssl/certs/ca-certificates.crt
RUN npm install --global --ignore-scripts @openai/codex@0.171.0
