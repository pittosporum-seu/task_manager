# Task Manager Skill

本 Skill 是未来 AI 使用 TaskManager 的说明草案。当前桌面程序不会加载它，也不会依赖它。

## 适用场景

- 用户想新增、更新、移动、完成、重开或删除任务。
- 用户想让 AI 根据自然语言整理任务。
- 用户想把任务操作接入未来 CLI 或 MCP server。

## 操作原则

- 只能通过 command、CLI 或 MCP 调用任务能力。
- 不要直接编辑 `data/tasks.json`。
- 不要在 Skill 中复制排序、归档、提醒等业务规则。
- 不要引入大模型 SDK 到桌面应用内部。

## 未来调用路径

```text
Natural language
-> Skill intent parsing
-> CLI/MCP tool
-> Command
-> TaskApplication.dispatch()
-> CommandResult
```

当前已经存在轻量 CLI：

```bash
python -m app.cli --file data/tasks.json list --view inbox
python -m app.cli --file data/tasks.json add "写周报" --quadrant q1
python -m app.cli --file data/tasks.json delete <task-id> --dry-run
```

Skill 后续应优先调用 CLI 或 MCP，不要直接编辑 JSON 文件。
涉及删除或批量整理时，必须先使用 dry-run 获取 preview，不要直接执行 destructive command。

## 当前可用的 command 概念

- `AddTask`
- `UpdateTask`
- `DeleteTask`
- `MoveTask`
- `CompleteTask`
- `ReopenTask`
- `CheckReminders`

## 注意

当前仓库还没有实现 MCP server。本文件只用于保留未来 AI 接入边界。
