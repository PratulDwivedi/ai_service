# Streaming and Normal Responses

This document explains how to use the Chat API in two modes:

- Normal (non-streaming) JSON responses (default)
- Streaming responses (Server-Sent Events / SSE) for progressive UI updates

## API: `/api/chat/query`

Supports both modes via the `stream` query parameter (boolean).

- Normal: `POST /api/chat/query` (default)
  - Returns full JSON response modeled by `ChatResponse`.
  - Use this for API clients that expect a single immediate response.

- Streaming: `POST /api/chat/query?stream=true`
  - Returns `text/event-stream` SSE.
  - The response yields incremental `data:` events with the following shapes:
    - Partial text chunks: `{"partial": "..."}`
    - Final message chunk: `{"final": "..."}`
    - Final payload: `{"done": true, "message": "...", "query": "...", "data": [...], "count": N}`
  - Use this for web UIs to show progressive LLM output.

### Example: Normal request

```bash
curl -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -X POST http://localhost:8001/api/chat/query \
  -d '{"table_name":"assets","message":"How many assets per category?"}'
```

### Example: Streaming request (curl)

```bash
curl -N -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -X POST "http://localhost:8001/api/chat/query?stream=true" \
  -d '{"table_name":"assets","message":"How many assets per category?"}'
```

Note: `curl -N` keeps the connection open and prints streaming chunks.

### Client Recommendations

- Browser UI: use `fetch()` with a `ReadableStream` to include `Authorization` header, then parse lines and handle SSE-like `data:` lines.
- If you want native `EventSource`, you must use cookie-based auth or a proxied endpoint (EventSource doesn't support custom headers).
- Mobile/native apps: use streaming request and append partials to UI until `done: true` payload arrives.

### Server behavior

- The server still executes the SQL and queries DuckDB immediately to obtain results.
- It then streams LLM partials for a user-friendly summary while the UI updates.
- The final SSE payload contains the complete JSON (same structure as normal response) so the client can update its state.

## Security and Limits

- Streaming uses your `OPENAI_API_KEY` and may incur additional cost.
- The server limits sample rows sent to the LLM to avoid token explosion.
- Add rate limiting in production to prevent abuse.

---

For examples of `fetch()` usage in the browser, see `TESTING_GUIDE.md` (appendix).