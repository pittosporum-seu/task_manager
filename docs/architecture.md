# TaskManager Architecture

当前代码按“规则、用例、存储、适配、界面”分层。目标是让 PyQt UI、未来 CLI、未来 AI Skill、未来 MCP server 都通过同一组任务能力入口工作。

## 分层

- `app/domain/`
  - 纯业务规则：排序、过滤、归档、提醒触发判断、象限业务定义。
  - 不读写文件，不依赖 PyQt。
- `app/application/`
  - 应用用例层：`Command`、`CommandResult`、`TaskApplication.dispatch()`、应用事件。
  - 所有修改任务的行为都必须通过 command 进入。
  - 不依赖 PyQt，不依赖任何 AI SDK。
- `app/infrastructure/`
  - 持久化适配层：当前只有 `JsonTaskRepository`。
  - 负责兼容 `data/tasks.json` 的现有格式。
- `app/services/task_service.py`
  - PyQt 适配层。
  - 把旧 UI 方法转换为 command，并把 application event 转为 Qt signal。
- `app/ui/`
  - 只负责展示和用户交互。
  - 通过 `TaskService` 调用任务能力，不直接修改数据。
- Future CLI / Future AI / Future MCP
  - 后续都应调用 command/application 接口。
  - 不允许直接编辑 `data/tasks.json`。

## 数据流

```text
UI / Future CLI / Future AI
-> Command
-> TaskApplication.dispatch()
-> Repository + Domain Rules
-> EventBus
-> TaskService / Qt signal
-> UI refresh
```

## 写操作入口

当前支持的 command：

- `AddTask`
- `UpdateTask`
- `DeleteTask`
- `MoveTask`
- `CompleteTask`
- `ReopenTask`
- `CheckReminders`

所有 command 都返回 `CommandResult`：

- `ok`
- `message`
- `changed`
- `task_id`
- `data`
- `events`

## 事件

- `TaskChanged`
  - 任务新增、更新、删除、移动、完成、重开或提醒状态更新时产生。
- `ReminderTriggered`
  - 到达提醒触发时间时产生。

`TaskService` 会订阅这些事件，并转换成现有 UI 使用的 `data_changed` 和 `reminder_triggered`。

## 存储

`JsonTaskRepository` 保持现有 JSON 格式：

```json
{
  "task-id": {
    "id": "task-id",
    "title": "Example"
  }
}
```

兼容旧数据：如果 payload 内缺少 `id`，会使用 JSON 外层 key 作为 fallback id。

## 边界约束

- `domain`、`application`、`infrastructure` 不允许依赖 PyQt。
- AI 后续只能通过 command、CLI 或 MCP 调用任务能力。
- AI 不允许直接写 `data/tasks.json`。
- 当前版本不实现 MCP server，不引入模型 SDK，不发起网络请求。

## CLI

当前已有轻量 CLI 入口：

```bash
python -m app.cli --file data/tasks.json list --view inbox
python -m app.cli --file data/tasks.json add "写周报" --quadrant q1
python -m app.cli --file data/tasks.json complete <task-id>
```

CLI 只做参数解析和 JSON 输出，写操作仍然会构造 command 并调用
`TaskApplication.dispatch()`。这层可以作为未来 AI/Skill/MCP 的稳定外壳，但当前不包含任何
AI 调用逻辑。
