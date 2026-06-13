# Command Contract

这是未来 CLI / AI / MCP 调用任务能力时应遵守的 command 契约。当前代码已经实现 Python dataclass command；本文档用于约定未来 JSON 或工具调用格式。

## 统一结果

每次写操作都返回 `CommandResult`：

```json
{
  "ok": true,
  "message": "Task added",
  "changed": true,
  "would_change": false,
  "task_id": "task-id",
  "preview": {},
  "data": {},
  "events": []
}
```

字段说明：

- `ok`：命令是否执行成功。
- `message`：给调用方看的简短结果。
- `changed`：是否改变了任务数据。
- `would_change`：dry-run 时表示如果真正执行是否会改变数据。
- `task_id`：主要影响的任务 id，没有时为 `null`。
- `preview`：dry-run 时返回的预览信息。
- `data`：附加数据，未来 CLI/MCP 应保持 JSON 可序列化。
- `events`：执行过程中产生的应用事件。

## CommandContext

未来 CLI / AI / MCP 调用 command 时应传入上下文：

```json
{
  "source": "cli",
  "dry_run": false,
  "request_id": null,
  "actor": null
}
```

推荐 source：

- `ui`
- `cli`
- `future_ai`
- `test`

安全规则：

- `future_ai` 来源的删除操作必须先 `dry_run=true`。
- CLI 删除任务必须显式 `--confirm` 或 `--dry-run`。
- dry-run 不写入 repository，不发布事件，只返回 preview 并写 audit log。

## Commands

### AddTask

```json
{
  "type": "AddTask",
  "title": "写周报",
  "description": "",
  "due_date": "2026-06-09T18:00",
  "has_time": true,
  "reminder_minutes": 30,
  "quadrant": "q1"
}
```

### UpdateTask

```json
{
  "type": "UpdateTask",
  "task_id": "task-id",
  "title": "写周报",
  "description": "补充项目进展",
  "due_date": null,
  "has_time": false,
  "reminder_minutes": null
}
```

### DeleteTask

```json
{
  "type": "DeleteTask",
  "task_id": "task-id"
}
```

### MoveTask

```json
{
  "type": "MoveTask",
  "task_id": "task-id",
  "new_quadrant": "q2"
}
```

### CompleteTask

```json
{
  "type": "CompleteTask",
  "task_id": "task-id"
}
```

### ReopenTask

```json
{
  "type": "ReopenTask",
  "task_id": "task-id"
}
```

### CheckReminders

```json
{
  "type": "CheckReminders"
}
```

## Events

### TaskChanged

```json
{
  "type": "TaskChanged",
  "action": "update",
  "task_id": "task-id"
}
```

### ReminderTriggered

```json
{
  "type": "ReminderTriggered",
  "task_id": "task-id",
  "title": "写周报"
}
```

## AI 调用限制

AI 后续只能通过 command、CLI 或 MCP 工具调用任务能力。任何 AI、Skill 或外部自动化都不应直接编辑 `data/tasks.json`。

## CLI JSON Output

当前 CLI 输出与 `CommandResult` 保持同形：

```bash
python -m app.cli --file data/tasks.json add "写周报" --quadrant q1
python -m app.cli --file data/tasks.json delete <task-id> --dry-run
python -m app.cli --file data/tasks.json delete <task-id> --confirm
```

示例输出：

```json
{
  "ok": true,
  "message": "Task added",
  "changed": true,
  "would_change": false,
  "task_id": "task-id",
  "preview": {},
  "data": {
    "task": {}
  },
  "events": [
    {
      "action": "add",
      "task_id": "task-id",
      "type": "TaskChanged"
    }
  ]
}
```

只读查询也使用同一 envelope，`changed` 为 `false`：

```bash
python -m app.cli --file data/tasks.json list --view archive
```

## Audit Log

每次 command 执行后会追加 JSONL 审计记录，默认文件为：

```text
data/audit.log.jsonl
```

示例字段：

```json
{
  "time": "2026-06-09T14:30:00",
  "source": "cli",
  "dry_run": false,
  "command": "AddTask",
  "payload": {},
  "ok": true,
  "changed": true,
  "would_change": false,
  "task_id": "task-id",
  "events": []
}
```
