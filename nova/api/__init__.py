"""API layer — FastAPI routers grouped by domain. Each imports only from nova.* + config
(never from server.py), and is included by server.py via app.include_router(). This is the
target home for all routes as they're extracted from the monolith, one group at a time."""
