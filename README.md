# Quadrant Task Manager

一个基于 PyQt6 的四象限任务管理器。项目来自 Gemini 分享页中的设计讨论整理，已合并为一套完整、可运行、可继续维护的代码结构。

## 功能

- 收件箱与四象限视图
- 任务自动排序：未完成任务优先，再按截止时间排序
- 拖拽任务到不同象限
- 任务标题、描述、截止时间、具体时间和提醒
- 完成状态复选框，已完成任务当天仍显示，历史完成任务进入归档
- 归档窗口可查看和恢复完成任务
- 统一样式配置，右键菜单悬停不会丢失文字
- 多语言文字托管，当前默认中文
- 自定义 SVG Logo 与复选框资源

## 运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

任务数据会保存在 `data/tasks.json`，该文件已被 `.gitignore` 忽略。

归档口径：归档窗口展示“历史完成记录”，即不包含今天刚完成、仍保留在主视图里的任务。

## 测试

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

UI smoke test 使用 Qt offscreen 模式，不会打开真实窗口。

## 打包

```powershell
pip install -r requirements-build.txt
.\scripts\build_exe.ps1
```

产物会输出到 `outputs/TaskManager-v0.1.0-win64.zip`。

## 结构

```text
app/
  config.py
  domain/
    task_rules.py
  models/
    task.py
  resources/
    strings.py
    imgs/
  services/
    task_service.py
  ui/
    components/
    views/
main.py
docs/
  gemini-summary.md
```

## 语言切换

在 `app/config.py` 中修改：

```python
LANGUAGE = "cn"
```

可选值为 `"cn"` 或 `"en"`。
