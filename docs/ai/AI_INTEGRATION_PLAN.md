# AI Integration Plan

本文件只描述未来接入计划。当前程序不接入 AI，不实现 MCP server，不引入大模型 SDK，也不添加网络请求。

## 目标

未来 AI 能帮助用户创建、整理、移动、完成和查询任务，但必须走稳定应用接口：

```text
AI / Skill / CLI / MCP
-> Command
-> TaskApplication.dispatch()
-> Repository + Domain Rules
-> EventBus
```

AI 不允许直接编辑 `data/tasks.json`。

## 推荐阶段

1. CLI 包装
   - 已新增轻量 CLI，把自然语言之外的确定性操作映射成 command。
   - CLI 输出 `CommandResult` 的 JSON 形式。
2. AI Skill
   - Skill 只负责解释用户意图并调用 CLI 或 MCP。
   - Skill 不读写任务 JSON。
3. MCP server
   - 在 command 层之外包装工具，例如 `add_task`、`move_task`、`complete_task`。
   - MCP handler 只构造 command 并调用 application。
4. AI 编排
   - 让模型做任务拆分、优先级建议、自然语言解析。
   - 所有最终写入仍由 command 执行。

## 禁止事项

- 不允许 AI 直接修改 `data/tasks.json`。
- 不允许在 UI 层塞入模型 SDK。
- 不允许绕过 `TaskApplication.dispatch()` 进行写操作。
- 不允许让 MCP server 复制一套任务业务逻辑。

## 已预留接口

- `CommandResult` JSON 序列化，供 CLI/未来 MCP 复用。
- `ListTasks` query DTO，供 CLI/未来 AI 查询不同任务视图。
- command 层已加入基础校验，例如空标题和非法象限。
- `CommandContext` 已支持 source、dry_run、request_id、actor。
- CLI 删除任务要求 `--confirm` 或 `--dry-run`。
- command 执行会写入 `audit.log.jsonl`，便于追溯自动化行为。

## 后续可扩展点

- 增加批量 command，但批量删除必须 dry-run + confirm。
- 增加更细的权限策略，例如按 actor 限制 destructive command。
