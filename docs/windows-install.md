# Windows installation

Build with `scripts/build_exe.ps1`, then run `scripts/install.ps1`.
The extracted distribution also includes `install.ps1`.
Run it with PowerShell: `powershell -ExecutionPolicy Bypass -File .\install.ps1`.

Installs to `%LOCALAPPDATA%\Programs\MyTask`, creates a Start menu shortcut,
and adds the bundled CLI directory to the user PATH. Open a new terminal to use
`mytask list`. No administrator rights are required.

Data and audit records live in `%LOCALAPPDATA%\MyTask\data` independently of
the application installation. Existing portable `data/tasks.json` is not moved
automatically: quit the old application and copy it to the new data directory
before first use. Do not overwrite an existing task file.

Repeated GUI launches activate the existing window. Minimize keeps the window
in the taskbar. Close hides it in the notification area; click the tray icon to
restore it, or use its Quit menu to exit. Without a system tray, Close exits.

GUI and CLI now share SQLite transactions. The GUI polls for external changes.
See sqlite.md for migration and concurrency details.
