"""
Process Manager panel - Interface for userspace/process-manager/
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

# Ensure parent directory is in path for absolute imports
_parent = str(Path(__file__).parent.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from utils.logger import get_logger
from utils.process_runner import ProcessRunner

logger = get_logger("process_manager_panel")


class ProcessManagerPanel(ttk.Frame):
    """Panel for process manager operations."""

    def __init__(self, parent):
        super().__init__(parent)
        self.binary_path = Path(__file__).parent.parent.parent / "userspace/process-manager/process-manager"
        self.runner = None

        self.setup_ui()
        self.check_binary()

    def setup_ui(self):
        """Setup the UI components."""
        # Title
        title = ttk.Label(self, text="Process Manager", font=("TkDefaultFont", 14, "bold"))
        title.pack(pady=10)

        # Binary info
        info_frame = ttk.LabelFrame(self, text="Binary Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.binary_label = ttk.Label(info_frame, text=f"Path: {self.binary_path}")
        self.binary_label.pack(anchor=tk.W)

        self.status_label = ttk.Label(info_frame, text="Checking...")
        self.status_label.pack(anchor=tk.W)

        # Control buttons
        btn_frame = ttk.LabelFrame(self, text="Operations", padding=10)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="List Processes", command=lambda: self.run_command(['--list'])).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Show Tree", command=lambda: self.run_command(['--tree'])).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Find Zombies", command=lambda: self.run_command(['--zombies'])).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Kill Process", command=self.kill_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=5)

        # Output console
        output_frame = ttk.LabelFrame(self, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbar + Text widget
        scroll = ttk.Scrollbar(output_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = tk.Text(output_frame, height=20, yscrollcommand=scroll.set, state=tk.DISABLED, font=("Courier", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.output_text.yview)

        # Configure tags for colored output
        self.output_text.tag_config("stdout", foreground="black")
        self.output_text.tag_config("stderr", foreground="red")
        self.output_text.tag_config("system", foreground="blue")

    def check_binary(self):
        """Check if binary exists and is executable."""
        if self.binary_path.exists() and os.access(self.binary_path, os.X_OK):
            self.status_label.config(text="Status: Ready ✓", foreground="green")
            logger.info(f"Binary found and executable: {self.binary_path}")
        else:
            self.status_label.config(text="Status: Binary not found or not executable!", foreground="red")
            logger.error(f"Binary not found or not executable: {self.binary_path}")

    def run_command(self, args):
        """Run process-manager with given arguments."""
        if not self.binary_path.exists():
            self.append_output("Error: Binary not found\n", "stderr")
            return

        self.append_output(f"$ {self.binary_path} {' '.join(args)}\n", "system")
        logger.info(f"Running command: {self.binary_path} {' '.join(args)}")

        self.runner = ProcessRunner(self.on_output)

        if self.runner.start([str(self.binary_path)] + args):
            # Schedule periodic queue processing
            self.process_runner_queue()
        else:
            self.append_output("Failed to start process\n", "stderr")

    def on_output(self, text, tag):
        """Callback for process output."""
        self.append_output(text, tag)

    def append_output(self, text, tag="stdout"):
        """Append text to output console."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text, tag)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def process_runner_queue(self):
        """Process queued output from runner."""
        if self.runner:
            self.runner.process_queue()

        # Schedule next check
        self.after(100, self.process_runner_queue)

    def kill_process(self):
        """Kill a process by PID."""
        pid = simpledialog.askinteger("Kill Process", "Enter PID to kill:", parent=self)
        if pid:
            self.run_command(['--kill', str(pid)])

    def clear_output(self):
        """Clear the output console."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        logger.info("Output cleared")


import os
