"""
Socket Server panel - Start/Stop server daemon
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from pathlib import Path

# Ensure parent directory is in path for absolute imports
_parent = str(Path(__file__).parent.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from utils.logger import get_logger
from utils.process_runner import ProcessRunner

logger = get_logger("socket_server_panel")


class SocketServerPanel(ttk.Frame):
    """Panel for socket server operations."""

    def __init__(self, parent):
        super().__init__(parent)
        self.binary_path = Path(__file__).parent.parent.parent / "userspace/socket-server/socket-server"
        self.runner = None

        self.setup_ui()
        self.check_binary()

    def setup_ui(self):
        """Setup the UI components."""
        # Title
        title = ttk.Label(self, text="Socket Server", font=("TkDefaultFont", 14, "bold"))
        title.pack(pady=10)

        # Binary info
        info_frame = ttk.LabelFrame(self, text="Binary Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.binary_label = ttk.Label(info_frame, text=f"Path: {self.binary_path}")
        self.binary_label.pack(anchor=tk.W)

        self.status_label = ttk.Label(info_frame, text="Checking...")
        self.status_label.pack(anchor=tk.W)

        # Server config
        config_frame = ttk.LabelFrame(self, text="Server Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        port_frame = ttk.Frame(config_frame)
        port_frame.pack(fill=tk.X, pady=5)

        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(port_frame, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "8080")

        # Server status
        status_frame = ttk.LabelFrame(self, text="Server Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.server_status_label = ttk.Label(status_frame, text="Server: STOPPED", font=("TkDefaultFont", 10, "bold"), foreground="red")
        self.server_status_label.pack(anchor=tk.W)

        self.pid_label = ttk.Label(status_frame, text="PID: -")
        self.pid_label.pack(anchor=tk.W)

        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Start Server", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=5)

        # Output console
        output_frame = ttk.LabelFrame(self, text="Server Output", padding=10)
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

    def start_server(self):
        """Start the socket server."""
        if not self.binary_path.exists():
            self.append_output("Error: Binary not found\n", "stderr")
            return

        try:
            port = int(self.port_entry.get().strip())
            if port < 1 or port > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number (1-65535)")
            return

        self.append_output(f"$ {self.binary_path} --port {port}\n", "system")
        self.append_output(f"Starting server on port {port}...\n", "system")
        logger.info(f"Starting socket server on port {port}")

        self.runner = ProcessRunner(self.on_output)

        if self.runner.start([str(self.binary_path), '--port', str(port)]):
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.DISABLED)

            self.server_status_label.config(text="Server: RUNNING", foreground="green")

            pid = self.runner.get_pid()
            if pid:
                self.pid_label.config(text=f"PID: {pid}")

            self.process_runner_queue()
        else:
            self.append_output("Failed to start server\n", "stderr")

    def stop_server(self):
        """Stop the socket server."""
        if self.runner:
            self.runner.stop()
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.NORMAL)

            self.server_status_label.config(text="Server: STOPPED", foreground="red")
            self.pid_label.config(text="PID: -")

            logger.info("Stopped socket server")

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
