# Roadmap

## Completed

- ~~Gmail tools (search, get, send, labels)~~
- ~~Drive tools (search, list, get, create, delete, trash, share, permissions)~~
- ~~Sheets tools (list, get, update, append, create, metadata)~~
- ~~Calendar tools (list, get, create, update, delete events)~~
- ~~Docs tools (search, get, create, modify, append text)~~
- ~~Tasks tools (list, get, create, update, delete, complete)~~
- ~~Forms tools (get form, get responses, create, add questions)~~
- ~~Apps Script tools (projects, deployments, versions, processes, run functions, triggers)~~
- ~~OAuth 2.1 with PKCE (zero GCP project required, clasp-based)~~
- ~~PyPI package publishing (v0.6.0)~~
- ~~Desktop Extension (DXT) for one-click install~~
- ~~45 unit tests with mocked APIs~~

## Near-term

- Google Slides API (create, read, update, manage presentations)
- Google Contacts API (CRUD contacts and contact groups)
- Least-privilege OAuth scopes (minimum required scopes per tool)
- Structured logging and error handling (consistent JSON logging, actionable error messages)
- Retry with exponential backoff for transient API failures

## Medium-term

- Rate limit management and quota awareness (proactive throttling, per-user tracking)
- Integration test suite (sandboxed tests against real Google APIs)
- Admin SDK Directory API read-only (user and group lookups for org context)
- Docs API enhancements (comments, suggestions, document review workflows)

## Long-term

- Connection pooling for Google API clients (reduce overhead in high-throughput scenarios)
- Observability and metrics (server health, tool usage, API call latency)
- E2E agent testing framework (validate full agent-to-MCP-to-API workflows)
