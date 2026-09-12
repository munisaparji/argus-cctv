# API reference

Start the local API with `python -m argus.cli serve`. Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`. The checked-in `apps/console/openapi.json` generates the TypeScript client types with `npm run types`.

| Method and path | Purpose |
| --- | --- |
| GET /api/health | Read service status and version |
| GET /api/incidents | List persisted incident records |
| GET /api/incidents/{id} | Read a complete incident |
| POST /api/incidents/{id}/decision | Confirm or dismiss with operator and note |
| GET /api/audit | Read the chronological decision audit |
| GET /api/config | Read the 13 factors and 12 allowed actions |
| GET /api/metrics | Read measured sample and existing research results |
| GET /api/annotations?annotator=name | Resume that local annotation session |
| PUT /api/annotations | Save or complete an independent annotation |
| GET /api/adjudication | Read completed annotations for comparison |
| GET /api/media/{relative_path} | Serve allowed sample, evidence or registered video files |
| WS /api/runs/{sample_clip_id} | Execute a sample and stream stage progress |

## Decision body

```json
{"decision":"dismiss","operator":"reviewer-1","note":"Evidence insufficient after review"}
```

The identifier must exist. Dismissal requires a note. A decision can occur once. Invalid input returns 422, a missing incident returns 404, and an already-decided record returns 409. Decision and audit insert share one database transaction. The record's recommended action set is logged, but the API never performs those actions.

## WebSocket events

Stage messages contain `module`, `status`, timing and the current record where available. The terminal message has `status: finished` and the completed record. An error message uses `status: error` and a descriptive `message`. Research model execution is intentionally a CLI batch workflow; the interactive WebSocket accepts bundled sample IDs.

## Local trust boundary

The service binds to loopback by default. Browser writes and sockets accept only the documented local ports. These origin checks reduce cross-site requests but do not provide authentication. Local clients without an Origin header can use the API. Session names are labels, not authenticated accounts. Network deployment requires its own authentication and authorization design.

The media endpoint resolves paths, checks permitted locations or exact registered video paths, and restricts file extensions. SQLite triggers prevent ordinary update or delete statements against audit rows. A database owner can still alter the database; this is an application audit trail, not immutable external storage.

