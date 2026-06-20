"""
Kernel Module panel - Load/Unload/Status for monitor.ko
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
from utils.privilege import run_with_privilege, ask_password_dialog, check_needs_root

logger = get_logger("kernel_panel")


class KernelPanel(ttk.Frame):
    """Panel for kernel module management."""

    def __init__(self, parent):
        super().__init__(parent)
        self.module_path = Path(__file__).parent.parent.parent / "kernel/monitor-module/monitor.ko"
        self.module_name = "monitor"

        self.setup_ui()
        self.update_status()

        # Auto-load /proc/process_monitor if module is loaded
        self.after(500, self.auto_load_procfs)

    def setup_ui(self):
        """Setup the UI components."""
        # Title
        title = ttk.Label(self, text="Kernel Module Manager", font=("TkDefaultFont", 14, "bold"))
        title.pack(pady=10)

        # Module info
        info_frame = ttk.LabelFrame(self, text="Module Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(info_frame, text=f"Module: {self.module_name}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Path: {self.module_path}").pack(anchor=tk.W)

        # Status frame
        status_frame = ttk.LabelFrame(self, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(status_frame, text="Checking...", font=("TkDefaultFont", 10, "bold"))
        self.status_label.pack(anchor=tk.W)

        self.procfs_label = ttk.Label(status_frame, text="")
        self.procfs_label.pack(anchor=tk.W)

        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.load_btn = ttk.Button(btn_frame, text="Load Module", command=self.load_module)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.unload_btn = ttk.Button(btn_frame, text="Unload Module", command=self.unload_module)
        self.unload_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = ttk.Button(btn_frame, text="Refresh Status", command=self.update_status)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        # dmesg output
        dmesg_frame = ttk.LabelFrame(self, text="Kernel Messages (dmesg)", padding=10)
        dmesg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbar + Text widget
        scroll = ttk.Scrollbar(dmesg_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.dmesg_text = tk.Text(dmesg_frame, height=15, yscrollcommand=scroll.set, state=tk.DISABLED)
        self.dmesg_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.dmesg_text.yview)

        ttk.Button(dmesg_frame, text="Refresh dmesg", command=self.refresh_dmesg).pack(pady=5)

        # /proc/process_monitor output
        proc_frame = ttk.LabelFrame(self, text="/proc/process_monitor Output", padding=10)
        proc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        proc_scroll = ttk.Scrollbar(proc_frame)
        proc_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.proc_text = tk.Text(proc_frame, height=10, yscrollcommand=proc_scroll.set, state=tk.DISABLED)
        self.proc_text.pack(fill=tk.BOTH, expand=True)
        proc_scroll.config(command=self.proc_text.yview)

        ttk.Button(proc_frame, text="Read /proc/process_monitor", command=self.read_procfs).pack(pady=5)

    def update_status(self):
        """Check if module is loaded."""
        try:
            import subprocess
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if self.module_name in result.stdout:
                self.status_label.config(text="Status: LOADED ✓", foreground="green")
                self.load_btn.config(state=tk.DISABLED)
                self.unload_btn.config(state=tk.NORMAL)
                logger.info(f"Module {self.module_name} is loaded")
            else:
                self.status_label.config(text="Status: NOT LOADED", foreground="red")
                self.load_btn.config(state=tk.NORMAL)
                self.unload_btn.config(state=tk.DISABLED)
                logger.info(f"Module {self.module_name} is not loaded")

            # Check /proc entry
            proc_path = Path(f"/proc/process_monitor")
            if proc_path.exists():
                self.procfs_label.config(text="/proc/process_monitor: EXISTS ✓", foreground="green")
            else:
                self.procfs_label.config(text="/proc/process_monitor: NOT FOUND", foreground="gray")

        except Exception as e:
            self.status_label.config(text=f"Status: ERROR - {e}", foreground="red")
            logger.error(f"Error checking module status: {e}")

    def load_module(self):
        """Load the kernel module using insmod."""
        if not self.module_path.exists():
            messagebox.showerror("Error", f"Module file not found:\n{self.module_path}")
            return

        if not messagebox.askyesno("Confirm",
                                    "Loading kernel modules requires root privileges.\n"
                                    "This will insert a kernel module into the running kernel.\n\n"
                                    "Continue?"):
            return

        logger.info(f"Loading module: {self.module_path}")

        def password_callback():
            return ask_password_dialog(self)

        returncode, stdout, stderr = run_with_privilege(
            ['insmod', str(self.module_path)],
            password_callback=password_callback
        )

        if returncode == 0:
            messagebox.showinfo("Success", f"Module {self.module_name} loaded successfully")
            logger.info(f"Module loaded successfully: {stdout}")
        else:
            messagebox.showerror("Error", f"Failed to load module:\n{stderr}")
            logger.error(f"Failed to load module: {stderr}")

        self.update_status()
        self.refresh_dmesg()

    def unload_module(self):
        """Unload the kernel module using rmmod."""
        if not messagebox.askyesno("Confirm",
                                    "Unload kernel module?\n"
                                    "This requires root privileges."):
            return

        logger.info(f"Unloading module: {self.module_name}")

        def password_callback():
            return ask_password_dialog(self)

        returncode, stdout, stderr = run_with_privilege(
            ['rmmod', self.module_name],
            password_callback=password_callback
        )

        if returncode == 0:
            messagebox.showinfo("Success", f"Module {self.module_name} unloaded successfully")
            logger.info(f"Module unloaded successfully")
        else:
            messagebox.showerror("Error", f"Failed to unload module:\n{stderr}")
            logger.error(f"Failed to unload module: {stderr}")

        self.update_status()
        self.refresh_dmesg()

    def refresh_dmesg(self):
        """Refresh dmesg output (show last 50 lines related to module)."""
        try:
            import subprocess
            result = subprocess.run(
                ['dmesg'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Filter for lines containing "monitor" or "process_monitor"
            lines = result.stdout.split('\n')
            filtered = [line for line in lines if 'monitor' in line.lower() or 'process_monitor' in line.lower()]

            # Show last 50 lines
            output = '\n'.join(filtered[-50:]) if filtered else "No relevant kernel messages found"

            self.dmesg_text.config(state=tk.NORMAL)
            self.dmesg_text.delete(1.0, tk.END)
            self.dmesg_text.insert(1.0, output)
            self.dmesg_text.config(state=tk.DISABLED)

            logger.info("dmesg output refreshed")

        except Exception as e:
            self.dmesg_text.config(state=tk.NORMAL)
            self.dmesg_text.delete(1.0, tk.END)
            self.dmesg_text.insert(1.0, f"Error reading dmesg: {e}")
            self.dmesg_text.config(state=tk.DISABLED)
            logger.error(f"Error reading dmesg: {e}")

    def auto_load_procfs(self):
        """Auto-load /proc/process_monitor on panel initialization if module is loaded."""
        proc_path = Path("/proc/process_monitor")
        if proc_path.exists():
            self.read_procfs()

    def read_procfs(self):
        """Read and display /proc/process_monitor."""
        proc_path = Path("/proc/process_monitor")

        try:
            if not proc_path.exists():
                raise FileNotFoundError("Module not loaded or /proc entry not created")

            with open(proc_path, 'r') as f:
                content = f.read()

            self.proc_text.config(state=tk.NORMAL)
            self.proc_text.delete(1.0, tk.END)
            self.proc_text.insert(1.0, content)
            self.proc_text.see(tk.END)  # Scroll to bottom
            self.proc_text.config(state=tk.DISABLED)

            logger.info(f"/proc/process_monitor read successfully ({len(content)} bytes, {len(content.splitlines())} lines)")

        except Exception as e:
            self.proc_text.config(state=tk.NORMAL)
            self.proc_text.delete(1.0, tk.END)
            self.proc_text.insert(1.0, f"Error: {e}")
            self.proc_text.config(state=tk.DISABLED)
            logger.error(f"Error reading /proc/process_monitor: {e}")
