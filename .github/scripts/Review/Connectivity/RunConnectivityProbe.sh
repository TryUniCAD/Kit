#!/usr/bin/env bash
set -euo pipefail
readonly KProbeSource="$1"
docker build --tag kit-review-runtime .github/scripts/Review
docker run --rm --read-only \
  --user "$(id -u):$(id -g)" --cap-drop=ALL \
  --security-opt=no-new-privileges --pids-limit=128 \
  --memory=4g --cpus=2 --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  --interactive --env HOME=/tmp --workdir /tmp \
  kit-review-runtime node --input-type=module - < "$KProbeSource"
