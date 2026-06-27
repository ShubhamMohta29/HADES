# CSRF Security Report

## Status: N/A

## Findings

HADES is a local desktop application. It has no HTTP server and does not set session cookies. The pywebview window communicates with Python via a local IPC bridge (`window.pywebview.api`), which is not accessible from any web origin.

CSRF requires a browser that can make cross-origin requests to a server that uses cookie-based sessions. Neither condition applies here.

## Recommendations

N/A. If a web-facing API is added in the future, implement `SameSite=Lax` on session cookies or require CSRF tokens on all state-changing endpoints.
