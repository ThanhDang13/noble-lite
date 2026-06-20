"""
Main Dashboard Application - Entry point and navigation
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Add dashboard directory to path for absolute imports
dashboard_dir = Path(__file__).parent
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

from utils.logger import get_logger
from panels.kernel_panel import KernelPanel
from panels.process_manager_panel import ProcessManagerPanel
from panels.file_manager_panel import FileManagerPanel
from panels.network_monitor_panel import NetworkMonitorPanel
from panels.socket_server_panel import SocketServerPanel
from panels.socket_client_panel import SocketClientPanel
from panels.scripts_panel import ScriptsPanel
from panels.logs_panel import LogsPanel

logger = get_logger("main")


class DashboardApp(tk.Tk):
    """Main dashboard application window."""

    def __init__(self):
        super().__init__()

        self.title("Linux System Programming Dashboard")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Configure style
        self.setup_style()

        # Create main container
        self.setup_ui()

        # Start with first panel
        self.show_panel("Kernel Module")

        logger.info("Dashboard application started")

    def setup_style(self):
        """Setup ttk style and theme."""
        style = ttk.Style()

        # Use a modern theme if available
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')

        # Customize colors
        style.configure('Sidebar.TFrame', background='#2c3e50')
        style.configure('Sidebar.TButton',
                       background='#34495e',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=10)
        style.map('Sidebar.TButton',
                 background=[('active', '#3498db'), ('pressed', '#2980b9')])

    def setup_ui(self):
        """Setup the main UI layout."""
        # Main container with sidebar and content area
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left sidebar for navigation
        self.sidebar = ttk.Frame(main_container, style='Sidebar.TFrame', width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)  # Don't shrink

        # Title in sidebar
        title_label = tk.Label(
            self.sidebar,
            text="Dashboard",
            font=("TkDefaultFont", 16, "bold"),
            bg='#2c3e50',
            fg='white',
            pady=20
        )
        title_label.pack(fill=tk.X)

        # Navigation buttons
        self.nav_buttons = {}
        self.panels_config = [
            ("Kernel Module", "🔧"),
            ("Process Manager", "📊"),
            ("File Manager", "📁"),
            ("Network Monitor", "🌐"),
            ("Socket Server", "🖥️"),
            ("Socket Client", "💻"),
            ("Scripts", "📜"),
            ("Logs", "📋")
        ]

        for panel_name, icon in self.panels_config:
            btn = tk.Button(
                self.sidebar,
                text=f"{icon}  {panel_name}",
                font=("TkDefaultFont", 11),
                bg='#34495e',
                fg='white',
                activebackground='#3498db',
                activeforeground='white',
                relief=tk.FLAT,
                bd=0,
                cursor='hand2',
                anchor=tk.W,
                padx=20,
                pady=12,
                command=lambda name=panel_name: self.show_panel(name)
            )
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.nav_buttons[panel_name] = btn

        # Spacer
        spacer = tk.Frame(self.sidebar, bg='#2c3e50')
        spacer.pack(fill=tk.BOTH, expand=True)

        # Status bar in sidebar
        self.status_frame = tk.Frame(self.sidebar, bg='#2c3e50', pady=10)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.kernel_status_label = tk.Label(
            self.status_frame,
            text="Module: Unknown",
            font=("TkDefaultFont", 9),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        self.kernel_status_label.pack(anchor=tk.W, padx=10)

        # Right content area
        self.content_frame = ttk.Frame(main_container)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Initialize panels (lazy loading)
        self.panels = {}
        self.current_panel = None

        # Update kernel status periodically
        self.update_kernel_status()

    def show_panel(self, panel_name):
        """Show the selected panel."""
        # Hide current panel
        if self.current_panel:
            self.current_panel.pack_forget()

        # Create panel if not exists (lazy loading)
        if panel_name not in self.panels:
            if panel_name == "Kernel Module":
                self.panels[panel_name] = KernelPanel(self.content_frame)
            elif panel_name == "Process Manager":
                self.panels[panel_name] = ProcessManagerPanel(self.content_frame)
            elif panel_name == "File Manager":
                self.panels[panel_name] = FileManagerPanel(self.content_frame)
            elif panel_name == "Network Monitor":
                self.panels[panel_name] = NetworkMonitorPanel(self.content_frame)
            elif panel_name == "Socket Server":
                self.panels[panel_name] = SocketServerPanel(self.content_frame)
            elif panel_name == "Socket Client":
                self.panels[panel_name] = SocketClientPanel(self.content_frame)
            elif panel_name == "Scripts":
                self.panels[panel_name] = ScriptsPanel(self.content_frame)
            elif panel_name == "Logs":
                self.panels[panel_name] = LogsPanel(self.content_frame)

        # Show selected panel
        panel = self.panels[panel_name]
        panel.pack(fill=tk.BOTH, expand=True)
        self.current_panel = panel

        # Update navigation button styles
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == panel_name:
                btn.config(bg='#3498db', font=("TkDefaultFont", 11, "bold"))
            else:
                btn.config(bg='#34495e', font=("TkDefaultFont", 11))

        logger.info(f"Switched to panel: {panel_name}")

    def update_kernel_status(self):
        """Update kernel module status in sidebar."""
        try:
            import subprocess
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if 'monitor' in result.stdout:
                self.kernel_status_label.config(text="Module: LOADED ✓", fg='#2ecc71')
            else:
                self.kernel_status_label.config(text="Module: NOT LOADED", fg='#e74c3c')

        except Exception:
            self.kernel_status_label.config(text="Module: Unknown", fg='#95a5a6')

        # Schedule next update (every 5 seconds)
        self.after(5000, self.update_kernel_status)


def main():
    """Main entry point."""
    app = DashboardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
