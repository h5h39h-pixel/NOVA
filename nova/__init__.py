"""Nova — AI Control Center application package.

Layering (a strict dependency DAG, no cycles):

    config            paths / endpoints (portable, config.json)
      ^
    nova.core.db      SQLite: connection, schema, settings, history
      ^
    nova.core.events  WebSocket bus: push() broadcast to dashboards
      ^
    nova.core.jobs    process supervision (ProcMgr + Job Object)   [future]
      ^
    nova.services.*   audit, notifications, webhooks, metrics ...  (business logic)
      ^
    nova.api.*        FastAPI routers (HTTP/WS surface)            [future]
      ^
    server.py         thin composition root: builds the app, wires lifespan

Rule: a lower layer never imports a higher one. Services depend on core; the API
depends on services + core; nothing depends on server.py.
"""
