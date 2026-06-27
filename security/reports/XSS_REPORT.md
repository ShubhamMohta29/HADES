# XSS Security Report

## Status: LOW

## Findings

Three JS functions render content into the DOM:

**`addMessage(who, text)` — SAFE ✅**
```js
div.innerHTML = '<span class="time">' + timeStamp() + '</span><span class="who">'
               + who + ':</span> ' + escapeHtml(text);
```
`text` (the AI/user message body) is passed through `escapeHtml()`. The `who` parameter is always either `"You"` or `"Hades"` — hardcoded strings from Python, never user input. ✅

**`addSystemMessage(text)` — SAFE ✅**
```js
div.textContent = "— " + text + " —";
```
Uses `textContent`, not `innerHTML` — browser never parses the value as HTML. ✅

**`addHelpCard(html)` — PATTERN RISK ⚠️**
```js
wrapper.innerHTML = html;
```
Uses `innerHTML` directly. Currently safe because `html` is sourced from `HELP_HTML` in `commands/help.py`, which is a hardcoded Python constant (not derived from user input). However, the pattern is dangerous: if `addHelpCard` were ever called with user-generated content, XSS would result immediately.

**`escapeHtml()` implementation — COMPLETE ✅**
```js
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, function(c) {
    return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];
  });
}
```
Escapes all five dangerous characters. ✅

**Python → JS injection safety** (`gui.py`):
All `evaluate_js()` calls use `json.dumps()` to serialize Python values:
```python
self._js(f"window.addMessage({json.dumps(who)}, {json.dumps(text)});")
self._js(f"window.addSystemMessage({json.dumps(text)});")
self._js(f"window.addHelpCard({json.dumps(html)});")
```
`json.dumps()` correctly escapes quotes, backslashes, and control characters, preventing injection through the Python→JS bridge. ✅

## What's at risk

If `addHelpCard` were ever refactored to accept user-supplied content (e.g., note previews, AI-generated HTML), the raw `innerHTML` assignment would enable stored XSS within the pywebview window.

## What's already secure

- User message content protected by `escapeHtml()`
- System messages use `textContent`
- Python→JS bridge uses `json.dumps()` for all values
- `HELP_HTML` is a hardcoded constant, never user-derived

## Recommendations

1. (LOW) Add a comment above `addHelpCard` in `index.html` noting that it must only be called with trusted, hardcoded HTML — never with user-generated content.
2. (INFO) If HADES ever renders user notes or AI responses as rich HTML, route them through `addMessage` (which uses `escapeHtml`) rather than `addHelpCard`.
