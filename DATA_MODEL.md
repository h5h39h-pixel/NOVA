# Data Model — Nova / AI Control Center

SQLite database at `<workspace>/data/control.db` (single file; the only persistent store).
Schema is created/migrated by `nova/core/db.py` → `init_db()` + `run_migrations()`.
Current `SCHEMA_VERSION = 1`.

## Tables

### `settings` — key/value app config
| column | type | notes |
|---|---|---|
| key | TEXT PK | setting name |
| value | TEXT | JSON-encoded value |

Seeded from `DEFAULT_SETTINGS` (mode, default models, accent, auth_*, lan_access,
allow_remote_exec, lite_visuals, webhook_*, metrics_interval, …). Secrets: `auth_token_hash`
(SHA-256), `cloud_api_key` (plaintext — see SECURITY.md). Never returned raw by the API.

### `conversations` — chat threads
| column | type | notes |
|---|---|---|
| cid | TEXT PK | conversation id (12-hex) |
| project | TEXT | grouping label (default "General") |
| title | TEXT | shown in the sidebar |
| created / updated | REAL | epoch seconds |
| archived | INTEGER | 0/1 |
| tokens | INTEGER | running token estimate |

### `chat` — messages (child of `conversations`)
| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| ts | REAL | epoch |
| cid | TEXT | → conversations.cid (FK by convention, not enforced) |
| session_id | TEXT | server-run id |
| role | TEXT | user / assistant |
| content | TEXT | message body |
| model_used | TEXT | model that produced it |

### `kb_docs` — knowledge-base documents
| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | filename |
| chunks | INTEGER | chunk count |
| created | REAL | epoch |

### `kb_chunks` — embedded chunks (child of `kb_docs`)
| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| doc_id | INTEGER | → kb_docs.id |
| ord | INTEGER | chunk order |
| text | TEXT | chunk text |
| emb | TEXT | JSON float[] (nomic-embed-text, 768-d) |

### `training_runs` — fine-tune history
| id, started, ended (REAL) · ok (0/1) · steps · base · learned · combined (INTEGER) · note (TEXT) |

### `schedules` — automations
| id · name · action · params (JSON TEXT) · interval_sec · next_run (REAL) · enabled (0/1) · last_run · last_status · created |

### `workflows` — multi-step pipelines
| id · name · steps (JSON TEXT) · created · last_run · last_status |

### `history` — terminal/action history
| id · ts · command · exit_code · duration (REAL) · output · source |

### `notifications` — notification center
| id · ts · level · title · body · seen (0/1) · category · link |

### `audit` — security/action audit trail
| id · ts · actor · action · detail · status |

### `bug_reports` — in-app issue tracker
| id · ts · title · detail · severity · status (open/closed) · page · logs |

### `metrics_history` — system telemetry trend (observability)
| id · ts · cpu · ram · gpu_util · vram_used · vram_total · gpu_temp (REAL) — ~30s spacing, last ~2880 rows |

### `schema_version` — migration bookkeeping
| version | INTEGER | current applied schema version |

## Relationships (logical; SQLite FKs not enforced)
```
conversations 1──* chat        (chat.cid → conversations.cid)
kb_docs       1──* kb_chunks    (kb_chunks.doc_id → kb_docs.id)
```
All other tables are independent logs/registries. Backups: full JSON bundle via
`/api/backup`; daily binary snapshots in `<workspace>/data/backups/` (see SECURITY.md).
