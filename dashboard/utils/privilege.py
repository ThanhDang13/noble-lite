"""
Privilege escalation utilities for running commands that need root.
Tries pkexec first (native system dialog), falls back to sudo with GUI password prompt.
"""

import os
import shutil
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox


def has_pkexec():
    """Check if pkexec is available on the system."""
    return shutil.which('pkexec') is not None


def run_with_privilege(command, password_callback=None):
    """
    Run a command with elevated privileges.

    Args:
        command: List of command arguments (e.g., ['insmod', 'module.ko'])
        password_callback: Optional function that returns password for sudo fallback

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    if has_pkexec():
        # Try pkexec first (native system authentication dialog)
        try:
            result = subprocess.run(
                ['pkexec'] + command,
                capture_output=True,
                text=True,
                timeout=60
            )
            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (1, '', 'pkexec timeout')
        except Exception as e:
            # If pkexec fails, fall through to sudo
            pass

    # Fallback to sudo with password
    if password_callback:
        password = password_callback()
        if password is None:
            return (1, '', 'Password required but not provided')

        try:
            proc = subprocess.Popen(
                ['sudo', '-S'] + command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(input=password + '\n', timeout=60)
            return (proc.returncode, stdout, stderr)
        except subprocess.TimeoutExpired:
            proc.kill()
            return (1, '', 'sudo timeout')
        except Exception as e:
            return (1, '', str(e))
    else:
        return (1, '', 'Privilege escalation required but no password callback provided')


def ask_password_dialog(parent=None):
    """Show a GUI dialog to ask for sudo password."""
    root = parent
    if root is None:
        root = tk.Tk()
        root.withdraw()

    password = simpledialog.askstring(
        "Administrator Password Required",
        "Enter your password for sudo:",
        show='*',
        parent=root
    )

    return password


def check_needs_root(command):
    """
    Check if a command likely needs root privileges.

    Args:
        command: List of command arguments

    Returns:
        bool: True if command likely needs root
    """
    root_commands = [
        'insmod', 'rmmod', 'modprobe',
        'apt-get', 'dpkg',
        'timedatectl', 'hwclock',
        'systemctl'
    ]

    if not command:
        return False

    cmd_name = os.path.basename(command[0])
    return cmd_name in root_commands
