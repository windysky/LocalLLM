# Admin Dashboard Button Errors – Investigation Summary

## Problem
- In `web/admin.html`, the model action buttons (Load/Unload/Remove) intermittently fail with `ReferenceError: loadModel is not defined` (and similarly for other actions). Earlier, the page also threw `Unexpected end of input` syntax errors.
- Models list renders, but the inline button handlers sometimes cannot find the global functions.
- A missing favicon at `/favicon.ico` returns 404 (cosmetic).

## What’s been tried
- Multiple rounds of brace/scope fixes to clear the syntax error at the end of the `<script>` block.
- Verified the backend `/api/models` endpoint returns data; issue is purely front-end scope/syntax.
- Searched for function definitions and ensured they are declared (`async function loadModel(...)` etc.) around lines ~970.
- Attempted exporting functions to `window.*` explicitly; ran into extra/duplicate braces causing scope breakage.
- Extracted the `<script>` content and used `node --check` and custom parsing to confirm syntax; traced an extra unmatched opening brace and removed it.
- Added explicit `window.*` assignments and a console log to report function availability.
- Added fallback definitions at the end of the script: if any of `window.loadModel`, `window.unloadModel`, or `window.removeModel` is still undefined, lightweight versions are attached to `window` that call the respective API endpoints and refresh the model list.
- Tested script parsing with `node --check` after each fix to ensure no syntax errors.

## Current state
- `web/admin.html` now parses cleanly (no syntax errors).
- Functions are attached to `window.*` and fallbacks are in place, but browser confirmation is still needed to ensure the console reports all functions as `function` and that the buttons execute correctly.
- Favicon 404 remains a cosmetic issue.

## Next steps
1. Hard-refresh the Admin Dashboard (Ctrl+F5) and confirm console shows all functions as `function` and buttons work.
2. If globals are still undefined, consider moving all JS into a dedicated file (e.g., `web/admin.js`) and including it with a single `<script src>` to avoid inline scope/brace drift.
3. Add a small favicon at `web/favicon.ico` (or point to `data:,`) to remove the 404 noise.
