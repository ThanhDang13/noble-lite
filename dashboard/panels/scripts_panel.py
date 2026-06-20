"""
Scripts panel - Run shell scripts with parameter inputs
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

# Ensure parent directory is in path for absolute imports
_parent = str(Path(__file__).parent.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from utils.logger import get_logger
from utils.process_runner import ProcessRunner
from utils.privilege import run_with_privilege, ask_password_dialog

logger = get_logger("scripts_panel")


class ScriptsPanel(ttk.Frame):
    """Panel for running shell scripts."""

    def __init__(self, parent):
        super().__init__(parent)
        self.scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        self.runner = None

        self.scripts = {
            'backup.sh': {
                'destructive': False,
                'needs_root': False,
                'params': [
                    ('source', 'Source path', 'entry'),
                    ('destination', 'Destination path', 'entry'),
                    ('compress', 'Compression (gzip/bzip2/xz)', 'combo')
                ]
            },
            'cleanup.sh': {
                'destructive': True,
                'needs_root': False,
                'params': [
                    ('days', 'Days to keep', 'entry'),
                    ('dry_run', 'Dry run', 'check')
                ]
            },
            'installer.sh': {
                'destructive': True,
                'needs_root': True,
                'params': [
                    ('packages', 'Package names (space-separated)', 'entry'),
                    ('action', 'Action (install/remove)', 'combo'),
                    ('update', 'Update package list first', 'check')
                ]
            },
            'scheduler.sh': {
                'destructive': False,
                'needs_root': False,
                'params': [
                    ('action', 'Action (add/remove/list)', 'combo'),
                    ('schedule', 'Schedule (cron format)', 'entry'),
                    ('command', 'Command to schedule', 'entry')
                ]
            },
            'timectl.sh': {
                'destructive': False,
                'needs_root': True,
                'params': [
                    ('action', 'Action (status/set-tz/enable-ntp)', 'combo'),
                    ('timezone', 'Timezone (e.g., Asia/Ho_Chi_Minh)', 'entry')
                ]
            }
        }

        self.param_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components."""
        # Title
        title = ttk.Label(self, text="Shell Scripts", font=("TkDefaultFont", 14, "bold"))
        title.pack(pady=10)

        # Scripts directory info
        info_frame = ttk.LabelFrame(self, text="Scripts Directory", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(info_frame, text=f"Path: {self.scripts_dir}").pack(anchor=tk.W)

        # Script selection
        select_frame = ttk.LabelFrame(self, text="Select Script", padding=10)
        select_frame.pack(fill=tk.X, padx=10, pady=5)

        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(select_frame, textvariable=self.script_var,
                                         values=list(self.scripts.keys()), state='readonly', width=30)
        self.script_combo.pack(side=tk.LEFT, padx=5)
        self.script_combo.bind('<<ComboboxSelected>>', self.on_script_selected)

        if self.scripts:
            self.script_combo.current(0)

        # Parameters frame (dynamic based on selected script)
        self.params_frame = ttk.LabelFrame(self, text="Parameters", padding=10)
        self.params_frame.pack(fill=tk.X, padx=10, pady=5)

        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Run Script", command=self.run_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Stop", command=self.stop_runner, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        self.stop_btn = btn_frame.winfo_children()[-1]
        ttk.Button(btn_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=5)

        # Output console
        output_frame = ttk.LabelFrame(self, text="Script Output", padding=10)
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

        # Initialize with first script
        self.on_script_selected(None)

    def on_script_selected(self, event):
        """Handle script selection change."""
        script_name = self.script_var.get()
        if not script_name:
            return

        # Clear existing param widgets
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        self.param_widgets.clear()

        script_info = self.scripts[script_name]

        # Show warning if destructive or needs root
        warning_text = []
        if script_info['destructive']:
            warning_text.append("⚠ DESTRUCTIVE: May delete/modify data")
        if script_info['needs_root']:
            warning_text.append("🔒 REQUIRES ROOT")

        if warning_text:
            warn_label = ttk.Label(self.params_frame, text=' | '.join(warning_text),
                                  foreground="red", font=("TkDefaultFont", 9, "bold"))
            warn_label.pack(anchor=tk.W, pady=5)

        # Create parameter widgets
        for param_name, param_label, param_type in script_info['params']:
            frame = ttk.Frame(self.params_frame)
            frame.pack(fill=tk.X, pady=3)

            ttk.Label(frame, text=param_label + ":", width=25).pack(side=tk.LEFT)

            if param_type == 'entry':
                widget = ttk.Entry(frame, width=40)
                widget.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            elif param_type == 'combo':
                widget = ttk.Combobox(frame, width=37, state='readonly')
                if param_name == 'compress':
                    widget['values'] = ['gzip', 'bzip2', 'xz']
                    widget.current(0)
                elif param_name == 'action' and script_name == 'installer.sh':
                    widget['values'] = ['install', 'remove']
                    widget.current(0)
                elif param_name == 'action' and script_name == 'scheduler.sh':
                    widget['values'] = ['add', 'remove', 'list']
                    widget.current(0)
                elif param_name == 'action' and script_name == 'timectl.sh':
                    widget['values'] = ['status', 'set-tz', 'enable-ntp', 'disable-ntp']
                    widget.current(0)
                widget.pack(side=tk.LEFT, padx=5)
            elif param_type == 'check':
                widget = ttk.Checkbutton(frame)
                widget.pack(side=tk.LEFT, padx=5)

            self.param_widgets[param_name] = (widget, param_type)

    def run_script(self):
        """Run the selected script with parameters."""
        script_name = self.script_var.get()
        if not script_name:
            messagebox.showerror("Error", "Please select a script")
            return

        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            self.append_output(f"Error: Script not found: {script_path}\n", "stderr")
            return

        script_info = self.scripts[script_name]

        # Confirm if destructive
        if script_info['destructive']:
            if not messagebox.askyesno("Confirm",
                                       f"⚠ WARNING: {script_name} may delete or modify data.\n\n"
                                       "Are you sure you want to continue?"):
                return

        # Build command arguments
        cmd = [str(script_path)]

        # Parse parameters based on script
        if script_name == 'backup.sh':
            source = self.param_widgets['source'][0].get().strip()
            dest = self.param_widgets['destination'][0].get().strip()
            compress = self.param_widgets['compress'][0].get()

            if not source or not dest:
                messagebox.showerror("Error", "Source and destination are required")
                return

            cmd.extend(['-c', compress, source, dest])

        elif script_name == 'cleanup.sh':
            days = self.param_widgets['days'][0].get().strip() or '7'
            dry_run = self.param_widgets['dry_run'][0].instate(['selected'])

            cmd.extend(['--days', days])
            if dry_run:
                cmd.append('--dry-run')

        elif script_name == 'installer.sh':
            packages = self.param_widgets['packages'][0].get().strip()
            action = self.param_widgets['action'][0].get()
            update = self.param_widgets['update'][0].instate(['selected'])

            if not packages:
                messagebox.showerror("Error", "Package names are required")
                return

            if update:
                cmd.append('--update')
            if action == 'remove':
                cmd.append('--remove')

            cmd.extend(packages.split())

        elif script_name == 'scheduler.sh':
            action = self.param_widgets['action'][0].get()

            if action == 'list':
                cmd.append('--list')
            else:
                schedule = self.param_widgets['schedule'][0].get().strip()
                command = self.param_widgets['command'][0].get().strip()

                if not schedule or not command:
                    messagebox.showerror("Error", "Schedule and command are required")
                    return

                if action == 'remove':
                    cmd.extend(['--remove', command])
                else:
                    cmd.extend(['--schedule', schedule, command])

        elif script_name == 'timectl.sh':
            action = self.param_widgets['action'][0].get()
            timezone = self.param_widgets['timezone'][0].get().strip()

            if action == 'status':
                cmd.append('--status')
            elif action == 'set-tz':
                if not timezone:
                    messagebox.showerror("Error", "Timezone is required")
                    return
                cmd.extend(['--set-tz', timezone])
            elif action == 'enable-ntp':
                cmd.append('--enable-ntp')
            elif action == 'disable-ntp':
                cmd.append('--disable-ntp')

        self.append_output(f"$ {' '.join(cmd)}\n", "system")
        logger.info(f"Running script: {' '.join(cmd)}")

        self.runner = ProcessRunner(self.on_output)

        if self.runner.start(cmd):
            self.stop_btn.config(state=tk.NORMAL)
            self.process_runner_queue()
        else:
            self.append_output("Failed to start script\n", "stderr")

    def stop_runner(self):
        """Stop the running script."""
        if self.runner:
            self.runner.stop()
            self.stop_btn.config(state=tk.DISABLED)
            logger.info("Stopped script")

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
