"""
Logs panel - View dashboard logs with filtering
"""

import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Ensure parent directory is in path for absolute imports
_parent = str(Path(__file__).parent.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from utils.logger import get_logger, LOGS_DIR

logger = get_logger("logs_panel")


class LogsPanel(ttk.Frame):
    """Panel for viewing dashboard logs."""

    def __init__(self, parent):
        super().__init__(parent)
        self.logs_dir = LOGS_DIR

        self.setup_ui()
        self.refresh_logs()

    def setup_ui(self):
        """Setup the UI components."""
        # Title
        title = ttk.Label(self, text="Dashboard Logs", font=("TkDefaultFont", 14, "bold"))
        title.pack(pady=10)

        # Info frame
        info_frame = ttk.LabelFrame(self, text="Logs Directory", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(info_frame, text=f"Path: {self.logs_dir}").pack(anchor=tk.W)

        # Filter frame
        filter_frame = ttk.LabelFrame(self, text="Filter", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        filter_inner = ttk.Frame(filter_frame)
        filter_inner.pack(fill=tk.X)

        ttk.Label(filter_inner, text="Module:").pack(side=tk.LEFT)
        self.filter_entry = ttk.Entry(filter_inner, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_inner, text="Apply Filter", command=self.apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_inner, text="Clear Filter", command=self.clear_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_inner, text="Refresh", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)

        # Log viewer
        log_frame = ttk.LabelFrame(self, text="Log Content", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbars
        v_scroll = ttk.Scrollbar(log_frame)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        h_scroll = ttk.Scrollbar(log_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.log_text = tk.Text(log_frame, height=25, wrap=tk.NONE,
                               yscrollcommand=v_scroll.set,
                               xscrollcommand=h_scroll.set,
                               state=tk.DISABLED, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        v_scroll.config(command=self.log_text.yview)
        h_scroll.config(command=self.log_text.xview)

        # Color tags for log levels
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")
        self.log_text.tag_config("DEBUG", foreground="gray")

    def refresh_logs(self):
        """Refresh and display logs."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)

        # Find today's log file
        from datetime import datetime
        log_file = self.logs_dir / f"dashboard_{datetime.now().strftime('%Y%m%d')}.log"

        if not log_file.exists():
            self.log_text.insert(tk.END, "No log file found for today.\n")
            self.log_text.config(state=tk.DISABLED)
            logger.info("No log file found")
            return

        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Display with color coding
            for line in lines:
                if '[ERROR]' in line:
                    self.log_text.insert(tk.END, line, "ERROR")
                elif '[WARNING]' in line:
                    self.log_text.insert(tk.END, line, "WARNING")
                elif '[DEBUG]' in line:
                    self.log_text.insert(tk.END, line, "DEBUG")
                else:
                    self.log_text.insert(tk.END, line, "INFO")

            # Scroll to end
            self.log_text.see(tk.END)
            logger.info(f"Loaded {len(lines)} log entries")

        except Exception as e:
            self.log_text.insert(tk.END, f"Error reading log file: {e}\n")
            logger.error(f"Error reading log file: {e}")

        self.log_text.config(state=tk.DISABLED)

    def apply_filter(self):
        """Apply filter to logs."""
        filter_text = self.filter_entry.get().strip().lower()
        if not filter_text:
            self.refresh_logs()
            return

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)

        from datetime import datetime
        log_file = self.logs_dir / f"dashboard_{datetime.now().strftime('%Y%m%d')}.log"

        if not log_file.exists():
            self.log_text.insert(tk.END, "No log file found.\n")
            self.log_text.config(state=tk.DISABLED)
            return

        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()

            filtered_lines = [line for line in lines if filter_text in line.lower()]

            for line in filtered_lines:
                if '[ERROR]' in line:
                    self.log_text.insert(tk.END, line, "ERROR")
                elif '[WARNING]' in line:
                    self.log_text.insert(tk.END, line, "WARNING")
                elif '[DEBUG]' in line:
                    self.log_text.insert(tk.END, line, "DEBUG")
                else:
                    self.log_text.insert(tk.END, line, "INFO")

            self.log_text.insert(1.0, f"Filtered: {len(filtered_lines)} / {len(lines)} entries\n\n", "INFO")
            logger.info(f"Filter applied: {filter_text} -> {len(filtered_lines)} entries")

        except Exception as e:
            self.log_text.insert(tk.END, f"Error reading log file: {e}\n")
            logger.error(f"Error applying filter: {e}")

        self.log_text.config(state=tk.DISABLED)

    def clear_filter(self):
        """Clear filter and show all logs."""
        self.filter_entry.delete(0, tk.END)
        self.refresh_logs()
