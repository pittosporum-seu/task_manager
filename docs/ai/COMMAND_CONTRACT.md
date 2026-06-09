# Command Contract

这是未来 CLI / AI / MCP 调用任务能力时应遵守的 command 契约。当前代码已经实现 Python dataclass command；本文档用于约定未来 JSON 或工具调用格式。

## 统一结果

每次写操作都返回 `CommandResult`：

```json
{
  "ok": true,
  "message": "Task added",
  "changed": true,
  "task_id": "task-id",
  "data": {},
  "events": []
}
```

字段说明：

- `ok`：命令是否执行成功。
- `message`：给调用方看的简短结果。
- `changed`：是否改变了任务数据。
- `task_id`：主要影响的任务 id，没有时为 `null`。
- `data`：附加数据，未来 CLI/MCP 应保持 JSON 可序列化。
- `events`：执行过程中产生的应用事件。

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
