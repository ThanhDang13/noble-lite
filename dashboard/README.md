# Linux System Programming Dashboard

Python GUI dashboard for managing and monitoring the Linux system programming project components.

## Features

- **Kernel Module Manager**: Load/unload monitor.ko, view dmesg, read /proc/process_monitor
- **Process Manager**: List processes, show tree, find zombies, kill processes
- **File Manager**: Analyze files, scan directories, watch for changes
- **Network Monitor**: View connections, ports, stats, live monitoring
- **Socket Server**: Start/stop TCP server daemon
- **Socket Client**: Send messages to socket servers
- **Scripts**: Run shell scripts with parameter inputs (backup, cleanup, installer, scheduler, timectl)
- **Logs**: View and filter dashboard logs

## Requirements

- Python 3.8+
- Tkinter (usually included with Python)
- Linux system with the project binaries built

## Project Structure

```
dashboard/
├── app.py                      # Main entry point
├── utils/
│   ├── logger.py              # Logging utilities
│   ├── privilege.py           # Root privilege handling (pkexec/sudo)
│   └── process_runner.py      # Subprocess management with real-time output
└── panels/
    ├── kernel_panel.py        # Kernel module management
    ├── process_manager_panel.py
    ├── file_manager_panel.py
    ├── network_monitor_panel.py
    ├── socket_server_panel.py
    ├── socket_client_panel.py
    ├── scripts_panel.py       # Shell scripts runner
    └── logs_panel.py          # Log viewer
```

## Usage

### Run the Dashboard

```bash
# From project root
python3 dashboard/app.py

# Or from dashboard directory
cd dashboard
python3 app.py
```

### Navigation

- Use the sidebar to switch between different modules
- Each panel has its own controls and output console
- Logs are automatically saved to `logs/dashboard_YYYYMMDD.log`

### Privilege Escalation

Commands requiring root (insmod, rmmod, installer.sh, timectl.sh) will:
1. Try `pkexec` first (system authentication dialog)
2. Fall back to `sudo` with GUI password prompt if pkexec unavailable

### Panel Details

#### Kernel Module
- **Load Module**: Uses `insmod` to load monitor.ko (requires root)
- **Unload Module**: Uses `rmmod` to unload (requires root)
- **Status**: Auto-updates every 5 seconds
- **dmesg**: Shows last 50 kernel messages related to module
- **Read /proc**: Displays output from /proc/process_monitor

#### Process Manager
- **List Processes**: Shows all running processes with PID, name, state, PPID
- **Show Tree**: Displays process hierarchy starting from init (PID 1)
- **Find Zombies**: Lists zombie processes
- **Kill Process**: Send SIGTERM to a process by PID

#### File Manager
- **Analyze File**: Show file metadata (size, permissions, timestamps)
- **Scan Directory**: List directory contents with types and sizes
- **Watch**: Live monitoring of directory changes (inotify-based)
- **Stop Watch**: Terminate watch mode

#### Network Monitor
- **Show Connections**: Active TCP connections
- **Show Ports**: Listening TCP/UDP ports
- **Show Stats**: Network interface statistics
- **Watch**: Live monitoring with configurable interval
- **Stop Watch**: Terminate watch mode

#### Socket Server
- **Start Server**: Launch TCP server on specified port
- **Stop Server**: Terminate running server
- **Real-time Output**: Shows client connections and messages

#### Socket Client
- **Host**: Server hostname or IP (default: 127.0.0.1)
- **Port**: Server port (default: 8080)
- **Message**: Text to send to server
- **Send Message**: Connects, sends message, displays response

#### Scripts
- **backup.sh**: Backup files/directories with compression
- **cleanup.sh**: Remove old logs and temp files (⚠ destructive)
- **installer.sh**: Install/remove packages via apt (⚠ destructive, requires root)
- **scheduler.sh**: Manage cron jobs or systemd timers
- **timectl.sh**: Manage timezone and NTP (requires root)

All destructive scripts require confirmation before execution.

#### Logs
- **View**: Display today's dashboard log file
- **Filter**: Search logs by module name or keyword
- **Auto-color**: ERROR (red), WARNING (orange), INFO (black)
- **Refresh**: Reload log file

## Architecture

### ProcessRunner
All userspace programs and scripts use `ProcessRunner` for:
- Non-blocking subprocess execution
- Real-time stdout/stderr streaming via threading + queue
- Safe Tkinter widget updates from background threads
- Process lifecycle management (start/stop/PID tracking)

### Privilege Handling
Commands needing root use `privilege.py`:
1. Check if `pkexec` available → use native system auth dialog
2. Otherwise → show custom Tkinter password dialog → `sudo -S`
3. Password never logged or stored

### Logging
All operations logged to `logs/dashboard_YYYYMMDD.log`:
- Timestamp + log level + module name + message
- Separate file per day
- Viewable from Logs panel

## Development

### Adding a New Panel

1. Create `dashboard/panels/new_panel.py`:
```python
from tkinter import ttk
from ..utils.logger import get_logger

logger = get_logger("new_panel")

class NewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
```

2. Import and register in `dashboard/app.py`:
```python
from panels.new_panel import NewPanel

# In panels_config:
("New Panel", "🆕"),

# In show_panel():
elif panel_name == "New Panel":
    self.panels[panel_name] = NewPanel(self.content_frame)
```

### Running a Command with Real-time Output

```python
from utils.process_runner import ProcessRunner

def on_output(text, tag):
    # tag is 'stdout', 'stderr', or 'system'
    self.append_to_console(text, tag)

runner = ProcessRunner(on_output)
runner.start(['/path/to/binary', '--arg'])

# Periodically in GUI thread:
runner.process_queue()

# To stop:
runner.stop()
```

## Security Notes

- Dashboard does NOT run as root by default
- Root commands isolated via pkexec/sudo per-operation
- Password prompt only when needed, not stored
- Scripts marked destructive require explicit confirmation
- All actions logged for audit trail

## Troubleshooting

**Binary not found errors:**
- Ensure all userspace programs are compiled: `make` in each userspace/* directory
- Ensure kernel module is built: `make` in kernel/monitor-module/

**Permission denied on kernel module load:**
- Module loading requires root
- Check pkexec is installed: `which pkexec`
- Or enter password when prompted for sudo

**Socket server won't start:**
- Port already in use: try different port
- Port < 1024 requires root: use port >= 1024

**Watch mode not stopping:**
- Click "Stop Watch" button
- If stuck, restart dashboard

## License

Part of Linux System Programming course project.
