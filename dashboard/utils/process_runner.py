"""
Subprocess runner with real-time output streaming to Tkinter widgets.
Uses threading + queue to safely update GUI from background threads.
"""

import subprocess
import threading
import queue
import os
import signal
from typing import Optional, Callable, List


class ProcessRunner:
    """Manages a subprocess with real-time output streaming."""

    def __init__(self, output_callback: Callable[[str, str], None]):
        """
        Args:
            output_callback: Function(text, tag) called with output lines.
                           tag is 'stdout', 'stderr', or 'system'
        """
        self.output_callback = output_callback
        self.process: Optional[subprocess.Popen] = None
        self.output_queue = queue.Queue()
        self.reader_threads = []
        self.is_running = False

    def start(self, command: List[str], cwd: Optional[str] = None, env: Optional[dict] = None):
        """
        Start a subprocess and begin streaming output.

        Args:
            command: Command and arguments as list
            cwd: Working directory
            env: Environment variables

        Returns:
            bool: True if process started successfully
        """
        if self.is_running:
            self.output_callback("Process already running\n", "system")
            return False

        try:
            # Use unbuffered mode for real-time output
            process_env = env or os.environ.copy()
            process_env['PYTHONUNBUFFERED'] = '1'

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered (was 1)
                cwd=cwd,
                env=process_env
            )

            self.is_running = True

            # Start reader threads for stdout and stderr
            stdout_thread = threading.Thread(
                target=self._read_output,
                args=(self.process.stdout, 'stdout'),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self._read_output,
                args=(self.process.stderr, 'stderr'),
                daemon=True
            )

            stdout_thread.start()
            stderr_thread.start()

            self.reader_threads = [stdout_thread, stderr_thread]

            # Start monitor thread to check process completion
            monitor_thread = threading.Thread(
                target=self._monitor_process,
                daemon=True
            )
            monitor_thread.start()

            return True

        except FileNotFoundError:
            self.output_callback(f"Command not found: {command[0]}\n", "stderr")
            return False
        except Exception as e:
            self.output_callback(f"Error starting process: {e}\n", "stderr")
            return False

    def _read_output(self, pipe, tag):
        """Read output from pipe and put into queue."""
        try:
            for line in pipe:
                self.output_queue.put((line, tag))
        except Exception as e:
            self.output_queue.put((f"Error reading output: {e}\n", "stderr"))
        finally:
            pipe.close()

    def _monitor_process(self):
        """Monitor process completion and notify via queue."""
        returncode = self.process.wait()
        self.is_running = False
        self.output_queue.put((f"\nProcess exited with code {returncode}\n", "system"))

    def process_queue(self):
        """Process queued output and call callback. Call this periodically from GUI thread."""
        try:
            while True:
                text, tag = self.output_queue.get_nowait()
                self.output_callback(text, tag)
        except queue.Empty:
            pass

    def stop(self):
        """Stop the running process."""
        if self.process and self.is_running:
            try:
                self.process.terminate()
                # Give it 2 seconds to terminate gracefully
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()

                self.output_callback("Process stopped\n", "system")
            except Exception as e:
                self.output_callback(f"Error stopping process: {e}\n", "stderr")
            finally:
                self.is_running = False

    def get_pid(self) -> Optional[int]:
        """Get PID of running process."""
        if self.process and self.is_running:
            return self.process.pid
        return None

    def send_input(self, text: str):
        """Send input to process stdin."""
        if self.process and self.is_running:
            try:
                self.process.stdin.write(text)
                self.process.stdin.flush()
            except Exception as e:
                self.output_callback(f"Error sending input: {e}\n", "stderr")
