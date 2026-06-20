# Dashboard Installation & Usage

## Prerequisites

Install Python 3 and Tkinter:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-tk
```

Or run the automated setup script:

```bash
./setup_dashboard.sh
```

## Quick Start

### Option 1: Use launcher script

```bash
./launch_dashboard.py
```

### Option 2: Run directly

```bash
cd dashboard
python3 app.py
```

### Option 3: Run from anywhere

```bash
python3 -m dashboard.app
# (from project root)
```

## First Time Setup

1. **Install Tkinter** (see above)

2. **Build all components**:
   ```bash
   # Build userspace programs
   cd userspace/process-manager && make && cd ../..
   cd userspace/file-manager && make && cd ../..
   cd userspace/network-monitor && make && cd ../..
   cd userspace/socket-server && make && cd ../..
   cd userspace/socket-client && make && cd ../..
   
   # Build kernel module (in VM only!)
   # cd kernel/monitor-module && make
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x scripts/*.sh
   ```

4. **Launch dashboard**:
   ```bash
   ./launch_dashboard.py
   ```

## Usage Guide

### Navigation
- Click on sidebar items to switch between panels
- Each panel has independent controls and output console
- Kernel module status shown at bottom of sidebar (updates every 5s)

### Panels Overview

#### 🔧 Kernel Module
- Load/unload `monitor.ko` (requires root)
- View kernel messages (dmesg)
- Read `/proc/process_monitor` output
- **Warning**: Only use in VM, never on host

#### 📊 Process Manager
- List all processes
- Show process tree
- Find zombie processes
- Kill process by PID

#### 📁 File Manager
- Analyze file metadata
- Scan directory contents
- Watch directory for real-time changes (blocking)

#### 🌐 Network Monitor
- Show active TCP connections
- Show listening ports (TCP/UDP)
- Show network interface statistics
- Watch mode with configurable interval (blocking)

#### 🖥️ Socket Server
- Start TCP server on specified port
- View real-time client connections
- Stop running server

#### 💻 Socket Client
- Connect to socket server
- Send messages
- View server response

#### 📜 Scripts
- Run shell scripts with GUI inputs
- **backup.sh**: Backup with compression
- **cleanup.sh**: Clean old logs/temp (⚠ destructive)
- **installer.sh**: Install/remove packages (⚠ destructive, requires root)
- **scheduler.sh**: Manage cron jobs
- **timectl.sh**: Manage time/timezone (requires root)

#### 📋 Logs
- View today's dashboard log
- Filter by module or keyword
- Color-coded by log level (ERROR=red, WARNING=orange)

### Root Privilege

Commands requiring root will:
1. Try `pkexec` first (system auth dialog)
2. Fall back to GUI password prompt for `sudo`

Never run the entire dashboard as root - privilege escalation is per-operation only.

### Logs

All operations are logged to:
```
logs/dashboard_YYYYMMDD.log
```

View from the Logs panel or directly:
```bash
tail -f logs/dashboard_$(date +%Y%m%d).log
```

## Troubleshooting

**"ModuleNotFoundError: No module named 'tkinter'"**
```bash
sudo apt-get install python3-tk
```

**"Binary not found" errors**
- Build the userspace programs: `make` in each `userspace/*/` directory

**"Permission denied" on module load**
- Module operations require root
- Make sure you're in a VM, not on host

**Socket server won't start**
- Port already in use: try different port
- Port < 1024 needs root: use port >= 1024

**Scripts not executable**
```bash
chmod +x scripts/*.sh
```

## Architecture

### ProcessRunner
- Non-blocking subprocess execution
- Real-time stdout/stderr streaming
- Thread-safe Tkinter updates via queue
- Used by all panels for command execution

### Privilege Escalation
- Automatic detection of commands needing root
- `pkexec` preferred (native system dialog)
- Falls back to `sudo -S` with GUI password prompt
- Password never logged or stored

### Logging
- Centralized logging via `utils/logger.py`
- Separate file per day
- All operations logged with timestamp + module + level

## Development

All panels inherit from `ttk.Frame` and follow this pattern:

```python
from tkinter import ttk
from ..utils.logger import get_logger
from ..utils.process_runner import ProcessRunner

logger = get_logger("my_panel")

class MyPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.runner = None
        self.setup_ui()
    
    def setup_ui(self):
        # Create widgets
        pass
    
    def run_command(self, args):
        self.runner = ProcessRunner(self.on_output)
        self.runner.start(['/path/to/binary'] + args)
        self.process_runner_queue()
    
    def on_output(self, text, tag):
        # Handle output (tag = 'stdout', 'stderr', 'system')
        pass
    
    def process_runner_queue(self):
        if self.runner:
            self.runner.process_queue()
        self.after(100, self.process_runner_queue)
```

Register new panels in `dashboard/app.py`:
1. Import the panel class
2. Add to `panels_config` list
3. Add case in `show_panel()` method

## File Structure

```
dashboard/
├── app.py                      # Main entry point
├── README.md                   # Full documentation
├── __init__.py
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Centralized logging
│   ├── privilege.py           # Root privilege handling
│   └── process_runner.py      # Subprocess with real-time output
└── panels/
    ├── __init__.py
    ├── kernel_panel.py
    ├── process_manager_panel.py
    ├── file_manager_panel.py
    ├── network_monitor_panel.py
    ├── socket_server_panel.py
    ├── socket_client_panel.py
    ├── scripts_panel.py
    └── logs_panel.py

logs/                           # Auto-created
    └── dashboard_YYYYMMDD.log
```

## Security Notes

- Dashboard runs as regular user by default
- Root operations isolated per-command
- Destructive scripts require confirmation
- Password prompts only when needed
- All actions logged for audit

## Project Context

This dashboard is part of a Linux System Programming course project:
- **YC1**: Shell scripts, system programming (C), kernel module
- **YC2**: Minimal Ubuntu, custom kernel build

The dashboard provides a unified GUI interface to manage and test all project components without memorizing CLI arguments.

## License

Part of Linux System Programming course project.
