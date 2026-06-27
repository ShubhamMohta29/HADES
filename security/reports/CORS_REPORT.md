# CORS Security Report

## Status: N/A

## Findings

HADES has no HTTP server and no CORS configuration. The pywebview bridge is a local IPC mechanism, not a cross-origin HTTP endpoint.

## Recommendations

N/A. If an HTTP API is added, set CORS origin to an explicit allowlist — never `*` with `credentials: true`.
