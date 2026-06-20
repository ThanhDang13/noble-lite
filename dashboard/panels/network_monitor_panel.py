"""
Network Monitor panel - Interface for userspace/network-monitor/
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, simpledialog
from pathlib import Path

# Ensure parent directory is in path for absolute imports
_parent = str(Path(__file__).parent.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from utils.logger import get_logger
from utils.process_runner import ProcessRunner

logger = get_logger("network_monitor_panel")


class NetworkMonitorPanel(ttk.Frame):
    """Panel for network monitoring operations."""

    def __init__(self, parent):
        super().__init__(parent)
        self.binary_path = Path(__file__).parent.parent.parent / "userspace/network-monitor/network-monitor"
        self.runner = None

        self.setup_ui()
        self.check_binary()

    def setup_ui(self):
        """Setup the UI components."""
        # Title
        title = ttk.Label(self, text="Network Monitor", font=("TkDefaultFont", 14, "bold"))
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

        ttk.Button(btn_frame, text="Show Connections", command=lambda: self.run_command(['--connections'])).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Show Ports", command=lambda: self.run_command(['--ports'])).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Show Stats", command=lambda: self.run_command(['--stats'])).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Watch (Live)", command=self.watch_network).pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop Watch", command=self.stop_runner, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=5)

        # Output console
        output_frame = ttk.LabelFrame(self, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll = ttk.Scrollbar(output_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = tk.Text(output_frame, height=20, yscrollcommand=scroll.set, state=tk.DISABLED, font=("Courier", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.output_text.yview)

        self.output_text.tag_config("stdout", foreground="black")
        self.output_text.tag_config("stderr", foreground="red")
        self.output_text.tag_config("system", foreground="blue")

    def check_binary(self):
        """Check if binary exists and is executable."""
        if self.binary_path.exists() and os.access(self.binary_path, os.X_OK):
            self.status_label.config(text="Status: Ready ✓", foreground="green")
            logger.info(f"Binary found: {self.binary_path}")
        else:
            self.status_label.config(text="Status: Binary not found!", foreground="red")
            logger.error(f"Binary not found: {self.binary_path}")

    def run_command(self, args):
        """Run network-monitor with given arguments."""
        if not self.binary_path.exists():
            self.append_output("Error: Binary not found\n", "stderr")
            return

        self.append_output(f"$ {self.binary_path} {' '.join(args)}\n", "system")
        logger.info(f"Running: {self.binary_path} {' '.join(args)}")

        self.runner = ProcessRunner(self.on_output)

        if self.runner.start([str(self.binary_path)] + args):
            self.process_runner_queue()
        else:
            self.append_output("Failed to start process\n", "stderr")

    def watch_network(self):
        """Start watching network (blocking operation with interval)."""
        interval = simpledialog.askinteger(
            "Watch Interval",
            "Enter refresh interval (seconds):",
            parent=self,
            initialvalue=2,
            minvalue=1,
            maxvalue=60
        )

        if not interval:
            return

        self.append_output(f"$ {self.binary_path} --watch {interval}\n", "system")
        self.append_output("Watch mode started. Press 'Stop Watch' to terminate.\n", "system")
        logger.info(f"Starting watch mode with interval: {interval}s")

        self.runner = ProcessRunner(self.on_output)

        if self.runner.start([str(self.binary_path), '--watch', str(interval)]):
            self.stop_btn.config(state=tk.NORMAL)
            self.process_runner_queue()
        else:
            self.append_output("Failed to start watch mode\n", "stderr")

    def stop_runner(self):
        """Stop the running process."""
        if self.runner:
            self.runner.stop()
            self.stop_btn.config(state=tk.DISABLED)
            logger.info("Stopped network-monitor process")

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
        self.after(100, self.process_runner_queue)

    def clear_output(self):
        """Clear the output console."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        logger.info("Output cleared")
