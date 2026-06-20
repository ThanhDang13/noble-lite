"""
Privilege escalation utilities for running commands that need root.
Tries pkexec first (native system dialog), falls back to sudo with GUI password prompt.
Supports cached password for multiple operations.
"""

import os
import shutil
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox
from threading import Lock


# Global password cache (in-memory only, cleared on exit)
_password_cache = None
_cache_lock = Lock()


def set_cached_password(password):
    """Cache password for reuse in multiple operations."""
    global _password_cache
    with _cache_lock:
        _password_cache = password


def clear_cached_password():
    """Clear cached password."""
    global _password_cache
    with _cache_lock:
        _password_cache = None


def get_cached_password():
    """Get cached password if available."""
    with _cache_lock:
        return _password_cache


def has_pkexec():
    """Check if pkexec is available on the system."""
    return shutil.which('pkexec') is not None


def run_with_privilege(command, password_callback=None, use_cached=True):
    """
    Run a command with elevated privileges.

    Args:
        command: List of command arguments (e.g., ['insmod', 'module.ko'])
        password_callback: Optional function that returns password for sudo fallback
        use_cached: Use cached password if available (default: True)

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    # Check if command is a shell script and convert to absolute path
    is_shell_script = False
    if command and os.path.isfile(command[0]) and command[0].endswith('.sh'):
        is_shell_script = True
        # Convert to absolute path for pkexec
        command[0] = os.path.abspath(command[0])

    if has_pkexec():
        # Try pkexec first (native system authentication dialog)
        try:
            # For shell scripts, use bash explicitly with absolute path
            if is_shell_script:
                pkexec_cmd = ['pkexec', 'bash', command[0]] + command[1:]
            else:
                pkexec_cmd = ['pkexec'] + command

            result = subprocess.run(
                pkexec_cmd,
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
    password = None

    # Try cached password first
    if use_cached:
        password = get_cached_password()

    # If no cached password, ask for one
    if password is None and password_callback:
        password = password_callback()
        if password is None:
            return (1, '', 'Password required but not provided')

        # Cache password for future use
        if use_cached:
            set_cached_password(password)

    if password:
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
