"""
Socket Client panel - Send messages to socket server
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Ensure parent directory is in path for absolute imports
_parent = str(Path(__file__).parent.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from utils.logger import get_logger
from utils.process_runner import ProcessRunner

logger = get_logger("socket_client_panel")


class SocketClientPanel(ttk.Frame):
    """Panel for socket client operations."""

    def __init__(self, parent):
        super().__init__(parent)
        self.binary_path = Path(__file__).parent.parent.parent / "userspace/socket-client/socket-client"
        self.runner = None

        self.setup_ui()
        self.check_binary()

    def setup_ui(self):
        """Setup the UI components."""
        # Title
        title = ttk.Label(self, text="Socket Client", font=("TkDefaultFont", 14, "bold"))
        title.pack(pady=10)

        # Binary info
        info_frame = ttk.LabelFrame(self, text="Binary Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.binary_label = ttk.Label(info_frame, text=f"Path: {self.binary_path}")
        self.binary_label.pack(anchor=tk.W)

        self.status_label = ttk.Label(info_frame, text="Checking...")
        self.status_label.pack(anchor=tk.W)

        # Connection config
        config_frame = ttk.LabelFrame(self, text="Connection Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        host_frame = ttk.Frame(config_frame)
        host_frame.pack(fill=tk.X, pady=2)
        ttk.Label(host_frame, text="Host:", width=10).pack(side=tk.LEFT)
        self.host_entry = ttk.Entry(host_frame, width=30)
        self.host_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.host_entry.insert(0, "127.0.0.1")

        port_frame = ttk.Frame(config_frame)
        port_frame.pack(fill=tk.X, pady=2)
        ttk.Label(port_frame, text="Port:", width=10).pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(port_frame, width=30)
        self.port_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.port_entry.insert(0, "8080")

        # Message input
        msg_frame = ttk.LabelFrame(self, text="Message", padding=10)
        msg_frame.pack(fill=tk.X, padx=10, pady=5)

        self.message_text = tk.Text(msg_frame, height=4, width=50)
        self.message_text.pack(fill=tk.BOTH, expand=True)
        self.message_text.insert(1.0, "Hello from socket client!")

        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Send Message", command=self.send_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=5)

        # Output console
        output_frame = ttk.LabelFrame(self, text="Client Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll = ttk.Scrollbar(output_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = tk.Text(output_frame, height=15, yscrollcommand=scroll.set,
                                   state=tk.DISABLED, font=("Courier", 9))
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

    def send_message(self):
        """Send message to server."""
        if not self.binary_path.exists():
            self.append_output("Error: Binary not found\n", "stderr")
            return

        host = self.host_entry.get().strip()
        port_str = self.port_entry.get().strip()
        message = self.message_text.get(1.0, tk.END).strip()

        if not host or not port_str or not message:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number (1-65535)")
            return

        cmd = [str(self.binary_path), '--host', host, '--port', str(port), '--message', message]
        self.append_output(f"$ {' '.join(cmd)}\n", "system")
        logger.info(f"Sending message to {host}:{port}")

        self.runner = ProcessRunner(self.on_output)

        if self.runner.start(cmd):
            self.process_runner_queue()
        else:
            self.append_output("Failed to start client\n", "stderr")

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
