# SQLite

GUI and CLI use tasks.db in the user data directory. Tasks, tag catalog and
audit records share one database. Each command begins an immediate transaction,
reloads current tasks, writes changes and commits before emitting events.
WAL and a ten-second busy timeout coordinate independent connections.
The GUI polls external task changes every second.

On first opening a database, sibling tasks.json, tags.json and audit.log.jsonl
are imported atomically. Sources are preserved and a marker prevents reimport.
Malformed input aborts migration. A legacy --file tasks.json selects tasks.db.
Copy portable legacy files to the user data directory before first launch.
JSON repositories remain for compatibility tests; runtime storage is SQLite.
CLI output remains JSON. Dry-run audit records are stored in SQLite.

Concurrent commands preserve unrelated tasks. Two edits of the same field
still use the last submitted value; dialog conflict detection is future work.
